from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak_retry_connector import BleakError
from Crypto.Cipher import AES  # nosec

from . import util
from .const import (
    READ_CHARACTERISTIC,
    SECURE_READ_CHARACTERISTIC,
    SECURE_WRITE_CHARACTERISTIC,
    WRITE_CHARACTERISTIC,
)

_LOGGER = logging.getLogger(__name__)


class AuthError(Exception):
    pass


class ResponseError(Exception):
    pass


class Session:

    write_characteristic = WRITE_CHARACTERISTIC
    read_characteristic = READ_CHARACTERISTIC

    def __init__(self, client: BleakClient, name: str, lock: asyncio.Lock) -> None:
        """Init the session."""
        self.name = name
        self._lock = lock
        self.cipher_decrypt: AES.MODE_CBC | None = None
        self.cipher_encrypt: AES.MODE_CBC | None = None
        self.client = client

    def set_write(self, write_characteristic: BleakGATTCharacteristic) -> None:
        self.write_characteristic = write_characteristic

    def set_read(self, read_characteristic: BleakGATTCharacteristic) -> None:
        self.read_characteristic = read_characteristic

    def set_key(self, key: bytes) -> None:
        self.cipher_encrypt = AES.new(key, AES.MODE_CBC, iv=bytes(0x10))
        self.cipher_decrypt = AES.new(key, AES.MODE_CBC, iv=bytes(0x10))

    def decrypt(self, data: bytes | bytearray) -> bytes:
        if self.cipher_decrypt is not None:
            cipherText = data[0x00:0x10]
            plainText = self.cipher_decrypt.decrypt(cipherText)
            if type(data) is not bytearray:
                data = bytearray(data)
            util._copy(data, plainText)

        return data

    def build_command(self, opcode: int) -> bytearray:
        cmd = bytearray(0x12)
        cmd[0x00] = 0xEE
        cmd[0x01] = opcode
        cmd[0x10] = 0x02
        return cmd

    def _write_checksum(self, command: bytearray) -> None:
        checksum = util._simple_checksum(command)
        command[0x03] = checksum

    def _validate_response(self, response: bytes | bytearray) -> None:
        _LOGGER.debug(
            "%s: Response simple checksum: %s",
            self.name,
            str(util._simple_checksum(response)),
        )
        if util._simple_checksum(response) != 0:
            raise ResponseError(f"Simple checksum mismatch {response!r}")

        if response[0x00] != 0xBB and response[0x00] != 0xAA:
            raise ResponseError(f"Incorrect flag in response: {response[0x00]}")

    async def _write(self, command: bytearray) -> bytes:
        """Write under the lock."""
        async with self._lock:
            return await self._locked_write(command)

    async def _locked_write(self, command: bytearray) -> bytes:
        _LOGGER.debug("%s: Writing command: %s", self.name, command.hex())

        # NOTE: The last two bytes are not encrypted
        # General idea seems to be that if the last byte
        # of the command indicates an offline key offset (is non-zero),
        # the command is "secure" and encrypted with the offline key
        if self.cipher_encrypt is not None:
            plainText = command[0x00:0x10]
            cipherText = self.cipher_encrypt.encrypt(plainText)
            util._copy(command, cipherText)

        _LOGGER.debug("%s: Encrypted command: %s", self.name, command.hex())

        future: asyncio.Future[bytes] = asyncio.Future()
        notified = False

        def _notify(char: int, data: bytes) -> None:
            nonlocal notified
            if notified:
                return
            notified = True
            _LOGGER.debug(
                "%s: Receiving response via notify: %s", self.name, data.hex()
            )
            decrypted_data = self.decrypt(data)
            _LOGGER.debug(
                "%s: Decrypted response via notify: %s", self.name, decrypted_data.hex()
            )
            try:
                self._validate_response(data)
            except ResponseError:
                _LOGGER.debug("%s: Invalid response, waiting for next one", self.name)
                return
            notified = True
            future.set_result(decrypted_data)

        _LOGGER.debug("%s: Starting notify", self.name)
        try:
            await self.client.start_notify(self.read_characteristic, _notify)
        except BleakError as err:
            if "not found" in str(err):
                raise AuthError(f"{self.name}: {err}") from err
            raise
        try:
            _LOGGER.debug(
                "%s: Writing command to %s: %s",
                self.name,
                self.write_characteristic,
                command,
            )
            await self.client.write_gatt_char(self.write_characteristic, command, True)
            _LOGGER.debug("%s: Waiting for response", self.name)
            result = await asyncio.wait_for(future, timeout=5)
            _LOGGER.debug("%s: Got response: %s", self.name, result.hex())
        except asyncio.TimeoutError:
            _LOGGER.debug("%s: Timeout", self.name)
            raise
        finally:
            _LOGGER.debug("%s: Stopping notify", self.name)
            try:
                await self.client.stop_notify(self.read_characteristic)
            except BleakError as err:
                if "not found" in str(err):
                    raise AuthError(f"{self.name}: {err}") from err
                raise

        _LOGGER.debug("%s: Received response: %s", self.name, result.hex())
        return result

    async def execute(self, command: bytearray) -> bytes:
        self._write_checksum(command)
        return await self._write(command)


class SecureSession(Session):

    write_characteristic = SECURE_WRITE_CHARACTERISTIC
    read_characteristic = SECURE_READ_CHARACTERISTIC

    def __init__(
        self, client: BleakClient, name: str, lock: asyncio.Lock, key_index: int
    ) -> None:
        super().__init__(client, name, lock)
        self.key_index = key_index

    def set_key(self, key: bytes) -> None:
        self.cipher_encrypt = AES.new(key, AES.MODE_ECB)
        self.cipher_decrypt = AES.new(key, AES.MODE_ECB)

    def build_command(self, opcode: int) -> bytearray:
        cmd = bytearray(0x12)
        cmd[0x00] = opcode
        cmd[0x10] = 0x0F
        cmd[0x11] = self.key_index
        return cmd

    def _write_checksum(self, command: bytearray) -> None:
        checksum = util._security_checksum(command)
        checksum_bytes = checksum.to_bytes(4, byteorder="little", signed=False)
        util._copy(command, checksum_bytes, destLocation=0x0C)

    def _validate_response(self, data: bytes) -> None:
        _LOGGER.debug(
            "%s: Response security checksum: %s",
            self.name,
            str(util._security_checksum(data)),
        )
        response_checksum = int.from_bytes(
            data[0x0C:0x10], byteorder="little", signed=False
        )
        _LOGGER.debug(
            "%s: Response security checksum: %s", self.name, str(response_checksum)
        )
        if util._security_checksum(data) != response_checksum:
            raise ResponseError(
                "Security checksum mismatch: %s != %s"
                % (util._security_checksum(data), response_checksum)
            )
