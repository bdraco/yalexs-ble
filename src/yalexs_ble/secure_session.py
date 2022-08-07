from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from Crypto.Cipher import AES  # nosec

from . import util
from .const import SECURE_READ_CHARACTERISTIC, SECURE_WRITE_CHARACTERISTIC
from .session import ResponseError, Session

_LOGGER = logging.getLogger(__name__)


class SecureSession(Session):

    _write_characteristic = SECURE_WRITE_CHARACTERISTIC
    _read_characteristic = SECURE_READ_CHARACTERISTIC

    def __init__(
        self, client: BleakClient, name: str, lock: asyncio.Lock, key_index: int
    ) -> None:
        super().__init__(client, name, lock)
        self.key_index = key_index
        self.write_characteristic = client.services.get_characteristic(
            self._write_characteristic
        )
        self.read_characteristic = client.services.get_characteristic(
            self._read_characteristic
        )

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
        response_checksum = int.from_bytes(
            data[0x0C:0x10], byteorder="little", signed=False
        )
        expected = util._security_checksum(data)
        _LOGGER.debug(
            "%s: Response security checksum: %s, expected: %s",
            self.name,
            response_checksum,
            expected,
        )
        if expected != response_checksum:
            raise ResponseError(
                f"Security checksum mismatch: {response_checksum} != {expected}"
            )
