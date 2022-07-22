from __future__ import annotations

import asyncio

from bleak import BleakClient, BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic
from Crypto.Cipher import AES  # nosec

from . import util


class Session:
    def __init__(self, client: BleakClient, lock: asyncio.Lock) -> None:
        """Init the session."""
        self._lock = lock
        self.cipher_decrypt: AES.MODE_CBC | None = None
        self.cipher_encrypt: AES.MODE_CBC | None = None
        self.client = client
        self.write_characteristic: BleakGATTCharacteristic | None = None
        self.read_characteristic: BleakGATTCharacteristic | None = None

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
        print("Response simple checksum: " + str(util._simple_checksum(response)))
        if util._simple_checksum(response) != 0:
            raise ValueError("Simple checksum mismatch")

        if response[0x00] != 0xBB and response[0x00] != 0xAA:
            raise ValueError("Incorrect flag in response")

    async def _write(self, command: bytearray) -> bytes:
        """Write under the lock."""
        async with self._lock:
            return await self._locked_write(command)

    async def _locked_write(self, command: bytearray) -> bytes:
        print("Writing command: " + command.hex())

        # NOTE: The last two bytes are not encrypted
        # General idea seems to be that if the last byte
        # of the command indicates an offline key offset (is non-zero),
        # the command is "secure" and encrypted with the offline key
        if self.cipher_encrypt is not None:
            plainText = command[0x00:0x10]
            cipherText = self.cipher_encrypt.encrypt(plainText)
            util._copy(command, cipherText)

        print("Encrypted command: " + command.hex())

        future: asyncio.Future[bytes] = asyncio.Future()
        notified = False

        def _notify(char: int, data: bytes) -> None:
            nonlocal notified
            if notified:
                return
            notified = True
            print(f"{self}: Receiving response via notify: {data.hex()}")
            decrypted_data = self.decrypt(data)
            print(f"{self}: Decrypted response via notify: {decrypted_data.hex()}")
            try:
                self._validate_response(data)
            except ValueError:
                print(f"{self}: Invalid response, waiting for next one")
                return
            notified = True
            future.set_result(decrypted_data)

        try:
            print(f"{self}: Starting notify")
            await self.client.start_notify(self.read_characteristic, _notify)
        except (ValueError, BleakError):
            await self.client.stop_notify(self.read_characteristic)
            await self.client.start_notify(self.read_characteristic, _notify)

        try:
            await self.client.write_gatt_char(self.write_characteristic, command, True)
            return await asyncio.wait_for(future, timeout=10)
        finally:
            print(f"{self}: Stopping notify")
            await self.client.stop_notify(self.read_characteristic)
            await asyncio.sleep(2)

    async def execute(self, command: bytearray) -> bytes:
        self._write_checksum(command)
        return await self._write(command)


class SecureSession(Session):
    def __init__(self, client: BleakClient, lock: asyncio.Lock, key_index: int) -> None:
        super().__init__(client, lock)
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
        print("Response security checksum: " + str(util._security_checksum(data)))
        response_checksum = int.from_bytes(
            data[0x0C:0x10], byteorder="little", signed=False
        )
        print("Response message checksum: " + str(response_checksum))
        if util._security_checksum(data) != response_checksum:
            raise ValueError("Security checksum mismatch")
