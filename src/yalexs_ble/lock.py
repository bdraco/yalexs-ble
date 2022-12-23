from __future__ import annotations

import asyncio
import bisect
import logging
import os
from collections.abc import Callable, Iterable
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
    BatteryState,
    Commands,
    DoorStatus,
    LockInfo,
    LockState,
    LockStatus,
)
from .secure_session import SecureSession
from .session import AuthError, DisconnectedError, Session

_LOGGER = logging.getLogger(__name__)

AA_BATTERY_VOLTAGE_TO_PERCENTAGE = (
    (1.55, 100),
    (1.549, 97),
    (1.548, 95),
    (1.547, 94),  # confirmed
    (1.49075, 93),  # confirmed
    (1.49, 90),
    (1.471, 85),  # confirmed
    (1.46, 80),
    (1.45, 75),
    (1.40, 70),
    (1.39, 65),
    (1.38, 60),
    (1.37, 55),
    (1.36, 50),
    (1.35, 45),
    (1.34, 40),
    (1.33, 35),
    (1.32, 30),
    (1.31, 35),
    (1.30, 30),
    (1.29, 25),
    (1.28, 20),
    (1.27, 15),
    (1.26, 10),
    (1.25, 5),
    (1.24, 0),
)
AA_BATTERY_VOLTAGE_LIST = [
    voltage for voltage, _ in sorted(AA_BATTERY_VOLTAGE_TO_PERCENTAGE)
]
AA_BATTERY_VOLTAGE_MAP = {
    voltage: percentage for voltage, percentage in AA_BATTERY_VOLTAGE_TO_PERCENTAGE
}


def convert_voltage_to_percentage(voltage: float) -> int:
    """Convert voltage to percentage."""
    pos = bisect.bisect_left(AA_BATTERY_VOLTAGE_LIST, voltage)
    if pos != 0:
        pos -= 1
    return AA_BATTERY_VOLTAGE_MAP[AA_BATTERY_VOLTAGE_LIST[pos]]


