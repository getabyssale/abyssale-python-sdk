"""The retry truth table.

These are the rules ported from the Node SDK's `middleware.ts`; each one exists because getting it
wrong has a specific cost, spelled out in the docstrings there.
"""

from __future__ import annotations

import email.utils
import time

import httpx
import pytest

from abyssale._retry import (
    CEILING_PROBE_DELAY_SECONDS,
    attempts_for,
    is_retryable_for_method,
    plan_retry,
    read_error_id,
    retry_after_seconds,
    retry_schedule,
)


def response(status: int, body: object | None = None, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status, json=body if body is not None else {}, headers=headers)


class TestPlanRetry:
    @pytest.mark.parametrize("status", [500, 502, 503, 504])
    def test_server_errors_are_retryable(self, status: int) -> None:
        plan = plan_retry(response(status))
        assert plan is not None and plan.probe is False

    @pytest.mark.parametrize("status", [200, 201, 202, 400, 401, 403, 404, 409, 422, 501])
    def test_everything_else_is_not(self, status: int) -> None:
        assert plan_retry(response(status)) is None

    def test_429_with_retry_after_gets_the_full_ladder(self) -> None:
        plan = plan_retry(response(429, headers={"retry-after": "12"}))
        assert plan == (False, 12.0)

    def test_bare_429_gets_exactly_one_probe(self) -> None:
        plan = plan_retry(response(429, {"id": "rate_limit_exceeded"}), "rate_limit_exceeded")
        assert plan is not None
        assert plan.probe is True
        assert plan.delay == CEILING_PROBE_DELAY_SECONDS

    def test_feature_not_in_plan_is_never_retried(self) -> None:
        # Permanent for this key: the plan does not include the design type, so a probe is
        # a second's delay bought for nothing.
        assert plan_retry(response(429, {"id": "feature_not_in_plan"}), "feature_not_in_plan") is None

    def test_a_permanent_code_with_retry_after_is_still_believed(self) -> None:
        # It named a window, so it is a real throttle whatever the id says.
        plan = plan_retry(response(429, {"id": "feature_not_in_plan"}, {"retry-after": "5"}), "feature_not_in_plan")
        assert plan == (False, 5.0)


class TestRetryAfter:
    def test_delta_seconds(self) -> None:
        assert retry_after_seconds(response(429, headers={"retry-after": "30"})) == 30.0

    def test_http_date(self) -> None:
        at = email.utils.formatdate(time.time() + 60, usegmt=True)
        seconds = retry_after_seconds(response(429, headers={"retry-after": at}))
        assert seconds is not None and 50 < seconds <= 61

    def test_a_past_date_is_clamped_to_zero(self) -> None:
        at = email.utils.formatdate(time.time() - 120, usegmt=True)
        assert retry_after_seconds(response(429, headers={"retry-after": at})) == 0.0

    def test_absent_and_unparseable(self) -> None:
        assert retry_after_seconds(response(429)) is None
        assert retry_after_seconds(response(429, headers={"retry-after": "soon"})) is None


class TestMethodSensitivity:
    @pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS", "get"])
    def test_5xx_is_retried_on_reads(self, method: str) -> None:
        assert is_retryable_for_method(response(503), method) is True

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
    def test_5xx_is_not_retried_on_writes(self, method: str) -> None:
        # Every POST on this API bills credits. A 504 at the gateway does not mean the generation
        # did not happen, so repeating it can bill twice.
        assert is_retryable_for_method(response(504), method) is False

    def test_429_is_retried_on_writes(self) -> None:
        # A throttle means the request was refused, not processed — safe to repeat.
        assert is_retryable_for_method(response(429), "POST") is True


class TestAttemptsFor:
    def test_a_probe_is_one_attempt_whatever_max_retries_says(self) -> None:
        plan = plan_retry(response(429), None)
        assert plan is not None
        assert attempts_for(plan, 5) == 1

    def test_a_probe_is_still_capped_by_max_retries(self) -> None:
        # max_retries=0 means retries are off, and a probe is a retry.
        plan = plan_retry(response(429), None)
        assert plan is not None
        assert attempts_for(plan, 0) == 0


class TestRetrySchedule:
    def test_a_success_yields_no_delays(self) -> None:
        assert next(retry_schedule(response(200), "GET", 3), None) is None

    def test_a_write_5xx_yields_no_delays(self) -> None:
        assert next(retry_schedule(response(503), "POST", 3), None) is None

    def test_read_5xx_backs_off_exponentially(self) -> None:
        schedule = retry_schedule(response(503), "GET", 3)
        delays = []
        delay = next(schedule, None)
        while delay is not None:
            delays.append(delay)
            try:
                delay = schedule.send(response(503))
            except StopIteration:
                break
        assert len(delays) == 3
        assert 1.0 <= delays[0] < 1.1
        assert 2.0 <= delays[1] < 2.1
        assert 4.0 <= delays[2] < 4.1

    def test_a_recovered_response_stops_the_schedule(self) -> None:
        schedule = retry_schedule(response(503), "GET", 3)
        next(schedule)
        with pytest.raises(StopIteration):
            schedule.send(response(200))

    def test_retry_after_replaces_the_backoff(self) -> None:
        first = response(429, headers={"retry-after": "7"})
        schedule = retry_schedule(first, "POST", 3)
        assert next(schedule) == 7.0

    def test_the_bare_429_probe_runs_once_and_stops(self) -> None:
        schedule = retry_schedule(response(429, {"id": "rate_limit_exceeded"}), "POST", 3)
        assert next(schedule) == CEILING_PROBE_DELAY_SECONDS
        with pytest.raises(StopIteration):
            schedule.send(response(429, {"id": "rate_limit_exceeded"}))


class TestReadErrorId:
    def test_reads_the_envelope_id(self) -> None:
        assert read_error_id(response(429, {"id": "request_rate_limited"})) == "request_rate_limited"

    def test_tolerates_a_body_that_is_not_the_envelope(self) -> None:
        assert read_error_id(httpx.Response(502, text="<html>bad gateway</html>")) is None
        assert read_error_id(response(429, {"message": "no id here"})) is None
