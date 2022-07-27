import asyncio
import logging
import struct
from collections.abc import Callable
from typing import Any, TypeVar, cast

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import BleakError

from .const import LockState
from .lock import Lock
from .session import AuthError

_LOGGER = logging.getLogger(__name__)


WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

DEFAULT_ATTEMPTS = 3


def lock_connection(func: WrapFuncType) -> WrapFuncType:
    """Define a wrapper to connect and disconnect from the lock."""

    async def _async_wrap_lock_connection(
        self: "PushLock", *args: Any, **kwargs: Any
    ) -> None:
        _LOGGER.debug("%s: Starting operation: %s", self.name, func)

        self._lock = self._get_lock_instance()
        await self._lock.connect()
        try:
            return await func(self, *args, **kwargs)
        except Exception:
            raise
        finally:
            await self._lock.disconnect()
            self._lock = None

    return cast(WrapFuncType, _async_wrap_lock_connection)


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

        for attempt in range(DEFAULT_ATTEMPTS):
            try:
                return await func(self, *args, **kwargs)
            except asyncio.TimeoutError:
                _LOGGER.debug(
                    "%s: Timeout error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except ValueError:
                _LOGGER.debug(
                    "%s: Encryption error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except BleakError:
                _LOGGER.debug(
                    "%s: Bleak error calling %s, retrying...",
                    self.name,
                    func,
                    exc_info=True,
                )
            except AuthError:
                raise
            except Exception as e:
                _LOGGER.exception("%s: Failed: %s", self.name, e)

    return cast(WrapFuncType, _async_wrap_retry_bluetooth_connection_error)


class PushLock:
    """A lock with push updates."""

    def __init__(self, serial_number: str) -> None:
        """Init the lock watcher."""
        self._serial_number = serial_number
        # M1FBA011ZZ -> M1FBA011
        self._local_name = f"{serial_number[0:2]}{serial_number[-5:]}"
        self._lock_state: LockState | None = None
        self._update_queue: asyncio.Queue[BLEDevice] = asyncio.Queue(1)
        self._last_adv_value = -1
        self._last_hk_state = -1
        self._lock: Lock | None = None
        self._lock_key: str | None = None
        self._lock_key_index: int | None = None
        self._ble_device: BLEDevice | None = None
        self._operation_lock = asyncio.Lock()
        self._runner: asyncio.Task | None = None  # type: ignore[type-arg]
        self._callbacks: list[Callable[[LockState], None]] = []

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
        return self._ble_device.name if self._ble_device else "Unknown"

    def _get_lock_instance(self) -> Lock:
        """Get the lock instance."""
        assert self._ble_device is not None  # nosec
        assert self._lock_key is not None  # nosec
        assert self._lock_key_index is not None  # nosec
        return Lock(self._ble_device, self._lock_key, self._lock_key_index)

    @operation_lock
    @retry_bluetooth_connection_error
    @lock_connection
    async def lock(self) -> None:
        """Lock the lock."""
        assert self._lock is not None  # nosec
        await self._lock.force_lock()

    @operation_lock
    @retry_bluetooth_connection_error
    @lock_connection
    async def unlock(self) -> None:
        """Unlock the lock."""
        assert self._lock is not None  # nosec
        await self._lock.force_unlock()

    @operation_lock
    @retry_bluetooth_connection_error
    @lock_connection
    async def update(self) -> None:
        """Update the lock state."""
        assert self._lock is not None  # nosec
        _LOGGER.debug("%s: Updating lock state", self.name)
        self._lock_state = await self._lock.status()
        _LOGGER.info("%s: New lock state: %s", self.name, self._lock_state)

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
        if 76 in ad.manufacturer_data and ad.manufacturer_data[76][0] == 0x06:
            hk_state = get_homekit_state_num(ad.manufacturer_data[76])
            if hk_state != self._last_hk_state:
                # has_update = True
                self._last_hk_state = hk_state
        if 465 in ad.manufacturer_data:
            current_value = ad.manufacturer_data[465][0]
            if current_value != self._last_adv_value:
                has_update = True
                self._last_adv_value = current_value
        _LOGGER.debug(
            "State: (current_state: %s) (hk_state: %s) "
            "(adv_value: %s) (has_update: %s)",
            self._lock_state,
            self._last_hk_state,
            self._last_adv_value,
            has_update,
        )
        if not self._update_queue.full() and has_update:
            self._update_queue.put_nowait(ble_device)

    async def start(self) -> Callable[[], None]:
        """Start watching for updates."""
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
                await self.update()
            except AuthError:
                _LOGGER.error(
                    "%s: Auth error, key or slot (key index) is incorrect", self.name
                )


def get_homekit_state_num(data: bytes) -> int:
    """Get the homekit state number from the manufacturer data."""
    acid, gsn, cn, cv = struct.unpack("<HHBB", data[9:15])
    return gsn
