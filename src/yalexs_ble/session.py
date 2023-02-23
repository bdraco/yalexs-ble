from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Callable

import async_timeout
from bleak import BleakClient
from bleak_retry_connector import BleakError
from Crypto.Cipher import AES  # nosec

from . import util
from .const import READ_CHARACTERISTIC, WRITE_CHARACTERISTIC

_LOGGER = logging.getLogger(__name__)


class YaleXSBLEError(Exception):
    """Base class for YaleXSBLE errors."""


class AuthError(YaleXSBLEError):
    """Error during authentication."""


class ResponseError(YaleXSBLEError):
    """Error during response."""


class DisconnectedError(YaleXSBLEError):
    """Disconnected during response."""


class NoAdvertisementError(YaleXSBLEError):
    """No advertisement data."""


class BluetoothError(YaleXSBLEError):
    """Bluetooth error."""


class Session:
    _write_characteristic = WRITE_CHARACTERISTIC
    _read_characteristic = READ_CHARACTERISTIC

    def __init__(
        self,
        client: BleakClient,
        name: str,
        lock: asyncio.Lock,
        disconnected_event: asyncio.Event,
        state_callback: Callable[[bytes], None] | None = None,
    ) -> None:
        """Init the session."""
        self.name = name
        self._lock = lock
        self.cipher_decrypt: AES.MODE_CBC | None = None
        self.cipher_encrypt: AES.MODE_CBC | None = None
        self.client = client
        self.write_characteristic = client.services.get_characteristic(
            self._write_characteristic
        )
        self.read_characteristic = client.services.get_characteristic(
            self._read_characteristic
        )
        self._notifications_started = False
        self._notify_future: asyncio.Future[bytes] | None = None
        self._state_callback = state_callback
        self._disconnected_event = disconnected_event
        self._first_request = True

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

    def build_operation_command(self, cmd_byte: int) -> bytearray:
        """Build a command to send to the lock."""
        cmd = self.build_command(0x02)
        cmd[0x04] = cmd_byte
        return cmd

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

    def _notify(self, char: int, data: bytes) -> None:
        _LOGGER.debug(
            "%s: Receiving response via notify: %s (waiting=%s)",
            self.name,
            data.hex(),
            bool(self._notify_future),
        )
        decrypted_data = self.decrypt(data)
        if self._state_callback:
            self._state_callback(decrypted_data)
        _LOGGER.debug(
            "%s: Decrypted response via notify: %s", self.name, decrypted_data.hex()
        )
        if self._notify_future is None:
            return
        try:
            self._validate_response(data)
        except ResponseError as ex:
            _LOGGER.debug("%s: Invalid response, waiting for next one", self.name)
            self._notify_future.set_exception(ex)
            self._notify_future = None
            return
        self._notify_future.set_result(decrypted_data)
        self._notify_future = None

    async def _locked_write(self, command: bytearray) -> bytes:
        # NOTE: The last two bytes are not encrypted
        # General idea seems to be that if the last byte
        # of the command indicates an offline key offset (is non-zero),
        # the command is "secure" and encrypted with the offline key
        if not self.client.is_connected or self._disconnected_event.is_set():
            raise BleakError("disconnected")
        assert self.cipher_encrypt is not None, "Cipher not set"  # nosec
        plainText = command[0x00:0x10]
        cipherText = self.cipher_encrypt.encrypt(plainText)
        util._copy(command, cipherText)
        _LOGGER.debug("%s: Encrypted command: %s", self.name, command.hex())

        for attempt in range(3):
            future: asyncio.Future[bytes] = asyncio.Future()
            self._notify_future = future
            _LOGGER.debug(
                "%s: Writing command to %s: %s",
                self.name,
                self.write_characteristic,
                command.hex(),
            )
            _LOGGER.debug("%s: Waiting for response", self.name)
            async with async_timeout.timeout(10):
                try:
                    await self.client.write_gatt_char(
                        self.write_characteristic, command, True
                    )
                    result = await future
                except ResponseError:
                    if attempt == 2:
                        raise
                    _LOGGER.debug("%s: Invalid response, retrying", self.name)
                    continue
                else:
                    break
        _LOGGER.debug("%s: Got response: %s", self.name, result.hex())
        return result

    async def start_notify(self) -> None:
        """Start notify."""
        if not self._notifications_started:
            _LOGGER.debug("%s: Starting notify for %s", self.name, type(self))
            try:
                await self._start_notify(self._notify)
            except BleakError as err:
                _LOGGER.debug("%s: Failed to start notify: %s", self.name, err)
                if "not found" in str(err):
                    raise AuthError(f"{self.name}: {err}") from err
                raise
            self._notifications_started = True

    async def _start_notify(self, callback: Callable[[int, bytearray], None]) -> None:
        """Start notify."""
        if not self.client.is_connected:
            return
        try:
            await self.client.start_notify(self.read_characteristic, callback)
            # Workaround for MacOS to allow restarting notify
        except ValueError:
            await self.stop_notify()
            if not self.client.is_connected:
                return
            await self.client.start_notify(self.read_characteristic, callback)

    async def stop_notify(self) -> None:
        """Stop notify."""
        if not self.client.is_connected or not self._notifications_started:
            return
        _LOGGER.debug("%s: Stopping notify: %s", self.name, type(self))
        try:
            await self.client.stop_notify(self.read_characteristic)
        except EOFError as err:
            _LOGGER.debug("%s: D-Bus stopping notify: %s", self.name, err)
            pass
        except BleakError as err:
            _LOGGER.debug("%s: Bleak error stopping notify: %s", self.name, err)
            pass

    async def execute(self, command: bytearray) -> bytes:
        """Execute command."""
        assert self.cipher_encrypt is not None, "Cipher not set"  # nosec
        self._write_checksum(command)
        write_task = asyncio.create_task(self._write(command))
        disconnect_task = asyncio.create_task(self._disconnected_event.wait())
        await asyncio.wait(
            (write_task, disconnect_task),
            return_when=asyncio.FIRST_COMPLETED,
        )
        if disconnect_task.done():
            write_task.cancel()
        if write_task.done():
            try:
                return await write_task
            except BleakError as err:
                if self._first_request and util.is_key_error(err):
                    raise AuthError(
                        f"Authentication error: key or slot (key index) is incorrect: {err}"
                    ) from err
                if util.is_disconnected_error(err):
                    raise DisconnectedError(f"{self.name}: {err}") from err
                raise
            finally:
                self._first_request = False
        write_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await write_task
        raise DisconnectedError(f"{self.name}: Disconnected")
