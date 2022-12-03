from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any, cast

from bleak import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BLEDevice,
    establish_connection,
)

from . import util
from .const import (
    FIRMWARE_REVISION_CHARACTERISTIC,
    MANUFACTURER_NAME_CHARACTERISTIC,
    MODEL_NUMBER_CHARACTERISTIC,
    SERIAL_NUMBER_CHARACTERISTIC,
    VALUE_TO_DOOR_STATUS,
    VALUE_TO_LOCK_STATUS,
    Commands,
    DoorStatus,
    LockInfo,
    LockState,
    LockStatus,
)
from .secure_session import SecureSession
from .session import AuthError, DisconnectedError, Session

_LOGGER = logging.getLogger(__name__)


class Lock:
    def __init__(
        self,
        ble_device_callback: Callable[[], BLEDevice],
        keyString: str,
        keyIndex: int,
        name: str,
        info: LockInfo | None = None,
    ) -> None:
        self.ble_device_callback = ble_device_callback
        self.key = bytes.fromhex(keyString)
        self.key_index = keyIndex
        self.name = name
        self.session: Session | None = None
        self.secure_session: SecureSession | None = None
        self.is_secure = False
        self._lock = asyncio.Lock()
        self._lock_info = info
        self.client: BleakClientWithServiceCache | None = None
        self._disconnected_event: asyncio.Event | None = None

    def set_name(self, name: str) -> None:
        self.name = name

    async def __aenter__(self) -> Lock:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            await asyncio.sleep(0)
        finally:
            await self.disconnect()

    def disconnected(self, *args: Any, **kwargs: Any) -> None:
        _LOGGER.debug("%s: Disconnected from lock callback", self.name)
        assert self._disconnected_event is not None  # nosec
        self._disconnected_event.set()

    async def connect(self) -> None:
        """Connect to the lock."""
        _LOGGER.debug(
            "%s: Connecting to the lock",
            self.name,
        )
        self._disconnected_event = asyncio.Event()
        try:
            self.client = await establish_connection(
                BleakClientWithServiceCache,
                self.ble_device_callback(),
                self.name,
                self.disconnected,
                use_services_cache=True,
                ble_device_callback=self.ble_device_callback,
            )
        except (asyncio.TimeoutError, BleakError) as err:
            _LOGGER.error("%s: Failed to connect to the lock: %s", self.name, err)
            raise err
        _LOGGER.debug("%s: Connected", self.name)

        self.session = Session(self.client, self.name, self._lock)
        self.secure_session = SecureSession(
            self.client, self.name, self._lock, self.key_index
        )
        if (
            not self.session.read_characteristic
            or not self.session.write_characteristic
            or not self.secure_session.read_characteristic
            or not self.secure_session.read_characteristic
        ):
            client = cast(BleakClientWithServiceCache, self.client)
            await client.clear_cache()
            raise BleakError("Missing characteristic")

        # Order matters here, we must start notify for the secure session before
        # the non-secure session
        await self.secure_session.start_notify()
        await self.session.start_notify()

        self.secure_session.set_key(self.key)
        handshake_keys = os.urandom(16)

        # Send SEC_LOCK_TO_MOBILE_KEY_EXCHANGE
        cmd = self.secure_session.build_command(0x01)
        util._copy(cmd, handshake_keys[0x00:0x08], destLocation=0x04)
        response = await self.secure_session.execute(self._disconnected_event, cmd)
        if response[0x00] != 0x02:
            raise AuthError(
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
        response = await self.secure_session.execute(self._disconnected_event, cmd)
        if response[0] != 0x04:
            raise AuthError(
                "Unexpected response to SEC_INITIALIZATION_COMMAND: " + response.hex()
            )

    async def lock_info(self) -> LockInfo:
        """Probe the lock for information."""
        _LOGGER.debug("%s: Probing the lock", self.name)
        assert self.client is not None  # nosec
        lock_info = []
        for char in (
            MANUFACTURER_NAME_CHARACTERISTIC,
            MODEL_NUMBER_CHARACTERISTIC,
            SERIAL_NUMBER_CHARACTERISTIC,
            FIRMWARE_REVISION_CHARACTERISTIC,
        ):
            lock_info.append((await self.client.read_gatt_char(char)).decode())
        self._lock_info = LockInfo(*lock_info)
        return self._lock_info

    async def force_lock(self) -> None:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        assert self._disconnected_event is not None  # nosec
        await self.session.execute(
            self._disconnected_event, self.session.build_command(Commands.LOCK.value)
        )

    async def force_unlock(self) -> None:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        assert self._disconnected_event is not None  # nosec
        await self.session.execute(
            self._disconnected_event, self.session.build_command(Commands.UNLOCK.value)
        )

    async def lock(self) -> None:
        if (await self.status()).lock == LockStatus.UNLOCKED:
            await self.force_lock()

    async def unlock(self) -> None:
        if (await self.status()).lock == LockStatus.LOCKED:
            await self.force_unlock()

    async def status(self) -> LockState:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        assert self._disconnected_event is not None  # nosec
        cmd = bytearray(0x12)
        cmd[0x00] = 0xEE
        cmd[0x01] = 0x02
        cmd[0x04] = 0x2F if self._lock_info and self._lock_info.door_sense else 0x02
        cmd[0x10] = 0x02
        response = await self.session.execute(self._disconnected_event, cmd)
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
        """Disconnect from the lock."""
        _LOGGER.debug("%s: Disconnecting from the lock", self.name)
        if not self.client or not self.client.is_connected:
            return

        await self.client.disconnect()

    async def _shutdown_connection(self) -> None:
        """Shutdown the connection."""
        _LOGGER.debug("%s: Shutting down the connection", self.name)
        if self.session:
            await self.session.stop_notify()

        assert self._disconnected_event is not None  # nosec
        if self.is_secure and self.secure_session:
            cmd = self.secure_session.build_command(0x05)
            cmd[0x11] = 0x00
            response = None
            try:
                response = await self.secure_session.execute(
                    self._disconnected_event, cmd
                )
            except DisconnectedError:
                # Lock already disconnected us
                pass
            except (BleakError, asyncio.TimeoutError, EOFError) as err:
                if not util.is_disconnected_error(err):
                    _LOGGER.debug(
                        "%s: Failed to cleanly disconnect from lock: %s", self.name, err
                    )
                pass
            if response and response[0] != 0x8B:
                _LOGGER.debug(
                    "%s: Unexpected response to DISCONNECT: %s", response.hex()
                )

        if self.secure_session:
            await self.secure_session.stop_notify()

    @property
    def is_connected(self) -> bool:
        return bool(self.client and self.client.is_connected)
