from dataclasses import dataclass
from enum import Enum

COMMAND_SERVICE_UUID = "0000fe24-0000-1000-8000-00805f9b34fb"
WRITE_CHARACTERISTIC = "bd4ac611-0b45-11e3-8ffd-0800200c9a66"
READ_CHARACTERISTIC = "bd4ac612-0b45-11e3-8ffd-0800200c9a66"
SECURE_WRITE_CHARACTERISTIC = "bd4ac613-0b45-11e3-8ffd-0800200c9a66"
SECURE_READ_CHARACTERISTIC = "bd4ac614-0b45-11e3-8ffd-0800200c9a66"

APPLE_MFR_ID = 76
YALE_MFR_ID = 465
HAP_FIRST_BYTE = 0x06


MANUFACTURER_NAME_CHARACTERISTIC = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHARACTERISTIC = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHARACTERISTIC = "00002a25-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_CHARACTERISTIC = "00002a26-0000-1000-8000-00805f9b34fb"


class Commands(Enum):

    UNLOCK = 0x0A
    LOCK = 0x0B


class LockStatus(Enum):

    UNKNOWN = 0x00
    UNKNOWN_01 = 0x01
    UNLOCKING = 0x02
    UNLOCKED = 0x03
    LOCKING = 0x04
    LOCKED = 0x05
    UNKNOWN_06 = 0x06


VALUE_TO_LOCK_STATUS = {status.value: status for status in LockStatus}


class DoorStatus(Enum):

    UNKNOWN = 0x00
    CLOSED = 0x01
    UNKNOWN_02 = 0x02
    OPENED = 0x03
    UNKNOWN_04 = 0x04


VALUE_TO_DOOR_STATUS = {status.value: status for status in DoorStatus}


@dataclass
class LockState:

    lock: LockStatus
    door: DoorStatus


@dataclass
class LockInfo:

    manufacturer: str
    model: str
    serial: str
    firmware: str


@dataclass
class ConnectionInfo:

    rssi: int
