"""Requests the client builds, and what it does with the answers."""

from __future__ import annotations

import math

import httpx
import pytest
import respx

from abyssale import Abyssale, AsyncAbyssale
from abyssale._config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RETRY_WAIT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
)
from abyssale._errors import AbyssaleConfigError

from .conftest import API_KEY, BASE_URL, error_body

DESIGN_ID = "64238d01-d402-474b-8c2d-fbc957e9d290"

DESIGN = {
    "id": DESIGN_ID,
    "name": "Ad campaign",
    "type": "static",
    "created_at": 1649942114,
    "updated_at": 1649942114,
    "project_id": "8f14e45f-ceea-467a-9a1b-1e0b0e0e0e0e",
}


class TestConfig:
    def test_env_supplies_the_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ABYSSALE_API_KEY", "from-env")
        assert Abyssale()._api_key == "from-env"

    def test_an_argument_beats_the_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ABYSSALE_API_KEY", "from-env")
        assert Abyssale(api_key="explicit")._api_key == "explicit"

    def test_no_key_anywhere_is_a_config_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ABYSSALE_API_KEY", raising=False)
        with pytest.raises(AbyssaleConfigError, match="ABYSSALE_API_KEY"):
            Abyssale()

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ABYSSALE_BASE_URL", raising=False)
        monkeypatch.delenv("ABYSSALE_TIMEOUT_MS", raising=False)
        monkeypatch.delenv("ABYSSALE_MAX_RETRIES", raising=False)
        monkeypatch.delenv("ABYSSALE_MAX_RETRY_WAIT_MS", raising=False)
        client = Abyssale(api_key=API_KEY)
        assert client.base_url == DEFAULT_BASE_URL
        assert client.timeout == DEFAULT_TIMEOUT_SECONDS
        assert client.max_retries == DEFAULT_MAX_RETRIES
        assert client.max_retry_wait == DEFAULT_MAX_RETRY_WAIT_SECONDS

    def test_the_timeout_env_var_is_milliseconds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ABYSSALE_TIMEOUT_MS", "5000")
        assert Abyssale(api_key=API_KEY).timeout == 5.0

    def test_the_max_retry_wait_env_var_is_milliseconds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ABYSSALE_MAX_RETRY_WAIT_MS", "5000")
        assert Abyssale(api_key=API_KEY).max_retry_wait == 5.0

    def test_the_wait_cap_can_be_disabled(self) -> None:
        assert Abyssale(api_key=API_KEY, max_retry_wait=math.inf).max_retry_wait == math.inf

    @pytest.mark.parametrize(
        ("var", "value"),
        [
            ("ABYSSALE_TIMEOUT_MS", "-1"),
            ("ABYSSALE_TIMEOUT_MS", "abc"),
            ("ABYSSALE_MAX_RETRIES", "-2"),
            ("ABYSSALE_MAX_RETRY_WAIT_MS", "-1"),
            ("ABYSSALE_MAX_RETRY_WAIT_MS", "abc"),
        ],
    )
    def test_invalid_settings_are_rejected(self, monkeypatch: pytest.MonkeyPatch, var: str, value: str) -> None:
        monkeypatch.setenv(var, value)
        with pytest.raises(AbyssaleConfigError, match=var):
            Abyssale(api_key=API_KEY)


