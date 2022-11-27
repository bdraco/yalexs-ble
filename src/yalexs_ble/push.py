from __future__ import annotations

import asyncio
import contextlib
import logging
import struct
from collections.abc import Callable
from typing import Any, TypeVar, cast

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDBusError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS, BleakNotFoundError, get_device

from .const import (
    APPLE_MFR_ID,
    HAP_ENCRYPTED_FIRST_BYTE,
    HAP_FIRST_BYTE,
    YALE_MFR_ID,
    ConnectionInfo,
    DoorStatus,
    LockInfo,
    LockState,
    LockStatus,
)
from .lock import Lock
from .session import AuthError, DisconnectedError, ResponseError
from .util import is_disconnected_error, local_name_is_unique

_LOGGER = logging.getLogger(__name__)

# Advertisement debugger (this one is quite noisy so it has its only logger)
_ADV_LOGGER = logging.getLogger("yalexs_ble_adv")

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

DEFAULT_ATTEMPTS = 4

# How long to wait before processing an advertisement change
ADV_UPDATE_COALESCE_SECONDS = 6.99

# How long to wait before processing the first update
FIRST_UPDATE_COALESCE_SECONDS = 0.50

# How long to wait before processing a HomeKit advertisement change
HK_UPDATE_COALESCE_SECONDS = 2.00

# How long to wait before processing a manual update request
MANUAL_UPDATE_COALESCE_SECONDS = 0.75

# How long to wait to query the lock after an operation to make sure its not jammed
POST_OPERATION_SYNC_TIME = 10.00

# How long to wait if we get an update storm from the lock
UPDATE_IN_PROGRESS_DEFER_SECONDS = 29.50

RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError, DisconnectedError)

RETRY_EXCEPTIONS = (ResponseError, *BLEAK_RETRY_EXCEPTIONS)

# 255 seems to be broadcast randomly when
# there is no update from the lock.
VALID_ADV_VALUES = {0, 1}


