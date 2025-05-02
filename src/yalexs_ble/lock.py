from __future__ import annotations

import asyncio
import bisect
import logging
import os
from collections.abc import Callable, Iterable
from typing import Any, TypeVar, cast

from bleak import BleakError
from bleak_retry_connector import (
    MAX_CONNECT_ATTEMPTS,
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
    LockStatus,
)
from .secure_session import SecureSession
from .session import AuthError, DisconnectedError, Session, YaleXSBLEError

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
WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])


def raise_if_not_connected(func: WrapFuncType) -> WrapFuncType:
    """Define a wrapper to raise if we are not connected to the lock."""

    async def _async_wrap_connected_operation(
        self: Lock, *args: Any, **kwargs: Any
    ) -> None:
        """Wrap a function to make sure the lock is connected."""
        if not self.is_connected:
            raise DisconnectedError("Lock is not connected")
        return await func(self, *args, **kwargs)

    return cast(WrapFuncType, _async_wrap_connected_operation)


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
        disconnect_callback: Callable[[], None] | None = None,
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
        self._state_callback = state_callback
        self._disconnected = False
        self._disconnect_callback = disconnect_callback
        self._disconnected_futures: set[asyncio.Future[None]] = set()

    def set_name(self, name: str) -> None:
        self.name = name

    def disconnected(self, *args: Any, **kwargs: Any) -> None:
        _LOGGER.debug("%s: Disconnected from lock callback", self.name)
        self._disconnected = True
        for future in self._disconnected_futures:
            if not future.done():
                future.set_result(None)
        self._disconnected_futures.clear()
        if self._disconnect_callback:
            self._disconnect_callback()

    async def connect(self, max_attempts: int = MAX_CONNECT_ATTEMPTS) -> None:
        """Connect to the lock."""
        _LOGGER.debug(
            "%s: Connecting to the lock",
            self.name,
        )
        try:
            self.client = await establish_connection(
                BleakClientWithServiceCache,
                self.ble_device_callback(),
                self.name,
                self.disconnected,
                use_services_cache=True,
                ble_device_callback=self.ble_device_callback,
                max_attempts=max_attempts,
            )
        except (asyncio.TimeoutError, BleakError) as err:
            _LOGGER.error("%s: Failed to connect to the lock: %s", self.name, err)
            raise err
        _LOGGER.debug("%s: Connected", self.name)

        self.session = Session(
            self.client,
            self.name,
            self._lock,
            self._disconnected_futures,
            self._internal_state_callback,
        )
        self.secure_session = SecureSession(
            self.client,
            self.name,
            self._lock,
            self._disconnected_futures,
            self.key_index,
        )
        session = self.session
        secure_session = self.secure_session
        _char_map = {
            session._read_characteristic: session.read_characteristic,
            session._write_characteristic: session.write_characteristic,
            secure_session._read_characteristic: secure_session.read_characteristic,
            secure_session._write_characteristic: secure_session.write_characteristic,
        }
        for char_uuid, char in _char_map.items():
            if not char:
                await self._handle_missing_characteristic(char_uuid)

        # Order matters here, we must start notify for the secure session before
        # the non-secure session
        await self.secure_session.start_notify()
        try:
            await self._setup_session()
        except BleakError as err:
            error_desc = str(err).lower()
            if "invalid handle" in error_desc:
                await self._handle_missing_characteristic(error_desc)
            raise err
        await self.session.start_notify()

    async def _handle_missing_characteristic(self, char_uuid: str) -> None:
        """Handle missing characteristic."""
        self.secure_session = None
        self.session = None
        client = cast(BleakClientWithServiceCache, self.client)
        _LOGGER.warning(
            "%s: Missing characteristic %s; Clearing cache", self.name, char_uuid
        )
        await client.clear_cache()
        raise BleakError(f"Missing characteristic {char_uuid}")

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
                _LOGGER.info("%s: Unknown state: %s", self.name, state.hex())
        elif state[0] == 0xAA:
            if state[1] == Commands.UNLOCK.value:
                self._state_callback([LockStatus.UNLOCKED])
            elif state[1] == Commands.LOCK.value:
                self._state_callback([LockStatus.LOCKED])
            else:
                _LOGGER.info("%s: Unknown state: %s", self.name, state.hex())

    async def _setup_session(self) -> None:
        """Setup the session."""
        assert self.session is not None  # nosec
        assert self.secure_session is not None  # nosec
        _LOGGER.debug("%s: Setting up the session", self.name)
        self.secure_session.set_key(self.key)
        handshake_keys = os.urandom(16)

        # Send SEC_LOCK_TO_MOBILE_KEY_EXCHANGE
        cmd = self.secure_session.build_command(0x01)
        util._copy(cmd, handshake_keys[0x00:0x08], destLocation=0x04)
        response = await self.secure_session.execute(
            cmd, "SEC_LOCK_TO_MOBILE_KEY_EXCHANGE"
        )
        if response[0x00] != 0x02:
            raise AuthError(
                "Authentication error: key or slot (key index) is incorrect: unexpected response to SEC_LOCK_TO_MOBILE_KEY_EXCHANGE: "
                + response.hex()
            )

        self.is_secure = True

        session_key = bytearray(16)
        util._copy(session_key, handshake_keys[0x00:0x08])
        util._copy(session_key, response[0x04:0x0C], destLocation=0x08)
        self.secure_session.set_key(session_key)

        # Send SEC_INITIALIZATION_COMMAND
        cmd = self.secure_session.build_command(0x03)
        util._copy(cmd, handshake_keys[0x08:0x10], destLocation=0x04)
        response = await self.secure_session.execute(cmd, "SEC_INITIALIZATION_COMMAND")
        if response[0] != 0x04:
            raise AuthError(
                "Authentication error: key or slot (key index) is incorrect: unexpected response to SEC_INITIALIZATION_COMMAND: "
                + response.hex()
            )
        self.session.set_key(session_key)
        self.secure_session.enable_cooldown()
        self.session.enable_cooldown()

    @raise_if_not_connected
    async def lock_info(self) -> LockInfo:
        """Probe the lock for information."""
        _LOGGER.debug("%s: Probing the lock", self.name)
        assert self.client is not None  # nosec
        lock_info = []
        for char_uuid in (
            MANUFACTURER_NAME_CHARACTERISTIC,
            MODEL_NUMBER_CHARACTERISTIC,
            SERIAL_NUMBER_CHARACTERISTIC,
            FIRMWARE_REVISION_CHARACTERISTIC,
        ):
            char = self.client.services.get_characteristic(char_uuid)
            if not char:
                await self._handle_missing_characteristic(char_uuid)
            lock_info.append(
                (await self.client.read_gatt_char(char)).decode().split("\0")[0]
            )
        self._lock_info = LockInfo(*lock_info)
        return self._lock_info

    @raise_if_not_connected
    async def force_securemode(self) -> None:
        """Force the lock into securemode."""
        _LOGGER.debug("%s: Securing", self.name)
        assert self.session is not None  # nosec
        await self.session.execute(
            self.session.build_operation_command(Commands.LOCK, 0x04),
            "force_securemode",
        )
        _LOGGER.debug("%s: Finished securemode", self.name)

    @raise_if_not_connected
    async def force_lock(self) -> None:
        """Force the lock to lock."""
        _LOGGER.debug("%s: Locking", self.name)
        assert self.session is not None  # nosec
        await self.session.execute(
            self.session.build_command(Commands.LOCK), "force_lock"
        )
        _LOGGER.debug("%s: Finished locking", self.name)

    @raise_if_not_connected
    async def force_unlock(self) -> None:
        """Force the lock to unlock."""
        _LOGGER.debug("%s: Unlocking", self.name)
        assert self.session is not None  # nosec
        await self.session.execute(
            self.session.build_command(Commands.UNLOCK), "force_unlock"
        )
        _LOGGER.debug("%s: Finished unlocking", self.name)

    async def securemode(self) -> None:
        if (await self.lock_status()) != LockStatus.SECUREMODE:
            await self.force_securemode()

    async def lock(self) -> None:
        if (await self.lock_status()) != LockStatus.LOCKED:
            await self.force_lock()

    async def unlock(self) -> None:
        if (await self.lock_status()) != LockStatus.UNLOCKED:
            await self.force_unlock()

    async def _execute_command(
        self, opcode: int, cmd_byte: int, command_name: str
    ) -> bytes:
        assert self.session is not None  # nosec
        command = self.session.build_operation_command(opcode, cmd_byte)
        _LOGGER.debug("%s: send: [%s] [%s]", self.name, command.hex(), hex(cmd_byte))
        response = await self.session.execute(command, command_name)
        _LOGGER.debug(
            "%s: response: [%s] [%s]", self.name, response.hex(), hex(cmd_byte)
        )
        return response

    def _parse_lock_and_door_state(
        self, response: bytes
    ) -> tuple[LockStatus, DoorStatus]:
        """Parse the lock and door state from the response."""
        return self._parse_lock_status(response[0x08]), self._parse_door_status(
            response[0x09]
        )

    def _parse_lock_status(self, lock_status: int) -> LockStatus:
        """Parse the lock state from the response."""
        lock_status_enum = VALUE_TO_LOCK_STATUS.get(lock_status, LockStatus.UNKNOWN)
        if lock_status_enum == LockStatus.UNKNOWN:
            _LOGGER.info(
                "%s: Unrecognized lock_status_str code: %s", self.name, hex(lock_status)
            )
        return lock_status_enum

    def _parse_door_status(self, door_status: int) -> DoorStatus:
        """Parse the door state from the response."""
        door_status_enum = VALUE_TO_DOOR_STATUS.get(door_status, DoorStatus.UNKNOWN)
        if door_status_enum == DoorStatus.UNKNOWN:
            _LOGGER.info(
                "%s: Unrecognized door_status_str code: %s", self.name, hex(door_status)
            )
        return door_status_enum

    @raise_if_not_connected
    async def lock_status(self) -> LockStatus:
        _LOGGER.debug("%s: Executing lock_status", self.name)
        # We used to use 0x2F here but it seems to be broken on some locks
        response = await self._execute_command(Commands.GETSTATUS, 0x02, "lock_status")
        _LOGGER.debug("%s: Finished executing lock_status", self.name)
        return self._parse_lock_status(response[0x08])

    @raise_if_not_connected
    async def door_status(self) -> DoorStatus:
        _LOGGER.debug("%s: Executing door_status", self.name)
        # We used to use 0x2F here but it seems to be broken on some locks
        response = await self._execute_command(Commands.GETSTATUS, 0x2E, "door_status")
        _LOGGER.debug("%s: Finished executing door_status", self.name)
        return self._parse_door_status(response[0x08])

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

    @raise_if_not_connected
    async def battery(self) -> BatteryState:
        _LOGGER.debug("%s: Executing battery", self.name)
        response = await self._execute_command(Commands.GETSTATUS, 0x0F, "battery")
        _LOGGER.debug("%s: Finished executing battery", self.name)
        return self._parse_battery_state(response)

    async def disconnect(self) -> None:
        """Disconnect from the lock."""
        _LOGGER.debug("%s: Disconnecting from the lock", self.name)
        if not self.client or not self.client.is_connected:
            return

        try:
            await self._shutdown_connection()
        except BleakError:
            _LOGGER.debug(
                "%s: Failed to shutdown connection to lock", self.name, exc_info=True
            )
        finally:
            try:
                await self.client.disconnect()
            except BleakError:
                _LOGGER.debug(
                    "%s: Failed to disconnect from lock", self.name, exc_info=True
                )

    async def _shutdown_connection(self) -> None:
        """Shutdown the connection."""
        _LOGGER.debug("%s: Shutting down the connection", self.name)
        if self.session:
            await self.session.stop_notify()
        if not self.is_secure or not self.secure_session or self._disconnected:
            return
        cmd = self.secure_session.build_command(0x05)
        cmd[0x11] = 0x00
        response = None
        try:
            response = await self.secure_session.execute(cmd, "shutdown")
            await self.secure_session.stop_notify()
        except (AuthError, DisconnectedError):
            # Lock already disconnected us
            return
        except (BleakError, asyncio.TimeoutError, EOFError) as err:
            if not util.is_disconnected_error(err):
                _LOGGER.debug(
                    "%s: Failed to cleanly disconnect from lock: %s", self.name, err
                )
            return
        except YaleXSBLEError as err:
            _LOGGER.debug(
                "%s: Failed to cleanly disconnect from lock: %s", self.name, err
            )
            return
        if response and response[0] != 0x8B:
            _LOGGER.debug("%s: Unexpected response to DISCONNECT: %s", response.hex())

    @property
    def is_connected(self) -> bool:
        """Return True if the lock is connected."""
        return bool(
            self.client
            and self.client.is_connected
            and self.session
            and self.secure_session
            and not self._disconnected
        )
