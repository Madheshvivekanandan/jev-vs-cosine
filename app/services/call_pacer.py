"""Spaces out Jev calls to stay inside free-tier rate limits."""

from collections.abc import Callable


class CallPacer:
    """Sleeps just long enough that consecutive calls are at least an interval apart."""

    def __init__(
        self,
        min_interval_seconds: float,
        *,
        clock: Callable[[], float],
        sleep: Callable[[float], None],
    ) -> None:
        """Configure the pacer.

        Args:
            min_interval_seconds: Minimum gap between call starts; 0 disables pacing.
            clock: Monotonic time source in seconds.
            sleep: Function that blocks for the given number of seconds.
        """
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must not be negative")
        self._min_interval_seconds = min_interval_seconds
        self._clock = clock
        self._sleep = sleep
        self._last_call_started: float | None = None

    def wait_turn(self) -> None:
        """Block until the next call is allowed, then mark it as started."""
        now = self._clock()
        if self._last_call_started is not None:
            wait_seconds = self._last_call_started + self._min_interval_seconds - now
            if wait_seconds > 0:
                self._sleep(wait_seconds)
                now = self._clock()
        self._last_call_started = now