def cancelable_operation(func: WrapFuncType) -> WrapFuncType:
    """Define a wrapper to make mutually exclusive operations cancelable."""

    async def _async_wrap_cancelable_operation(
        self: "PushLock", *args: Any, **kwargs: Any
    ) -> None:
        await self._cancel_in_progress_operation()
        await self._cancel_in_progress_update()
        self._operation_task = asyncio.create_task(func(self, *args, **kwargs))
        await self._operation_task
        self._operation_task = None

    return cast(WrapFuncType, _async_wrap_cancelable_operation)


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
        self._operation_task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._update_task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._debounce_lock = asyncio.Lock()
        self.loop = asyncio._get_running_loop()
        self._cancel_deferred_update: asyncio.TimerHandle | None = None
        self.last_error: str | None = None
        self.auth_error = False

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
            self._lock_info,
        )

    async def _cancel_any_update(self) -> None:
        """Cancel any update task."""
        await asyncio.sleep(0)
        await self._cancel_in_progress_update()

    async def _cancel_in_progress_update(self) -> None:
        """Cancel any in progress update task."""
        if self._update_task:
            _LOGGER.debug("Canceling in progress update: %s", self._update_task)
            self._update_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._update_task
            self._update_task = None

    async def _cancel_in_progress_operation(self) -> None:
        """Cancel any in progress operation task."""
        if self._operation_task:
            _LOGGER.debug("Canceling in progress task: %s", self._operation_task)
            self._operation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._operation_task
            self._operation_task = None

    @cancelable_operation
    @operation_lock
    @retry_bluetooth_connection_error
    async def lock(self) -> None:
        """Lock the lock."""
        _LOGGER.debug("%s: Starting lock", self.name)
        await self._cancel_any_update()
        self._callback_state(LockState(LockStatus.LOCKING, self.door_status))
        lock = self._get_lock_instance()
        try:
            async with lock:
                await lock.force_lock()
        except Exception:
            self._callback_state(LockState(LockStatus.UNKNOWN, self.door_status))
            raise
        self._callback_state(LockState(LockStatus.LOCKED, self.door_status))
        await self._cancel_any_update()
        self._schedule_update(POST_OPERATION_SYNC_TIME)
        _LOGGER.debug("%s: Finished lock", self.name)

    @cancelable_operation
    @operation_lock
    @retry_bluetooth_connection_error
    async def unlock(self) -> None:
        """Unlock the lock."""
        _LOGGER.debug("%s: Starting unlock", self.name)
        await self._cancel_any_update()
        self._callback_state(LockState(LockStatus.UNLOCKING, self.door_status))
        lock = self._get_lock_instance()
        try:
            async with lock:
                await lock.force_unlock()
        except Exception:
            self._callback_state(LockState(LockStatus.UNKNOWN, self.door_status))
            raise
        self._callback_state(LockState(LockStatus.UNLOCKED, self.door_status))
        await self._cancel_any_update()
        self._schedule_update(POST_OPERATION_SYNC_TIME)
        _LOGGER.debug("%s: Finished unlock", self.name)

    async def update(self) -> None:
        """Request that status be updated."""
        self._schedule_update(MANUAL_UPDATE_COALESCE_SECONDS)

    async def validate(self) -> None:
        """Validate lock credentials."""
        _LOGGER.debug("%s: Starting validate", self.name)
        await self._update()
        _LOGGER.debug("%s: Finished validate", self.name)

    @operation_lock
    @retry_bluetooth_connection_error
    async def _update(self) -> LockState:
        """Update the lock state."""
        _LOGGER.debug("%s: Starting update", self.name)
        lock = self._get_lock_instance()
        try:
            async with lock:
                if not self._lock_info:
                    self._lock_info = await lock.lock_info()
                state = await lock.status()
        except asyncio.CancelledError:
            _LOGGER.debug(
                "%s: In-progress update canceled due "
                "to lock operation or setup timeout",
                self.name,
            )
            raise
        _LOGGER.debug("%s: Finished update", self.name)
        self._callback_state(state)
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
                if hk_state != self._last_hk_state:
                    if self._last_hk_state == -1:
                        next_update = FIRST_UPDATE_COALESCE_SECONDS
                    else:
                        next_update = HK_UPDATE_COALESCE_SECONDS
                    self._last_hk_state = hk_state
            elif first_byte == HAP_ENCRYPTED_FIRST_BYTE:
                # Encrypted data, we don't know how to decrypt it
                # but we know its a state change so we schedule an update
                next_update = HK_UPDATE_COALESCE_SECONDS
        if YALE_MFR_ID in mfr_data:
            current_value = mfr_data[YALE_MFR_ID][0]
            if (
                current_value in VALID_ADV_VALUES
                and current_value != self._last_adv_value
            ):
                if not next_update:
                    if self._last_adv_value == -1:
                        next_update = FIRST_UPDATE_COALESCE_SECONDS
                    else:
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
            self._schedule_update(next_update)

    async def start(self) -> Callable[[], None]:
        """Start watching for updates."""
        _LOGGER.debug("Waiting for advertisement callbacks for %s", self.name)
        if self._running:
            raise RuntimeError("Already running")
        self.last_error = "No Bluetooth advertisement received"
        self._running = True
        if device := await get_device(self.address):
            self.set_ble_device(device)
            self._schedule_update(ADV_UPDATE_COALESCE_SECONDS)

        def _cancel() -> None:
            self._running = False
            asyncio.create_task(self._cancel_in_progress_update())

        return _cancel

    def _schedule_update(self, seconds: float) -> None:
        """Schedule an update."""
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
            self._cancel_deferred_update.cancel()
            self._cancel_deferred_update = None
        _LOGGER.debug(
            "%s: Scheduling update to happen in %s seconds",
            self.name,
            future_update_time,
        )
        self._cancel_deferred_update = self.loop.call_at(
            now + future_update_time, self._deferred_update
        )

    def _deferred_update(self) -> None:
        """Update the lock state."""
        self._cancel_deferred_update = None
        if self._debounce_lock.locked():
            _LOGGER.debug(
                "%s: Rescheduling update since one already in progress", self.name
            )
            self._schedule_update(UPDATE_IN_PROGRESS_DEFER_SECONDS)
            return
        self.loop.create_task(self._queue_update())

    async def _queue_update(self) -> None:
        """Watch for updates."""
        _LOGGER.debug("%s: Update queued", self.name)
        async with self._debounce_lock:
            _LOGGER.debug("%s: Queued update starting", self.name)
            if not self._running:
                _LOGGER.debug(
                    "%s: Queued updated ignored because not running", self.name
                )
                return
            _LOGGER.debug("%s: Starting update", self.name)
            try:
                self.last_error = "Could not connect"
                self._update_task = asyncio.create_task(self._update())
                await self._update_task
                self._update_task = None
            except AuthError as ex:
                self.auth_error = True
                self.last_error = (
                    f"Authentication error: key or slot (key index) is incorrect: {ex}"
                )
                _LOGGER.error(
                    "%s: Auth error: key or slot (key index) is incorrect: %s",
                    self.name,
                    ex,
                    exc_info=True,
                )
            except ValueError as ex:
                self.auth_error = True
                self.last_error = (
                    "Authentication value error: key or slot "
                    f"(key index) is incorrect: {ex}"
                )
                _LOGGER.error(
                    "%s: Auth value error: key or slot (key index) is incorrect: %s",
                    self.name,
                    ex,
                    exc_info=True,
                )
            except asyncio.CancelledError:
                _LOGGER.debug("%s: In-progress update canceled", self.name)
            except asyncio.TimeoutError:
                self.last_error = "Timed out updating"
                _LOGGER.exception("%s: Timed out updating", self.name)
            except Exception as ex:  # pylint: disable=broad-except
                self.last_error = str(ex)
                _LOGGER.exception("%s: Error updating", self.name)


def get_homekit_state_num(data: bytes) -> int:
    """Get the homekit state number from the manufacturer data."""
    acid, gsn, cn, cv = struct.unpack("<HHBB", data[9:15])
    return gsn