class TestRequests:
    def test_every_request_carries_the_api_key(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(200, json=[]))
        client.list_fonts()
        assert route.calls.last.request.headers["x-api-key"] == API_KEY
        assert route.calls.last.request.headers["user-agent"].startswith("abyssale-python/")

    def test_advanced_becomes_the_i_query_param(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/designs/{DESIGN_ID}").mock(return_value=httpx.Response(200, json=DESIGN))
        client.get_design(DESIGN_ID, advanced=True)
        assert route.calls.last.request.url.params["i"] == "advanced"

    def test_the_plain_read_sends_no_query_at_all(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/designs/{DESIGN_ID}").mock(return_value=httpx.Response(200, json=DESIGN))
        client.get_design(DESIGN_ID)
        assert not route.calls.last.request.url.params

    def test_unset_filters_are_dropped(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/designs").mock(return_value=httpx.Response(200, json=[]))
        client.list_designs(type="static")
        params = route.calls.last.request.url.params
        assert dict(params) == {"type": "static"}

    def test_path_arguments_are_encoded(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # A format specifier can be a human-authored name, spaces and all.
        route = respx_mock.get(url__regex=rf"{BASE_URL}/designs/{DESIGN_ID}/formats/.*").mock(
            return_value=httpx.Response(200, json={"id": DESIGN_ID, "name": "x", "width": 1, "height": 1})
        )
        client.get_design_format(DESIGN_ID, "summer sale/2026")
        assert "summer%20sale%2F2026" in str(route.calls.last.request.url)

    def test_a_post_sends_the_body_verbatim(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # Element payloads are passed through untouched: the API accepts unknown layer names by
        # design, so the SDK must not filter or coerce them.
        route = respx_mock.post(f"{BASE_URL}/banner-builder/{DESIGN_ID}/generate").mock(
            return_value=httpx.Response(200, json={"id": DESIGN_ID, "name": "b", "file": {"url": "https://x/y.png"}})
        )
        body = {"elements": {"not_a_real_layer": {"payload": "Hello"}}, "template_format_name": "fb"}
        client.generate_image(DESIGN_ID, body)
        import json as _json

        assert _json.loads(route.calls.last.request.content) == body


class TestResponses:
    def test_a_list_response_becomes_models(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/designs").mock(
            return_value=httpx.Response(200, json=[{**DESIGN, "preview_url": "https://cdn/preview.png"}])
        )
        designs = client.list_designs()
        assert len(designs) == 1
        assert designs[0].name == "Ad campaign"
        assert str(designs[0].preview_url) == "https://cdn/preview.png"

    def test_unknown_fields_do_not_raise(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        # The API ships ahead of the published spec; a field this SDK has never heard of must parse.
        respx_mock.get(f"{BASE_URL}/designs/{DESIGN_ID}").mock(
            return_value=httpx.Response(200, json={**DESIGN, "a_field_invented_next_quarter": 42})
        )
        design = client.get_design(DESIGN_ID)
        assert design.a_field_invented_next_quarter == 42  # type: ignore[attr-defined]

    def test_the_multipage_read_carries_pages_not_formats(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/designs/{DESIGN_ID}").mock(
            return_value=httpx.Response(
                200,
                json={**DESIGN, "type": "printer_multipage", "pages": [], "elements_per_page": {"page_1": []}},
            )
        )
        design = client.get_design(DESIGN_ID)
        assert design.formats is None
        assert design.elements_per_page == {"page_1": []}


class TestRetryIntegration:
    def test_a_read_5xx_is_retried_until_it_succeeds(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/fonts").mock(
            side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, json=[])]
        )
        assert client.list_fonts() == []
        assert route.call_count == 3

    def test_a_write_5xx_is_not_retried(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        from abyssale import AbyssaleAPIError

        route = respx_mock.post(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(504, json=error_body("api_error"))
        )
        with pytest.raises(AbyssaleAPIError):
            client.create_project({"name": "x"})
        assert route.call_count == 1

    def test_feature_not_in_plan_is_answered_immediately(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        from abyssale import AbyssaleRateLimitError

        route = respx_mock.post(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(429, json=error_body("feature_not_in_plan"))
        )
        with pytest.raises(AbyssaleRateLimitError) as caught:
            client.create_project({"name": "x"})
        assert caught.value.id == "feature_not_in_plan"
        assert route.call_count == 1  # not even the probe

    def test_a_bare_429_gets_exactly_one_probe(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.post(f"{BASE_URL}/projects").mock(
            side_effect=[
                httpx.Response(429, json=error_body("rate_limit_exceeded")),
                httpx.Response(200, json={"id": "p1", "name": "x"}),
            ]
        )
        client.create_project({"name": "x"})
        assert route.call_count == 2

    def test_a_cool_off_longer_than_the_budget_fails_immediately(self, respx_mock: respx.MockRouter) -> None:
        """The quota-spent case: the server asks for 28 minutes, the caller agreed to 30 seconds.

        Answering now with `retry_after` intact hands the decision back rather than making it for
        them — the whole call would otherwise block for up to `max_retries` times that window.
        """
        from abyssale import AbyssaleRateLimitError

        route = respx_mock.get(f"{BASE_URL}/fonts").mock(
            return_value=httpx.Response(429, json=error_body("rate_limit_exceeded"), headers={"retry-after": "1659"})
        )
        with Abyssale(api_key=API_KEY, base_url=BASE_URL, max_retry_wait=30.0) as client:
            with pytest.raises(AbyssaleRateLimitError) as caught:
                client.list_fonts()
        assert route.call_count == 1
        assert caught.value.retry_after == 1659.0  # the server's figure survives, to act on

    def test_a_cool_off_inside_the_budget_is_still_waited_out(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        slept: list[float] = []
        monkeypatch.setattr("abyssale._client.time.sleep", slept.append)
        route = respx_mock.get(f"{BASE_URL}/fonts").mock(
            side_effect=[
                httpx.Response(429, json=error_body("request_rate_limited"), headers={"retry-after": "4"}),
                httpx.Response(200, json=[]),
            ]
        )
        with Abyssale(api_key=API_KEY, base_url=BASE_URL, max_retry_wait=30.0) as client:
            assert client.list_fonts() == []
        assert route.call_count == 2
        assert slept == [4.0]

    def test_max_retries_zero_disables_the_probe(self, respx_mock: respx.MockRouter) -> None:
        from abyssale import AbyssaleRateLimitError

        route = respx_mock.get(f"{BASE_URL}/fonts").mock(
            return_value=httpx.Response(429, json=error_body("rate_limit_exceeded"))
        )
        with Abyssale(api_key=API_KEY, base_url=BASE_URL, max_retries=0) as client:
            with pytest.raises(AbyssaleRateLimitError):
                client.list_fonts()
        assert route.call_count == 1


class TestAsyncClient:
    async def test_it_sends_the_same_request(self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/designs/{DESIGN_ID}").mock(return_value=httpx.Response(200, json=DESIGN))
        design = await async_client.get_design(DESIGN_ID, advanced=True)
        assert design.name == "Ad campaign"
        assert route.calls.last.request.url.params["i"] == "advanced"
        assert route.calls.last.request.headers["x-api-key"] == API_KEY

    async def test_it_retries_the_same_way(self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/fonts").mock(
            side_effect=[httpx.Response(502), httpx.Response(200, json=[])]
        )
        assert await async_client.list_fonts() == []
        assert route.call_count == 2
