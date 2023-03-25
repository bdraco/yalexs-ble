from __future__ import annotations

import asyncio
import contextlib
import logging
import struct
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import replace
from typing import Any, TypeVar, cast

import async_timeout
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDBusError, BleakError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS, BleakNotFoundError, get_device

from .const import (
    APPLE_MFR_ID,
    HAP_ENCRYPTED_FIRST_BYTE,
    HAP_FIRST_BYTE,
    YALE_MFR_ID,
    AuthState,
    BatteryState,
    ConnectionInfo,
    DoorStatus,
    LockInfo,
    LockState,
    LockStatus,
)
from .lock import Lock
from .session import (
    AuthError,
    BluetoothError,
    DisconnectedError,
    NoAdvertisementError,
    ResponseError,
    YaleXSBLEError,
)
from .util import is_disconnected_error, local_name_is_unique

_LOGGER = logging.getLogger(__name__)

# Advertisement debugger (this one is quite noisy so it has its only logger)
_ADV_LOGGER = logging.getLogger("yalexs_ble_adv")

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

NEVER_TIME = -86400.0

DEFAULT_ATTEMPTS = 4

DISCONNECT_DELAY = 5.1

RESYNC_DELAY = 0.01

# After a lock operation we need to wait for the lock to
# update its state or it will return a stale state.
LOCK_STATE_STATE_DEBOUNCE_DELAY = 3.0

# How long to wait before processing an advertisement change
ADV_UPDATE_COALESCE_SECONDS = 0.05

# How long to wait before processing the first update
FIRST_UPDATE_COALESCE_SECONDS = 0.01

# How long to wait before processing a HomeKit advertisement change
HK_UPDATE_COALESCE_SECONDS = 0.025

# How long to wait before processing a manual update request
MANUAL_UPDATE_COALESCE_SECONDS = 0.05

# How long to wait to query the lock after an operation to make sure its not jammed
POST_OPERATION_SYNC_TIME = 10.00

# How long to wait if we get an update storm from the lock
UPDATE_IN_PROGRESS_DEFER_SECONDS = 1.0

RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError, DisconnectedError)

RETRY_EXCEPTIONS = (ResponseError, *BLEAK_RETRY_EXCEPTIONS)

# 255 seems to be broadcast randomly when
# there is no update from the lock.
VALID_ADV_VALUES = {0, 1}

AUTH_FAILURE_TO_START_REAUTH = 5


def operation_lock(func: WrapFuncType) -> WrapFuncType:
    """Define a wrapper to only allow a single operation at a time."""

    async def _async_wrap_operation_lock(
        self: "PushLock", *args: Any, **kwargs: Any
    ) -> None:
        _LOGGER.debug("%s: Acquiring lock", self.name)
        async with self._operation_lock:
            return await func(self, *args, **kwargs)

    return cast(WrapFuncType, _async_wrap_operation_lock)


def retry_bluetooth_connection_error(func: WrapFuncType) -> WrapFuncType:
    """Define a wrapper to retry on bleak error.

    The accessory is allowed to disconnect us any time so
    we need to retry the operation.
    """

    async def _async_wrap_retry_bluetooth_connection_error(
        self: "PushLock", *args: Any, **kwargs: Any
    ) -> Any:
        _LOGGER.debug("%s: Starting retry loop", self.name)
        attempts = DEFAULT_ATTEMPTS
        max_attempts = attempts - 1

        for attempt in range(attempts):
            try:
                return await func(self, *args, **kwargs)
            except AuthError:
                self._auth_failures += 1
                if self._auth_failures >= AUTH_FAILURE_TO_START_REAUTH:
                    # If the bluetooth connection drops in the middle of authentication
                    # we may see it as a failed authentication. If we see 5 failed
                    # authentications in a row we can reasonably assume that the key has
                    # changed and we should re-authenticate.
                    self._update_any_state([AuthState(successful=False)])
                raise
            except BleakNotFoundError:
                # The lock cannot be found so there is no
                # point in retrying.
                raise
            except RETRY_BACKOFF_EXCEPTIONS as err:
                if attempt >= max_attempts:
                    _LOGGER.debug(
                        "%s: %s error calling %s, reach max attempts (%s/%s)",
                        self.name,
                        type(err),
                        func,
                        attempt,
                        max_attempts,
                        exc_info=True,
                    )
                    if is_disconnected_error(err):
                        raise DisconnectedError(str(err))
                    raise
                _LOGGER.debug(
                    "%s: %s error calling %s, backing off %ss, retrying (%s/%s)...",
                    self.name,
                    type(err),
                    func,
                    0.25,
                    attempt,
                    max_attempts,
                    exc_info=True,
                )
                await asyncio.sleep(0.25)
            except RETRY_EXCEPTIONS as err:
                if attempt >= max_attempts:
                    _LOGGER.debug(
                        "%s: %s error calling %s, reach max attempts (%s/%s)",
                        self.name,
                        type(err),
                        func,
                        attempt,
                        max_attempts,
                        exc_info=True,
                    )
                    if is_disconnected_error(err):
                        raise DisconnectedError(str(err))
                    raise
                _LOGGER.debug(
                    "%s: %s error calling %s, retrying  (%s/%s)...",
                    self.name,
                    type(err),
                    func,
                    attempt,
                    max_attempts,
                    exc_info=True,
                )

    return cast(WrapFuncType, _async_wrap_retry_bluetooth_connection_error)


