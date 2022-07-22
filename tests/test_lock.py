from yalexs_ble.lock import Lock


def test_create_lock():
    Lock("1.2.3.4", "0800200c9a66", 1)
