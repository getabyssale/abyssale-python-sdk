"""The polling helpers: the schedule, the transient-failure budget, and what counts as done."""

from __future__ import annotations

import math

import httpx
import pytest
import respx

from abyssale import Abyssale, AbyssalePollingError, AsyncAbyssale
from abyssale._polling import (
    POLL_MIN_INTERVAL_SECONDS,
    POLL_MIN_MAX_INTERVAL_SECONDS,
    POLL_MIN_TIMEOUT_SECONDS,
    resolve_poll_options,
)

from .conftest import BASE_URL, error_body

REQUEST_ID = "b0a1c2d3-e4f5-4678-9abc-def012345678"
BANNER = {"id": "8d0f1e2b-3c4d-4e5f-8a9b-0c1d2e3f4a5b", "name": "b", "file": {"url": "https://cdn/x.png"}}


def status(*, finalized: bool, banners: list[dict] | None = None, errors: list[dict] | None = None) -> dict:
    body: dict = {"id": REQUEST_ID, "is_finalized": finalized, "banners": banners or []}
    if errors is not None:
        body["errors"] = errors
    return body


class TestOptions:
    def test_defaults(self) -> None:
        options = resolve_poll_options()
        assert (options.interval, options.max_interval, options.timeout) == (3.0, 30.0, 1800.0)

    def test_the_floors_cannot_be_undercut(self) -> None:
        # A caller who asks to poll every 100ms gets the floor, not their number: the status route
        # is rate-limited, and a tight loop spends the workspace's budget for nothing.
        options = resolve_poll_options(interval=0.1, max_interval=0.1, timeout=1)
        assert (options.interval, options.max_interval, options.timeout) == (
            POLL_MIN_INTERVAL_SECONDS,
            POLL_MIN_MAX_INTERVAL_SECONDS,
            POLL_MIN_TIMEOUT_SECONDS,
        )