class Lock:
    def __init__(
        self,
        ble_device_callback: Callable[[], BLEDevice],
        keyString: str,
        keyIndex: int,
        name: str,
        state_callback: Callable[
            [Iterable[LockStatus | DoorStatus | BatteryState]], None
        ],
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
        self._state_callback = state_callback

    def set_name(self, name: str) -> None:
        self.name = name

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

        self.session = Session(
            self.client, self.name, self._lock, self._internal_state_callback
        )
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
            await client.disconnect()
            raise BleakError("Missing characteristic")

        # Order matters here, we must start notify for the secure session before
        # the non-secure session
        await self.secure_session.start_notify()
        await self.session.start_notify()

        self.secure_session.set_key(self.key)
        await self._setup_session()

    def _internal_state_callback(self, state: bytes) -> None:
        """Handle state change."""
        _LOGGER.debug("%s: State changed: %s", self.name, state.hex())
        if state[0] == 0xBB:
            if state[4] == 0x02:  # lock only
                lock_status = state[0x08]
                self._state_callback(
                    [VALUE_TO_LOCK_STATUS.get(lock_status, LockStatus.UNKNOWN)]
                )
            elif state[4] == 0x2E:  # door state
                door_status = state[0x08]
                self._state_callback(
                    [VALUE_TO_DOOR_STATUS.get(door_status, DoorStatus.UNKNOWN)]
                )
            elif state[4] == 0x2F:  # door and lock
                self._state_callback(self._parse_lock_and_door_state(state))
            elif state[4] == 0x0F:
                self._state_callback([self._parse_battery_state(state)])
            else:
                _LOGGER.debug("%s: Unknown state: %s", self.name, state.hex())
        elif state[0] == 0xAA:
            if state[1] == Commands.UNLOCK.value:
                self._state_callback([LockStatus.UNLOCKED])
            if state[1] == Commands.LOCK.value:
                self._state_callback([LockStatus.LOCKED])
            else:
                _LOGGER.debug("%s: Unknown state: %s", self.name, state.hex())

    async def _setup_session(self) -> None:
        """Setup the session."""
        assert self.session is not None  # nosec
        assert self.secure_session is not None  # nosec
        assert self._disconnected_event is not None  # nosec
        _LOGGER.debug("%s: Setting up the session", self.name)
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
        _LOGGER.debug("%s: Locking", self.name)
        await self.session.execute(
            self._disconnected_event, self.session.build_command(Commands.LOCK.value)
        )
        _LOGGER.debug("%s: Finished locking", self.name)

    async def force_unlock(self) -> None:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        assert self._disconnected_event is not None  # nosec
        _LOGGER.debug("%s: Unlocking", self.name)
        await self.session.execute(
            self._disconnected_event, self.session.build_command(Commands.UNLOCK.value)
        )
        _LOGGER.debug("%s: Finished unlocking", self.name)

    async def lock(self) -> None:
        if (await self.status()).lock == LockStatus.UNLOCKED:
            await self.force_lock()

    async def unlock(self) -> None:
        if (await self.status()).lock == LockStatus.LOCKED:
            await self.force_unlock()

    async def _execute_command(self, cmd_byte: int) -> bytes:
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected")
        assert self._disconnected_event is not None  # nosec
        response = await self.session.execute(
            self._disconnected_event, self.session.build_operation_command(cmd_byte)
        )
        _LOGGER.debug("%s: response: [%s]", self.name, response.hex())
        return response

    def _parse_lock_and_door_state(
        self, response: bytes
    ) -> tuple[LockStatus, DoorStatus]:
        """Parse the lock and door state from the response."""
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
        return lock_status_enum, door_status_enum

    async def status(self) -> LockState:
        _LOGGER.debug("%s: Executing status", self.name)
        response = await self._execute_command(
            0x2F if self._lock_info and self._lock_info.door_sense else 0x02
        )
        _LOGGER.debug("%s: Finished executing status", self.name)
        lock_status_enum, door_status_enum = self._parse_lock_and_door_state(response)
        return LockState(lock_status_enum, door_status_enum, None)

    def _parse_battery_state(self, response: bytes) -> BatteryState:
        """Parse the battery state from the response."""
        voltage = (response[0x09] * 256 + response[0x08]) / 1000
        # The voltage is divided by 4 in the lock
        # since it uses 4 AA batteries. For the Li-ion
        # battery, this is likely wrong, but since we don't
        # currently have a way to detect the battery type,
        # this is the best we can do for now.
        percentage = convert_voltage_to_percentage(voltage / 4)
        return BatteryState(voltage, percentage)

    async def battery(self) -> BatteryState:
        _LOGGER.debug("%s: Executing battery", self.name)
        response = await self._execute_command(0x0F)
        _LOGGER.debug("%s: Finished executing battery", self.name)
        return self._parse_battery_state(response)

    async def disconnect(self) -> None:
        """Disconnect from the lock."""
        _LOGGER.debug("%s: Disconnecting from the lock", self.name)
        if not self.client or not self.client.is_connected:
            return

        try:
            await self._shutdown_connection()
        finally:
            await self.client.disconnect()

    async def _shutdown_connection(self) -> None:
        """Shutdown the connection."""
        _LOGGER.debug("%s: Shutting down the connection", self.name)
        if (
            not self.is_secure
            or not self.secure_session
            or self._disconnected_event is None
        ):
            return
        cmd = self.secure_session.build_command(0x05)
        cmd[0x11] = 0x00
        response = None
        try:
            response = await self.secure_session.execute(self._disconnected_event, cmd)
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
            _LOGGER.debug("%s: Unexpected response to DISCONNECT: %s", response.hex())

    @property
    def is_connected(self) -> bool:
        return bool(self.client and self.client.is_connected)
