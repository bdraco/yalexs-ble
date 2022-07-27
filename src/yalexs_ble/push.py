import asyncio
import logging
import struct
from collections.abc import Callable
from typing import Any, TypeVar, cast

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import BleakError

from .const import (
    APPLE_MFR_ID,
    HAP_FIRST_BYTE,
    YALE_MFR_ID,
    DoorStatus,
    LockState,
    LockStatus,
)
from .lock import Lock
from .session import AuthError, ResponseError

_LOGGER = logging.getLogger(__name__)


WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

DEFAULT_ATTEMPTS = 3


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
            except asyncio.TimeoutError:
                if attempt == max_attempts:
                    raise
                _LOGGER.debug(
                    "%s: Timeout error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except ResponseError:
                if attempt == max_attempts:
                    raise
                _LOGGER.debug(
                    "%s: Response error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except BleakError:
                if attempt == max_attempts:
                    raise
                _LOGGER.debug(
                    "%s: Bleak error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except AuthError:
                raise

    return cast(WrapFuncType, _async_wrap_retry_bluetooth_connection_error)


class PushLock:
    """A lock with push updates."""

    def __init__(self, local_name: str) -> None:
        """Init the lock watcher."""
        self._local_name = local_name
        self._lock_state: LockState | None = None
        self._update_queue: asyncio.Queue[BLEDevice] = asyncio.Queue(1)
        self._last_adv_value = -1
        self._last_hk_state = -1
        self._lock_key: str | None = None
        self._lock_key_index: int | None = None
        self._ble_device: BLEDevice | None = None
        self._operation_lock = asyncio.Lock()
        self._runner: asyncio.Task | None = None  # type: ignore[type-arg]
        self._callbacks: list[Callable[[LockState], None]] = []
        self._update_task: asyncio.Task | None = None  # type: ignore[type-arg]

    @property
    def local_name(self) -> str:
        """Get the local name."""
        return self._local_name

    def register_callback(
        self, callback: Callable[[LockState], None]
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

    @property
    def name(self) -> str:
        """Get the name of the lock."""
        return self._local_name

    def _get_lock_instance(self) -> Lock:
        """Get the lock instance."""
        assert self._ble_device is not None  # nosec
        assert self._lock_key is not None  # nosec
        assert self._lock_key_index is not None  # nosec
        return Lock(self._ble_device, self._lock_key, self._lock_key_index)

    async def _cancel_any_update(self) -> None:
        """Cancel any update task."""
        await asyncio.sleep(0)
        if self._update_task:
            _LOGGER.debug("Canceling in progress update: %s", self._update_task)
            self._update_task.cancel()
            self._update_task = None

    @property
    def door_status(self) -> DoorStatus:
        """Return the current door status."""
        return self._lock_state.door if self._lock_state else DoorStatus.UNKNOWN

    @property
    def lock_status(self) -> LockStatus:
        """Return the current lock status."""
        return self._lock_state.lock if self._lock_state else LockStatus.UNKNOWN

    @operation_lock
    @retry_bluetooth_connection_error
    async def lock(self) -> None:
        """Lock the lock."""
        _LOGGER.debug("Starting lock")
        await self._cancel_any_update()
        self._callback_state(LockState(LockStatus.LOCKING, self.door_status))
        lock = self._get_lock_instance()
        try:
            await lock.connect()
            await lock.force_lock()
        except Exception:
            self._callback_state(LockState(LockStatus.UNKNOWN, self.door_status))
            raise
        finally:
            await lock.disconnect()
        self._callback_state(LockState(LockStatus.LOCKED, self.door_status))
        await self._cancel_any_update()
        _LOGGER.debug("Finished lock")

    @operation_lock
    @retry_bluetooth_connection_error
    async def unlock(self) -> None:
        """Unlock the lock."""
        _LOGGER.debug("Starting unlock")
        await self._cancel_any_update()
        self._callback_state(LockState(LockStatus.UNLOCKING, self.door_status))
        lock = self._get_lock_instance()
        try:
            await lock.connect()
            await lock.force_unlock()
        except Exception:
            self._callback_state(LockState(LockStatus.UNKNOWN, self.door_status))
            raise
        finally:
            await lock.disconnect()
        self._callback_state(LockState(LockStatus.UNLOCKED, self.door_status))
        await self._cancel_any_update()
        _LOGGER.debug("Finished unlock")

    @operation_lock
    @retry_bluetooth_connection_error
    async def update(self) -> LockState:
        """Update the lock state."""
        lock = self._get_lock_instance()
        try:
            await lock.connect()
            state = await lock.status()
        except asyncio.CancelledError:
            _LOGGER.debug(
                "%s: In-progress update canceled due to lock operation", self.name
            )
            raise
        finally:
            await lock.disconnect()
        _LOGGER.debug("%s: Updating lock state", self.name)
        self._callback_state(state)
        return state

    def _callback_state(self, lock_state: LockState) -> None:
        """Call the callbacks."""
        self._lock_state = lock_state
        _LOGGER.debug("%s: New lock state: %s", self.name, self._lock_state)
        for callback in self._callbacks:
            try:
                callback(lock_state)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("%s: Error calling callback", self.name)

    def update_advertisement(
        self, ble_device: BLEDevice, ad: AdvertisementData
    ) -> None:
        """Update the advertisement."""
        if ble_device.name != self._local_name:
            return
        _LOGGER.debug(
            "%s: Accepting new advertisement since local name does match: %s: %s",
            self.name,
            ble_device.name,
            ad,
        )
        self.set_ble_device(ble_device)
        has_update = False
        if (
            APPLE_MFR_ID in ad.manufacturer_data
            and ad.manufacturer_data[APPLE_MFR_ID][0] == HAP_FIRST_BYTE
        ):
            hk_state = get_homekit_state_num(ad.manufacturer_data[APPLE_MFR_ID])
            if hk_state != self._last_hk_state:
                # has_update = True
                self._last_hk_state = hk_state
        if YALE_MFR_ID in ad.manufacturer_data:
            current_value = ad.manufacturer_data[YALE_MFR_ID][0]
            if current_value != self._last_adv_value:
                has_update = True
                self._last_adv_value = current_value
        _LOGGER.debug(
            "%s: State: (current_state: %s) (hk_state: %s) "
            "(adv_value: %s) (has_update: %s)",
            self.name,
            self._lock_state,
            self._last_hk_state,
            self._last_adv_value,
            has_update,
        )
        if not self._update_queue.full() and has_update:
            self._update_queue.put_nowait(ble_device)

    async def start(self) -> Callable[[], None]:
        """Start watching for updates."""
        _LOGGER.debug("Waiting for advertisement callbacks for %s", self.name)
        if self._runner:
            raise RuntimeError("Already running")
        self._runner = asyncio.create_task(self._queue_watcher())

        def _cancel() -> None:
            self._update_queue.put_nowait(None)
            if self._runner:
                self._runner.cancel()
                self._runner = None

        return _cancel

    async def _queue_watcher(self) -> None:
        """Watch for updates."""
        while await self._update_queue.get():
            _LOGGER.debug("%s: Starting update", self.name)
            try:
                self._update_task = asyncio.create_task(self.update())
                await self._update_task
            except AuthError:
                _LOGGER.error(
                    "%s: Auth error, key or slot (key index) is incorrect", self.name
                )
            except asyncio.CancelledError:
                pass
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("%s: Error updating", self.name)


def get_homekit_state_num(data: bytes) -> int:
    """Get the homekit state number from the manufacturer data."""
    acid, gsn, cn, cv = struct.unpack("<HHBB", data[9:15])
    return gsn
