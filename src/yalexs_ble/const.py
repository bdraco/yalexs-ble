from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict

COMMAND_SERVICE_UUID = "0000fe24-0000-1000-8000-00805f9b34fb"
WRITE_CHARACTERISTIC = "bd4ac611-0b45-11e3-8ffd-0800200c9a66"
READ_CHARACTERISTIC = "bd4ac612-0b45-11e3-8ffd-0800200c9a66"
SECURE_WRITE_CHARACTERISTIC = "bd4ac613-0b45-11e3-8ffd-0800200c9a66"
SECURE_READ_CHARACTERISTIC = "bd4ac614-0b45-11e3-8ffd-0800200c9a66"

APPLE_MFR_ID = 76
YALE_MFR_ID = 465
HAP_FIRST_BYTE = 0x06
HAP_ENCRYPTED_FIRST_BYTE = 0x11


MANUFACTURER_NAME_CHARACTERISTIC = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHARACTERISTIC = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHARACTERISTIC = "00002a25-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_CHARACTERISTIC = "00002a26-0000-1000-8000-00805f9b34fb"

NO_DOOR_SENSE_MODELS = ("ASL-02", "ASL-01")


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
class BatteryState:

    voltage: float
    percentage: int


@dataclass
class LockState:

    lock: LockStatus
    door: DoorStatus
    battery: BatteryState | None


@dataclass
class LockInfo:

    manufacturer: str
    model: str
    serial: str
    firmware: str

    @property
    def door_sense(self) -> bool:
        """Check if the lock has door sense support."""
        return bool(
            self.model
            and not any(
                self.model.startswith(old_model) for old_model in NO_DOOR_SENSE_MODELS
            )
        )


@dataclass
class ConnectionInfo:

    rssi: int


class YaleXSBLEDiscovery(TypedDict):
    """A validated discovery of a Yale XS BLE device."""

    name: str
    address: str
    serial: str
    key: str
    slot: int
