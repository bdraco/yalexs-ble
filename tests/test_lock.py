from bleak_retry_connector import BLEDevice

from yalexs_ble.lock import Lock


def test_create_lock():
    Lock(BLEDevice("aa:bb:cc:dd:ee:ff", "lock"), "0800200c9a66", 1)
