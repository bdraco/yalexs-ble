from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import BLEDevice, establish_connection

from . import session, util
from .const import (
    VALUE_TO_DOOR_STATUS,
    VALUE_TO_LOCK_STATUS,
    Commands,
    DoorStatus,
    LockState,
    LockStatus,
)

_LOGGER = logging.getLogger(__name__)


class Lock:
    def __init__(self, device: BLEDevice, keyString: str, keyIndex: int) -> None:
        self.device = device
        self.key = bytes.fromhex(keyString)
        self.key_index = keyIndex
        self.name = device.name
        self.session: session.Session | None = None
        self.secure_session: session.SecureSession | None = None
        self.is_secure = False
        self._lock = asyncio.Lock()
        self.client: BleakClient | None = None

    def set_name(self, name: str) -> None:
        self.name = name

    def disconnected(self, *args: Any, **kwargs: Any) -> None:
        _LOGGER.debug("%s: Disconnected from lock", self.name)

    async def connect(self) -> None:
        """Connect to the lock."""
        _LOGGER.debug("%s: Connecting to the lock", self.name)
        self.client = await establish_connection(
            BleakClient, self.device, self.name, self.disconnected
        )
        _LOGGER.debug("%s: Connected", self.name)
        self.session = session.Session(self.client, self.name, self._lock)
        self.secure_session = session.SecureSession(
            self.client, self.name, self._lock, self.key_index
        )

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

    async def status(self) -> LockState:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        cmd = bytearray(0x12)
        cmd[0x00] = 0xEE
        cmd[0x01] = 0x02
        cmd[0x04] = 0x2F  # We want door status as well
        cmd[0x10] = 0x02
        response = await self.session.execute(cmd)
        _LOGGER.debug("%s: Status response: [%s]", self.name, response.hex())
        lock_status = response[0x08]
        door_status = response[0x09]

        lock_status_enum = VALUE_TO_LOCK_STATUS.get(lock_status, LockStatus.UNKNOWN)
        door_status_enum = VALUE_TO_DOOR_STATUS.get(door_status, DoorStatus.UNKNOWN)

        if lock_status_enum == LockStatus.UNKNOWN:
            _LOGGER.debug(
                "%s: Unrecognized lock_status_str code: %s", self.name, hex(lock_status)
            )
        if door_status_enum == DoorStatus.UNKNOWN:
            _LOGGER.debug(
                "%s: Unrecognized door_status_str code: %s", self.name, hex(door_status)
            )
        return LockState(lock_status_enum, door_status_enum)

    async def disconnect(self) -> None:

        # if self.is_secure:
        #     cmd = self.secure_session.build_command(0x05)
        #     cmd[0x11] = 0x00
        #     response = self.secure_session.execute(cmd)

        #     if response[0] != 0x8b:
        #         raise Exception("Unexpected response to DISCONNECT: " +
        #                         response.hex())
        if self.client:
            await self.client.disconnect()

    @property
    def is_connected(self) -> bool:
        return bool(self.client and self.client.is_connected)