class PushLock:
    """A lock with push updates."""

    def __init__(
        self,
        local_name: str | None = None,
        address: str | None = None,
        ble_device: BLEDevice | None = None,
        key: str | None = None,
        key_index: int | None = None,
        advertisement_data: AdvertisementData | None = None,
        idle_disconnect_delay: float = DISCONNECT_DELAY,
    ) -> None:
        """Init the lock watcher."""
        if local_name is None and address is None:
            raise ValueError("Must specify either local_name or address")
        if not address and not local_name_is_unique(local_name):
            raise ValueError("local_name must be unique when address is not provided")

        self._local_name = local_name
        self._local_name_is_unique = local_name_is_unique(local_name)
        self._address = address
        self._name: str | None = None
        self._lock_info: LockInfo | None = None
        self._lock_state: LockState | None = None
        self._last_adv_value = -1
        self._last_hk_state = -1
        self._lock_key = key
        self._lock_key_index = key_index
        self._advertisement_data = advertisement_data
        self._ble_device = ble_device
        self._operation_lock = asyncio.Lock()
        self._running = False
        self._callbacks: list[
            Callable[[LockState, LockInfo, ConnectionInfo], None]
        ] = []
        self._update_task: asyncio.Task[None] | None = None
        self.loop = asyncio._get_running_loop()
        self._cancel_deferred_update: asyncio.TimerHandle | None = None
        self._client: Lock | None = None
        self._connect_lock = asyncio.Lock()
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._idle_disconnect_delay = idle_disconnect_delay
        self._first_update_future: asyncio.Future[None] | None = None
        self._background_tasks: set[asyncio.Task[None]] = set()
        self._auth_failures: int = 0
        self._last_lock_operation_complete_time = NEVER_TIME

    @property
    def local_name(self) -> str | None:
        """Get the local name."""
        return self._local_name

    @property
    def name(self) -> str:
        """Get the name of the lock."""
        if self._name:
            return self._name
        if self._local_name_is_unique and self._local_name:
            return self._local_name
        return self.address

    @property
    def address(self) -> str:
        """Get the address of the lock."""
        return self._ble_device.address if self._ble_device else self._address

    @property
    def door_status(self) -> DoorStatus:
        """Return the current door status."""
        return self._lock_state.door if self._lock_state else DoorStatus.UNKNOWN

    @property
    def lock_status(self) -> LockStatus:
        """Return the current lock status."""
        return self._lock_state.lock if self._lock_state else LockStatus.UNKNOWN

    @property
    def battery(self) -> BatteryState | None:
        """Return the current battery state."""
        return self._lock_state.battery if self._lock_state else None

    @property
    def auth(self) -> AuthState | None:
        """Return the current auth state."""
        return self._lock_state.auth if self._lock_state else None

    @property
    def lock_state(self) -> LockState | None:
        """Return the current lock state."""
        return self._lock_state

    @property
    def lock_info(self) -> LockInfo | None:
        """Return the current lock info."""
        return self._lock_info

    @property
    def connection_info(self) -> ConnectionInfo | None:
        """Return the current connection info."""
        if self._advertisement_data:
            return ConnectionInfo(self._advertisement_data.rssi)
        return None

    @property
    def ble_device(self) -> BLEDevice | None:
        """Return the current BLEDevice."""
        return self._ble_device

    def set_name(self, name: str) -> None:
        """Set the name of the lock."""
        self._name = name

    def reset_advertisement_state(self) -> None:
        """Reset the advertisement state."""
        self._last_adv_value = -1
        self._last_hk_state = -1

    def register_callback(
        self, callback: Callable[[LockState, LockInfo, ConnectionInfo], None]
    ) -> Callable[[], None]:
        """Register a callback to be called when the lock state changes."""

        def unregister_callback() -> None:
            self._callbacks.remove(callback)

        self._callbacks.append(callback)
        return unregister_callback

    def set_lock_key(self, key: str, slot: int) -> None:
        """Set the lock key."""
        self._lock_key = key
        self._lock_key_index = slot

    def set_ble_device(self, ble_device: BLEDevice) -> None:
        """Set the ble device."""
        self._ble_device = ble_device
        self._address = ble_device.address

    def set_advertisement_data(self, advertisement_data: AdvertisementData) -> None:
        """Set the advertisement data."""
        self._advertisement_data = advertisement_data

    def _get_lock_instance(self) -> Lock:
        """Get the lock instance."""
        assert self._ble_device is not None  # nosec
        assert self._lock_key is not None  # nosec
        assert self._lock_key_index is not None  # nosec
        return Lock(
            lambda: self._ble_device,
            self._lock_key,
            self._lock_key_index,
            self.name,
            self._state_callback,
            self._lock_info,
        )

    def _reset_disconnect_timer(self) -> None:
        """Reset disconnect timer."""
        self._cancel_disconnect_timer()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            self._idle_disconnect_delay, self._disconnect_with_timer
        )

    async def _execute_forced_disconnect(self) -> None:
        """Execute forced disconnection."""
        self._cancel_disconnect_timer()
        _LOGGER.debug(
            "%s: Executing forced disconnect",
            self.name,
        )
        if (update_task := self._update_task) and not update_task.done():
            self._update_task = None
            update_task.cancel()
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await update_task
        await self._execute_disconnect()

    def _disconnect_with_timer(self) -> None:
        """Disconnect from device."""
        if self._operation_lock.locked():
            _LOGGER.debug("%s: Disconnect timer reset due to operation lock", self.name)
            self._reset_disconnect_timer()
            return
        if self._cancel_deferred_update:
            _LOGGER.debug(
                "%s: Disconnect timer fired while we were waiting to update", self.name
            )
            self._reset_disconnect_timer()
            self._cancel_future_update()
            self._deferred_update()
            return
        self._cancel_disconnect_timer()
        self.background_task(self._execute_timed_disconnect())

    def _cancel_disconnect_timer(self) -> None:
        """Cancel disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    async def _execute_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        _LOGGER.debug(
            "%s: Executing timed disconnect after timeout of %s",
            self.name,
            DISCONNECT_DELAY,
        )
        await self._execute_disconnect()

    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        async with self._connect_lock:
            if self._disconnect_timer:  # If the timer was reset, don't disconnect
                return
            client = self._client
            self._client = None
            if client:
                _LOGGER.debug("%s: Disconnecting", self.name)
                await client.disconnect()
                _LOGGER.debug("%s: Disconnect completed", self.name)

    async def _ensure_connected(self) -> Lock:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            self._reset_disconnect_timer()
            _LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete",
                self.name,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return self._client
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                self._reset_disconnect_timer()
                return self._client
            self._client = self._get_lock_instance()
            try:
                await self._client.connect()
            except Exception as ex:
                _LOGGER.debug(
                    "%s: Failed to connect due to %s, forcing disconnect", self.name, ex
                )
                await self._client.disconnect()
                raise
            self._reset_disconnect_timer()
            return self._client

    async def lock(self) -> None:
        """Lock the lock."""
        self._update_any_state([LockStatus.LOCKING])
        self._cancel_future_update()
        await self._execute_lock_operation(
            "force_lock", LockStatus.LOCKING, LockStatus.LOCKED
        )

    async def unlock(self) -> None:
        """Unlock the lock."""
        self._update_any_state([LockStatus.UNLOCKING])
        self._cancel_future_update()
        await self._execute_lock_operation(
            "force_unlock", LockStatus.UNLOCKING, LockStatus.UNLOCKED
        )

    @operation_lock
    @retry_bluetooth_connection_error
    async def _execute_lock_operation(
        self, op_attr: str, pending_state: LockStatus, complete_state: LockStatus
    ) -> None:
        """Execute a lock operation."""
        _LOGGER.debug("%s: Starting %s", self.name, pending_state)
        self._update_any_state([pending_state])
        self._cancel_future_update()
        try:
            lock = await self._ensure_connected()
            self._cancel_future_update()
            await getattr(lock, op_attr)()
        except Exception:
            self._update_any_state([LockStatus.UNKNOWN])
            raise
        self._update_any_state([complete_state])
        _LOGGER.debug("%s: Finished %s", self.name, complete_state)
        self._last_lock_operation_complete_time = time.monotonic()
        self._reset_disconnect_timer()

    def _state_callback(
        self, states: Iterable[LockStatus | DoorStatus | BatteryState]
    ) -> None:
        """Handle state change."""
        self._reset_disconnect_timer()
        self._update_any_state(states)

    def _update_any_state(
        self, states: Iterable[LockStatus | DoorStatus | BatteryState | AuthState]
    ) -> None:
        _LOGGER.debug("%s: State changed: %s", self.name, states)
        lock_state = self._lock_state or LockState(
            self.lock_status, self.door_status, self.battery, self.auth
        )
        original_lock_status = lock_state.lock
        for state in states:
            if isinstance(state, AuthState):
                lock_state = replace(lock_state, auth=state)
            elif isinstance(state, LockStatus):
                lock_state = replace(lock_state, lock=state)
            elif isinstance(state, DoorStatus):
                lock_state = replace(lock_state, door=state)
            elif isinstance(state, BatteryState):
                if state.voltage <= 3.0:
                    _LOGGER.debug(
                        "%s: Battery voltage is impossible: %s",
                        self.name,
                        state.voltage,
                    )
                    continue
                lock_state = replace(lock_state, battery=state)
            else:
                raise ValueError(f"Unexpected state type: {state}")

        if (
            original_lock_status != lock_state.lock
            and (not lock_state.auth or lock_state.auth.successful)
            and original_lock_status != LockStatus.UNKNOWN
        ):
            self._schedule_future_update(RESYNC_DELAY)

        self._callback_state(lock_state)

    async def update(self) -> None:
        """Request that status be updated."""
        self._schedule_future_update_with_debounce(
            0
            if self._client and self._client.is_connected
            else MANUAL_UPDATE_COALESCE_SECONDS
        )

    async def validate(self) -> None:
        """Validate lock credentials."""
        _LOGGER.debug("%s: Starting validate", self.name)
        await self._update()
        _LOGGER.debug("%s: Finished validate", self.name)

    @operation_lock
    @retry_bluetooth_connection_error
    async def _update(self) -> LockState:
        """Update the lock state."""
        has_lock_info = self._lock_info is not None

        _LOGGER.debug(
            "%s: Starting update (has_lock_info: %s)", self.name, has_lock_info
        )
        try:
            lock = await self._ensure_connected()
            if not self._lock_info:
                self._lock_info = await lock.lock_info()
            state = await lock.status()
            battery_state = await lock.battery()
        except asyncio.CancelledError:
            _LOGGER.debug(
                "%s: In-progress update canceled due "
                "to lock operation or setup timeout",
                self.name,
            )
            raise
        else:
            self._auth_failures = 0
            state = replace(
                state, battery=battery_state, auth=AuthState(successful=True)
            )
        _LOGGER.debug("%s: Finished update", self.name)
        self._callback_state(state)

        if not has_lock_info:
            # On first update free up the connection
            # so we can bring other locks online if
            # the bluetooth adapter is out of connections
            # slots
            await self._execute_forced_disconnect()

        return state

    def _callback_state(self, lock_state: LockState) -> None:
        """Call the callbacks."""
        self._lock_state = lock_state
        _LOGGER.debug(
            "%s: New state: %s %s %s",
            self.name,
            self._lock_state,
            self._lock_info,
            self.connection_info,
        )
        if not self._callbacks:
            return
        assert self._lock_info is not None  # nosec
        connection_info = self.connection_info
        assert connection_info is not None  # nosec
        for callback in self._callbacks:
            try:
                callback(lock_state, self._lock_info, connection_info)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("%s: Error calling callback", self.name)

    def update_advertisement(
        self, ble_device: BLEDevice, ad: AdvertisementData
    ) -> None:
        """Update the advertisement."""
        adv_debug_enabled = _ADV_LOGGER.isEnabledFor(logging.DEBUG)
        if self._local_name_is_unique and self._local_name == ad.local_name:
            if adv_debug_enabled:
                _ADV_LOGGER.debug(
                    "%s: Accepting new advertisement since local_name %s matches: %s",
                    self.name,
                    ad.local_name,
                    ad,
                )
        elif self.address and self.address == ble_device.address:
            if adv_debug_enabled:
                _ADV_LOGGER.debug(
                    "%s: Accepting new advertisement since address %s matches: %s",
                    self.name,
                    self.address,
                    ad,
                )
        else:
            return
        self.set_ble_device(ble_device)
        self.set_advertisement_data(ad)
        next_update = 0.0
        mfr_data = ad.manufacturer_data
        if APPLE_MFR_ID in mfr_data:
            first_byte = mfr_data[APPLE_MFR_ID][0]
            if first_byte == HAP_FIRST_BYTE:
                hk_state = get_homekit_state_num(mfr_data[APPLE_MFR_ID])
                # Sometimes the yale data is glued on to the end of the HomeKit data
                # but in that case it seems wrong so we don't process it
                #
                # if len(mfr_data[APPLE_MFR_ID]) > 20 and YALE_MFR_ID not in mfr_data:
                # mfr_data[YALE_MFR_ID] = mfr_data[APPLE_MFR_ID][20:]
                if self._last_hk_state == -1:
                    # We haven't seen a HomeKit state yet so we schedule an update
                    next_update = FIRST_UPDATE_COALESCE_SECONDS
                elif hk_state != self._last_hk_state:
                    next_update = HK_UPDATE_COALESCE_SECONDS
                self._last_hk_state = hk_state
            elif first_byte == HAP_ENCRYPTED_FIRST_BYTE:
                # Encrypted data, we don't know how to decrypt it
                # but we know its a state change so we schedule an update
                next_update = HK_UPDATE_COALESCE_SECONDS
        if YALE_MFR_ID in mfr_data:
            current_value = mfr_data[YALE_MFR_ID][0]
            if not next_update:
                if self._last_adv_value == -1:
                    # We haven't seen a valid value yet so we schedule an update
                    next_update = FIRST_UPDATE_COALESCE_SECONDS
                elif (
                    current_value in VALID_ADV_VALUES
                    and current_value != self._last_adv_value
                ):
                    next_update = ADV_UPDATE_COALESCE_SECONDS
            self._last_adv_value = current_value
        if adv_debug_enabled:
            scheduled_update = None
            if self._cancel_deferred_update:
                scheduled_update = (
                    self._cancel_deferred_update.when() - self.loop.time()
                )
            _ADV_LOGGER.debug(
                "%s: State: (current_state: %s) (hk_state: %s) "
                "(adv_value: %s) (next_update: %s) (scheduled_update: %s)",
                self.name,
                self._lock_state,
                self._last_hk_state,
                self._last_adv_value,
                next_update,
                scheduled_update,
            )
        if next_update:
            self._schedule_future_update_with_debounce(next_update)

    async def start(self) -> Callable[[], None]:
        """Start watching for updates."""
        _LOGGER.debug("Waiting for advertisement callbacks for %s", self.name)
        if self._running:
            raise RuntimeError("Already running")
        self._running = True
        self._first_update_future = asyncio.get_running_loop().create_future()
        if device := await get_device(self.address):
            self.set_ble_device(device)
            self._schedule_future_update_with_debounce(ADV_UPDATE_COALESCE_SECONDS)

        def _cancel() -> None:
            self._running = False
            self._cancel_future_update()
            self.background_task(self._execute_forced_disconnect())

        return _cancel

    def background_task(self, fut: Awaitable[Any]) -> None:
        """Execute a background task."""
        task = asyncio.create_task(fut)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.remove)

    async def wait_for_first_update(self, timeout: float) -> None:
        """Wait for the first update."""
        if not self._running:
            raise RuntimeError("Not running")
        if not self._first_update_future:
            raise RuntimeError("Already waited for first update")
        try:
            async with async_timeout.timeout(timeout):
                await self._first_update_future
        except asyncio.TimeoutError:
            self._first_update_future.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._first_update_future
            raise NoAdvertisementError("No advertisement received")
        finally:
            self._first_update_future = None

    def _cancel_future_update(self) -> None:
        """Cancel an update."""
        if self._cancel_deferred_update:
            self._cancel_deferred_update.cancel()
            self._cancel_deferred_update = None

    def _schedule_future_update_with_debounce(self, seconds: float) -> None:
        """Schedule an update with a potential debounce."""
        now = self.loop.time()
        future_update_time = seconds
        if self._cancel_deferred_update:
            time_till_update = self._cancel_deferred_update.when() - now
            if time_till_update < HK_UPDATE_COALESCE_SECONDS:
                future_update_time = HK_UPDATE_COALESCE_SECONDS
                _LOGGER.debug(
                    "%s: Existing update too soon %s, "
                    "rescheduling update for in %s seconds",
                    self.name,
                    time_till_update,
                    future_update_time,
                )
            elif time_till_update < seconds:
                _LOGGER.debug(
                    "%s: Existing update in %s seconds will happen sooner than now",
                    self.name,
                    time_till_update,
                )
                return
            _LOGGER.debug("%s: Rescheduling update", self.name)
        self._schedule_future_update(future_update_time)

    def _schedule_future_update(self, future_update_time: float) -> None:
        """Schedule an update in future seconds."""
        _LOGGER.debug(
            "%s: Scheduling update to happen in %s seconds",
            self.name,
            future_update_time,
        )
        self._cancel_future_update()
        self._cancel_deferred_update = self.loop.call_later(
            future_update_time, self._deferred_update
        )

    def _deferred_update(self) -> None:
        """Update the lock state."""
        self._cancel_future_update()
        now = time.monotonic()
        if self._update_task and not self._update_task.done():
            _LOGGER.debug(
                "%s: Rescheduling update since one already in progress", self.name
            )
            self._schedule_future_update_with_debounce(UPDATE_IN_PROGRESS_DEFER_SECONDS)
            return
        if (
            seconds_time_lock_op := (now - self._last_lock_operation_complete_time)
        ) < LOCK_STATE_STATE_DEBOUNCE_DELAY:
            _LOGGER.debug("%s: Rescheduling update to avoid stale state", self.name)
            self._schedule_future_update_with_debounce(seconds_time_lock_op)
            return
        self._update_task = asyncio.create_task(self._execute_deferred_update())

    def _set_update_state(self, exception: Exception | None) -> None:
        """Set the update state."""
        if not self._first_update_future:
            return
        if exception:
            self._first_update_future.set_exception(exception)
        else:
            self._first_update_future.set_result(None)

    async def _execute_deferred_update(self) -> None:
        """Execute deferred update."""
        _LOGGER.debug("%s: Deferred update starting", self.name)
        if not self._running:
            _LOGGER.debug("%s: Deferred updated ignored because not running", self.name)
            return
        _LOGGER.debug("%s: Starting deferred update", self.name)
        try:
            await self._update()
            self._set_update_state(None)
        except AuthError as ex:
            self._set_update_state(ex)
            _LOGGER.error(
                "%s: Auth error: key or slot (key index) is incorrect: %s",
                self.name,
                ex,
                exc_info=True,
            )
        except asyncio.CancelledError:
            self._set_update_state(RuntimeError("Update was canceled"))
            _LOGGER.debug("%s: In-progress update canceled", self.name)
        except asyncio.TimeoutError as ex:
            self._set_update_state(ex)
            _LOGGER.exception("%s: Timed out updating", self.name)
        except BleakError as ex:
            wrapped_bleak_exc = BluetoothError(str(ex))
            wrapped_bleak_exc.__cause__ = ex
            self._set_update_state(wrapped_bleak_exc)
            _LOGGER.exception("%s: Bluetooth error updating", self.name)
        except Exception as ex:  # pylint: disable=broad-except
            wrapped_exc = YaleXSBLEError(str(ex))
            wrapped_exc.__cause__ = ex
            self._set_update_state(wrapped_exc)
            _LOGGER.exception("%s: Unknown error updating", self.name)


def get_homekit_state_num(data: bytes) -> int:
    """Get the homekit state number from the manufacturer data."""
    acid, gsn, cn, cv = struct.unpack("<HHBB", data[9:15])
    return gsn