class TestWaitForGenerationRequest:
    def test_it_polls_until_finalized(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(202, json=status(finalized=False)),
                httpx.Response(202, json=status(finalized=False)),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        result = client.wait_for_generation_request(REQUEST_ID)
        assert result.is_finalized is True
        assert len(result.banners) == 1
        assert route.call_count == 3

    def test_partial_success_resolves(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # One format failing does not invalidate the others — the caller checks `errors`.
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(
                200,
                json=status(
                    finalized=True,
                    banners=[BANNER],
                    errors=[{"template_format_name": "instagram-post", "reason": "missing asset"}],
                ),
            )
        )
        result = client.wait_for_generation_request(REQUEST_ID)
        assert result.banners and result.errors

    def test_finalized_with_no_banners_at_all_raises(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(
                200,
                json=status(
                    finalized=True, errors=[{"template_format_name": "facebook-feed", "reason": "render failed"}]
                ),
            )
        )
        with pytest.raises(AbyssalePollingError) as caught:
            client.wait_for_generation_request(REQUEST_ID)
        assert "facebook-feed: render failed" in str(caught.value)
        # The finalized status object is reachable for callers who want to read `errors` themselves.
        assert caught.value.__cause__ is not None

    def test_a_verdict_fails_on_the_first_poll(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # A 404 says the request does not exist; re-asking for 30 minutes will not change that.
        route = respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(404, json=error_body("generation_request_not_found"))
        )
        with pytest.raises(AbyssalePollingError) as caught:
            client.wait_for_generation_request(REQUEST_ID)
        assert caught.value.id == "generation_request_not_found"
        assert route.call_count == 1

    def test_transient_failures_are_absorbed(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        assert client.wait_for_generation_request(REQUEST_ID).is_finalized

    def test_too_many_consecutive_failures_give_up(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(return_value=httpx.Response(503))
        with pytest.raises(AbyssalePollingError):
            client.wait_for_generation_request(REQUEST_ID)

    def test_the_failure_streak_resets_on_success(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # Three failures, a success, then three more: nine polls in total, none of them fatal,
        # because the budget is consecutive failures and not failures overall.
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(202, json=status(finalized=False)),
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        assert client.wait_for_generation_request(REQUEST_ID).is_finalized

    def test_only_one_bare_429_is_absorbed_for_the_whole_poll(
        self, client: Abyssale, respx_mock: respx.MockRouter
    ) -> None:
        # The first bare 429 might be the gateway's per-second ceiling. A second one, after the
        # probe already cleared, answers that: it is not the ceiling, so waiting is not the fix.
        route = respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(429, json=error_body("rate_limit_exceeded"))
        )
        with pytest.raises(AbyssalePollingError) as caught:
            client.wait_for_generation_request(REQUEST_ID)
        assert caught.value.id == "rate_limit_exceeded"
        # One probe inside the request loop, then the poll's own single absorption.
        assert route.call_count <= 4

    def test_a_cool_off_past_the_wait_budget_ends_the_poll(self, respx_mock: respx.MockRouter) -> None:
        """The deadline bounds the whole wait, not one silence inside it.

        A 30-minute poll has room to sleep off a 28-minute `Retry-After` in a single go, which is
        exactly what `max_retry_wait` exists to refuse — so the poll ends here rather than going
        quiet for the rest of its budget.
        """
        route = respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(429, json=error_body("request_rate_limited"), headers={"retry-after": "1659"})
        )
        with Abyssale(api_key="k", base_url=BASE_URL, max_retry_wait=30.0) as client:
            with pytest.raises(AbyssalePollingError) as caught:
                client.wait_for_generation_request(REQUEST_ID)
        assert caught.value.id == "request_rate_limited"
        assert route.call_count == 1

    def test_a_cool_off_inside_the_wait_budget_is_still_absorbed(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(429, json=error_body("request_rate_limited"), headers={"retry-after": "5"}),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        with Abyssale(api_key="k", base_url=BASE_URL, max_retry_wait=30.0) as client:
            assert client.wait_for_generation_request(REQUEST_ID).is_finalized

    def test_an_unbounded_client_still_waits_the_cool_off_out(self, respx_mock: respx.MockRouter) -> None:
        # `math.inf` is the opt-out, and a batch job that passes it gets the old behaviour back.
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(429, json=error_body("request_rate_limited"), headers={"retry-after": "600"}),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        with Abyssale(api_key="k", base_url=BASE_URL, max_retry_wait=math.inf) as client:
            assert client.wait_for_generation_request(REQUEST_ID).is_finalized

    def test_a_network_blip_is_transient(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.ConnectError("reset"),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        assert client.wait_for_generation_request(REQUEST_ID).is_finalized

    def test_it_gives_up_at_the_deadline(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(202, json=status(finalized=False))
        )
        # The floor is 60s and the backoff doubles from 3s, so this terminates in ~6 polls.
        with pytest.raises(AbyssalePollingError, match="may still complete"):
            client.wait_for_generation_request(REQUEST_ID, timeout=1)


class TestWaitForDuplicationRequest:
    def _body(self, state: str) -> dict:
        return {
            "request_id": REQUEST_ID,
            "status": state,
            "created_at_ts": 1749827734,
            "target_project": {"id": "p1", "name": "Project"},
            "designs": [],
        }

    @pytest.mark.parametrize("terminal", ["COMPLETED", "ERROR"])
    def test_both_terminal_states_resolve(self, client: Abyssale, respx_mock: respx.MockRouter, terminal: str) -> None:
        # ERROR is a result, not an exception: the caller reads `status`.
        respx_mock.get(f"{BASE_URL}/design-duplication-requests/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(200, json=self._body("IN_PROGRESS")),
                httpx.Response(200, json=self._body(terminal)),
            ]
        )
        result = client.wait_for_duplication_request(REQUEST_ID)
        assert str(getattr(result.status, "value", result.status)) == terminal


class TestAsyncPolling:
    async def test_it_polls_the_same_way(self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            side_effect=[
                httpx.Response(202, json=status(finalized=False)),
                httpx.Response(200, json=status(finalized=True, banners=[BANNER])),
            ]
        )
        result = await async_client.wait_for_generation_request(REQUEST_ID)
        assert result.is_finalized and route.call_count == 2

    async def test_a_verdict_still_fails_fast(self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/generation-request/{REQUEST_ID}").mock(
            return_value=httpx.Response(404, json=error_body("generation_request_not_found"))
        )
        with pytest.raises(AbyssalePollingError):
            await async_client.wait_for_generation_request(REQUEST_ID)


JOB_ID = "8f0c2a4e-4869-11f0-96f2-0a00d9eb8f78"
OUTPUT = {"type": "image", "url": "https://s3.example/out.webp", "mime_type": "image/webp"}


def asset_job(status: str, **extra: object) -> dict[str, object]:
    body: dict[str, object] = {
        "job_id": JOB_ID,
        "operation": "images_remove_background",
        "status": status,
        "outputs": [],
        "credits": {"generation_credits": 0, "ai_credits": 0},
        "error": None,
        "created_at": "2026-11-09T10:00:00Z",
        "finalized_at": None,
    }
    body.update(extra)
    return body


class TestWaitForAssetJob:
    def test_it_polls_until_completed_and_returns_the_job(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/asset-jobs/{JOB_ID}").mock(
            side_effect=[
                httpx.Response(200, json=asset_job("PENDING")),
                httpx.Response(200, json=asset_job("PROCESSING")),
                httpx.Response(200, json=asset_job("COMPLETED", outputs=[OUTPUT])),
            ]
        )
        job = client.wait_for_asset_job(JOB_ID)
        assert str(job.outputs[0].url) == OUTPUT["url"]
        assert route.call_count == 3

    def test_a_failed_job_raises_naming_its_code(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        failed = asset_job(
            "FAILED", error={"code": "invalid_input_asset", "message": "The image was not found (HTTP 404)."}
        )
        route = respx_mock.get(f"{BASE_URL}/asset-jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=failed))
        with pytest.raises(AbyssalePollingError, match="invalid_input_asset") as caught:
            client.wait_for_asset_job(JOB_ID)
        # `id` is reserved for an API error body — the poll itself answered 200.
        assert caught.value.id is None
        cause = caught.value.__cause__
        assert cause is not None
        assert str(getattr(cause.args[0].status, "value", cause.args[0].status)) == "FAILED"
        assert route.call_count == 1

    def test_an_unknown_job_fails_on_the_first_poll(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/asset-jobs/{JOB_ID}").mock(
            return_value=httpx.Response(404, json=error_body("asset_job_not_found"))
        )
        with pytest.raises(AbyssalePollingError) as caught:
            client.wait_for_asset_job(JOB_ID)
        assert caught.value.id == "asset_job_not_found"
        assert route.call_count == 1

    async def test_the_async_client_waits_the_same_way(
        self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter
    ) -> None:
        respx_mock.get(f"{BASE_URL}/asset-jobs/{JOB_ID}").mock(
            side_effect=[
                httpx.Response(200, json=asset_job("PROCESSING")),
                httpx.Response(200, json=asset_job("FAILED", error={"code": "invalid_input", "message": "refused"})),
            ]
        )
        with pytest.raises(AbyssalePollingError, match="invalid_input"):
            await async_client.wait_for_asset_job(JOB_ID)
