import pytest

from app.services.call_pacer import CallPacer


class _FakeTime:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_wait_turn_first_call_does_not_sleep() -> None:
    fake = _FakeTime()
    pacer = CallPacer(2.0, clock=fake.clock, sleep=fake.sleep)

    pacer.wait_turn()

    assert fake.sleeps == []


def test_wait_turn_sleeps_only_the_remaining_gap() -> None:
    fake = _FakeTime()
    pacer = CallPacer(2.0, clock=fake.clock, sleep=fake.sleep)
    pacer.wait_turn()
    fake.now += 0.5

    pacer.wait_turn()

    assert fake.sleeps == [pytest.approx(1.5)]


def test_wait_turn_with_zero_interval_never_sleeps() -> None:
    fake = _FakeTime()
    pacer = CallPacer(0.0, clock=fake.clock, sleep=fake.sleep)

    pacer.wait_turn()
    pacer.wait_turn()

    assert fake.sleeps == []


def test_call_pacer_with_negative_interval_raises() -> None:
    fake = _FakeTime()

    with pytest.raises(ValueError, match="negative"):
        CallPacer(-1.0, clock=fake.clock, sleep=fake.sleep)
