import asyncio

import pytest

from yalexs_ble.push import (
    PushLock,
    cancelable_operation,
    operation_lock,
    retry_bluetooth_connection_error,
)


@pytest.mark.asyncio
async def test_operation_lock():
    """Test the operation_lock function."""

    counter = 0

    class MockPushLock:
        def __init__(self):
            self._operation_lock = asyncio.Lock()

        @property
        def name(self):
            return "lock"

        @operation_lock
        async def do_something(self):
            nonlocal counter
            counter += 1
            await asyncio.sleep(1)
            counter -= 1

    lock = MockPushLock()
    tasks = []
    for _ in range(10):
        tasks.append(asyncio.create_task(lock.do_something()))

    for _ in range(10):
        await asyncio.sleep(0)
        assert counter == 1

    for task in tasks:
        task.cancel()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_operation_lock_with_retry_bluetooth_connection_error():
    """Test the operation_lock and retry_bluetooth_connection_error function."""

    counter = 0

    class MockPushLock:
        def __init__(self):
            self._operation_lock = asyncio.Lock()

        @property
        def name(self):
            return "lock"

        @retry_bluetooth_connection_error
        @operation_lock
        async def do_something(self):
            nonlocal counter
            counter += 1
            try:
                await asyncio.sleep(0.001)
                raise asyncio.TimeoutError()
            finally:
                counter -= 1

    lock = MockPushLock()
    tasks = []
    for _ in range(10):
        tasks.append(asyncio.create_task(lock.do_something()))

    for _ in range(10):
        await asyncio.sleep(0)
        assert counter == 1

    await asyncio.sleep(0.1)
    for _ in range(10):
        await asyncio.sleep(0)
        assert counter == 0

    for task in tasks:
        task.cancel()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_retry_bluetooth_connection_error_with_operation_lock():
    """Test the operation_lock and retry_bluetooth_connection_error function."""

    counter = 0

    class MockPushLock:
        def __init__(self):
            self._operation_lock = asyncio.Lock()

        @property
        def name(self):
            return "lock"

        @operation_lock
        @retry_bluetooth_connection_error
        async def do_something(self):
            nonlocal counter
            counter += 1
            try:
                await asyncio.sleep(0.001)
                raise asyncio.TimeoutError()
            finally:
                counter -= 1

    lock = MockPushLock()
    tasks = []
    for _ in range(10):
        tasks.append(asyncio.create_task(lock.do_something()))

    for _ in range(10):
        await asyncio.sleep(0)
        assert counter == 1

    await asyncio.sleep(0.1)
    for _ in range(10):
        await asyncio.sleep(0)
        assert counter == 0

    for task in tasks:
        task.cancel()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_operation_lock_with_cancelable_operation():
    """Test the operation_lock and rcancelable_operation function."""

    counter = 0

    class MockPushLock(PushLock):
        @property
        def name(self):
            return "lock"

        @cancelable_operation
        @operation_lock
        async def do_something(self):
            nonlocal counter
            await asyncio.sleep(0.05)
            counter += 1

    lock = MockPushLock("a")
    tasks = []
    for _ in range(10):
        tasks.append(asyncio.create_task(lock.do_something()))

    await asyncio.sleep(0.1)
    assert counter == 1
