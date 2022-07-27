import asyncio
import logging

from bleak import BleakScanner

from yalexs_ble import LockState, PushLock

_LOGGER = logging.getLogger(__name__)

LOCK_SERIAL = None
LOCK_KEY = None
LOCK_KEY_INDEX = None


assert isinstance(LOCK_SERIAL, str)  # nosec
assert isinstance(LOCK_KEY, str)  # type: ignore[unreachable] # nosec
assert isinstance(LOCK_KEY_INDEX, int)  # nosec


async def run():
    push_lock = PushLock(LOCK_SERIAL)
    push_lock.set_lock_key(LOCK_KEY, LOCK_KEY_INDEX)
    _LOGGER.info("Expected local_name: %s", push_lock.local_name)

    scanner = BleakScanner()

    def new_state(new_state: LockState) -> None:
        _LOGGER.info("New state: %s", new_state)

    cancel = push_lock.register_callback(new_state)
    scanner.register_detection_callback(push_lock.update_advertisement)
    await scanner.start()
    await push_lock.start()
    _LOGGER.info(
        "Started, waiting for lock to be discovered with local_name: %s",
        push_lock.local_name,
    )
    await asyncio.sleep(1000000)
    cancel()


logging.basicConfig(level=logging.INFO)
logging.getLogger("yalexs_ble").setLevel(logging.DEBUG)
asyncio.run(run())
