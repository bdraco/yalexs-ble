from __future__ import annotations

import asyncio
import os

from bleak import BleakClient

from . import session, util
from .const import Commands


class Lock:
    COMMAND_SERVICE_UUID = "0000fe24-0000-1000-8000-00805f9b34fb"
    WRITE_CHARACTERISTIC = "bd4ac611-0b45-11e3-8ffd-0800200c9a66"
    READ_CHARACTERISTIC = "bd4ac612-0b45-11e3-8ffd-0800200c9a66"
    SECURE_WRITE_CHARACTERISTIC = "bd4ac613-0b45-11e3-8ffd-0800200c9a66"
    SECURE_READ_CHARACTERISTIC = "bd4ac614-0b45-11e3-8ffd-0800200c9a66"

    def __init__(self, address: str, keyString: str, keyIndex: int) -> None:
        self.address = address
        self.key = bytes.fromhex(keyString)
        self.key_index = keyIndex
        self.name: str | None = None
        self.session: session.Session | None = None
        self.secure_session: session.SecureSession | None = None
        self.is_secure = False
        self._lock = asyncio.Lock()

    def set_name(self, name: str) -> None:
        self.name = name

    async def connect(self) -> None:
        """Connect to the lock."""
        self.client = BleakClient(self.address)
        self.session = session.Session(self.client, self._lock)
        self.secure_session = session.SecureSession(
            self.client, self._lock, self.key_index
        )

        await self.client.connect()
        for service in self.client.services:
            for characteristic in service.characteristics:
                if characteristic.uuid == self.WRITE_CHARACTERISTIC:
                    self.session.set_write(characteristic)
                elif characteristic.uuid == self.READ_CHARACTERISTIC:
                    self.session.set_read(characteristic)
                elif characteristic.uuid == self.SECURE_WRITE_CHARACTERISTIC:
                    self.secure_session.set_write(characteristic)
                elif characteristic.uuid == self.SECURE_READ_CHARACTERISTIC:
                    self.secure_session.set_read(characteristic)

        if not self.secure_session.write_characteristic:
            raise RuntimeWarning("No secure write characteristic found")
        if not self.secure_session.read_characteristic:
            raise RuntimeWarning("No secure read characteristic found")
        if not self.session.write_characteristic:
            raise RuntimeWarning("No write characteristic found")
        if not self.session.read_characteristic:
            raise RuntimeWarning("No read characteristic found")

        self.secure_session.set_key(self.key)

        handshake_keys = os.urandom(16)

        # Send SEC_LOCK_TO_MOBILE_KEY_EXCHANGE
        cmd = self.secure_session.build_command(0x01)
        util._copy(cmd, handshake_keys[0x00:0x08], destLocation=0x04)
        response = await self.secure_session.execute(cmd)
        if response[0x00] != 0x02:
            raise Exception(
                "Unexpected response to SEC_LOCK_TO_MOBILE_KEY_EXCHANGE: "
                + response.hex()
            )

        self.is_secure = True

        session_key = bytearray(16)
        util._copy(session_key, handshake_keys[0x00:0x08])
        util._copy(session_key, response[0x04:0x0C], destLocation=0x08)
        self.session.set_key(session_key)
        self.secure_session.set_key(session_key)

        # Send SEC_INITIALIZATION_COMMAND
        cmd = self.secure_session.build_command(0x03)
        util._copy(cmd, handshake_keys[0x08:0x10], destLocation=0x04)
        response = await self.secure_session.execute(cmd)
        if response[0] != 0x04:
            raise ValueError(
                "Unexpected response to SEC_INITIALIZATION_COMMAND: " + response.hex()
            )

    async def force_lock(self) -> None:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        await self.session.execute(self.session.build_command(Commands.LOCK.value))

    async def force_unlock(self) -> None:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        await self.session.execute(self.session.build_command(Commands.UNLOCK.value))

    async def lock(self) -> None:
        if await self.status() == "unlocked":
            await self.force_lock()

    async def unlock(self) -> None:
        if await self.status() == "locked":
            await self.force_unlock()

    async def status(self) -> str:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        cmd = bytearray(0x12)
        cmd[0x00] = 0xEE
        cmd[0x01] = 0x02
        cmd[0x04] = 0x02
        cmd[0x10] = 0x02

        response = await self.session.execute(cmd)
        status = response[0x08]

        strstatus = "unknown"
        if status == 0x02:
            strstatus = "unlocking"
        elif status == 0x03:
            strstatus = "unlocked"
        elif status == 0x04:
            strstatus = "locking"
        elif status == 0x05:
            strstatus = "locked"

        if strstatus == "unknown":
            print("Unrecognized status code: " + hex(status))

        return strstatus

    async def disconnect(self) -> None:

        # if self.is_secure:
        #     cmd = self.secure_session.build_command(0x05)
        #     cmd[0x11] = 0x00
        #     response = self.secure_session.execute(cmd)

        #     if response[0] != 0x8b:
        #         raise Exception("Unexpected response to DISCONNECT: " +
        #                         response.hex())

        await self.client.disconnect()

    @property
    def is_connected(self) -> bool:
        return bool(self.client and self.client.is_connected)
