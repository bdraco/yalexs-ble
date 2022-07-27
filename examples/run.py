import asyncio
import logging
import struct

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import BleakError

from yalexs_ble.const import LockState
from yalexs_ble.lock import Lock

_LOGGER = logging.getLogger(__name__)

LOCK_ADDRESS = None
LOCK_KEY = None
LOCK_KEY_INDEX = None

assert isinstance(LOCK_ADDRESS, str)  # nosec
assert isinstance(LOCK_KEY, str)  # type: ignore[unreachable] # nosec
assert isinstance(LOCK_KEY_INDEX, int)  # nosec


def get_homekit_state_num(data: bytes) -> int:
    """Get the homekit state number from the manufacturer data."""
    acid, gsn, cn, cv = struct.unpack("<HHBB", data[9:15])
    return gsn


async def run():
    scanner = BleakScanner()
    lock_state: LockState | None = None
    update_queue = asyncio.Queue(1)
    last_adv_value = -1
    last_hk_state = -1

    def _found(d: BLEDevice, ad: AdvertisementData):
        nonlocal lock_state
        nonlocal last_adv_value
        nonlocal last_hk_state
        if d.address == LOCK_ADDRESS:
            has_update = False
            if 76 in ad.manufacturer_data and ad.manufacturer_data[76][0] == 0x06:
                hk_state = get_homekit_state_num(ad.manufacturer_data[76])
                if hk_state != last_hk_state:
                    # has_update = True
                    last_hk_state = hk_state
            if 465 in ad.manufacturer_data:
                current_value = ad.manufacturer_data[465][0]
                if current_value != last_adv_value:
                    has_update = True
                    last_adv_value = current_value
            _LOGGER.debug(
                "State: (current_state: %s) (hk_state: %s) "
                "(adv_value: %s) (has_update: %s)",
                lock_state,
                last_hk_state,
                last_adv_value,
                has_update,
            )
            if not update_queue.full() and has_update:
                update_queue.put_nowait(d)

    scanner.register_detection_callback(_found)
    await scanner.start()

    while True:
        d = await update_queue.get()
        lock = Lock(d, LOCK_KEY, LOCK_KEY_INDEX)
        for _ in range(3):
            try:
                await lock.connect()
                lock_state = await lock.status()
                _LOGGER.info("New lock state: %s", lock_state)
                await lock.disconnect()
                break
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout")
            except ValueError as e:
                _LOGGER.warning("Encryption error: %s", e)
            except BleakError as e:
                _LOGGER.warning("Bleak error: %s", e)
            except Exception as e:
                _LOGGER.exception("Failed: %s", e)


logging.basicConfig(level=logging.INFO)
logging.getLogger("yalexs_ble").setLevel(logging.DEBUG)
asyncio.run(run())
