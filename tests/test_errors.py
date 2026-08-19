"""The error envelope → exception mapping.

The API answers with exactly one body shape — ``{id, message, errors?}`` — at every status on every
endpoint, so this mapping is the only place that reads a response body for its meaning.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from abyssale import (
    Abyssale,
    AbyssaleAPIError,
    AbyssaleAuthError,
    AbyssaleConnectionError,
    AbyssaleNotFoundError,
    AbyssaleRateLimitError,
)
from abyssale._transport import validate

from .conftest import BASE_URL, error_body


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (400, AbyssaleAPIError),
            (401, AbyssaleAuthError),
            (403, AbyssaleAuthError),
            (404, AbyssaleNotFoundError),
            (429, AbyssaleRateLimitError),
            (500, AbyssaleAPIError),
        ],
    )
    def test_each_status_raises_its_class(
        self, client: Abyssale, respx_mock: respx.MockRouter, status: int, expected: type[AbyssaleAPIError]
    ) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(
            return_value=httpx.Response(status, json=error_body("some_code", "it went wrong"))
        )
        with pytest.raises(expected) as caught:
            client.list_fonts()
        assert caught.value.status == status
        assert caught.value.id == "some_code"
        assert caught.value.message == "it went wrong"

    def test_every_subclass_is_catchable_as_the_base(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(404, json=error_body("design_not_found")))
        with pytest.raises(AbyssaleAPIError):
            client.list_fonts()


class TestEnvelope:
    def test_field_problems_are_exposed_as_a_list(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        problems = [{"path": "formats[0].width", "code": "out_of_range", "message": "too wide"}]
        respx_mock.post(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(400, json=error_body("invalid_payload", "bad body", problems))
        )
        with pytest.raises(AbyssaleAPIError) as caught:
            client.create_project({})
        assert caught.value.errors == problems

    def test_errors_is_none_when_the_failure_is_not_field_scoped(
        self, client: Abyssale, respx_mock: respx.MockRouter
    ) -> None:
        # `feature_not_in_plan` is a plan problem, not a payload problem, and carries no `errors`.
        respx_mock.post(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(429, json=error_body("feature_not_in_plan"))
        )
        with pytest.raises(AbyssaleRateLimitError) as caught:
            client.create_project({})
        assert caught.value.errors is None

    def test_a_bodyless_error_still_raises_something_readable(
        self, client: Abyssale, respx_mock: respx.MockRouter
    ) -> None:
        # The edge always sends a body; something in front of it might not.
        respx_mock.get(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(502))
        with pytest.raises(AbyssaleAPIError) as caught:
            client.list_fonts()
        assert caught.value.id is None
        assert "502" in str(caught.value)

    def test_a_non_json_error_body_is_kept_as_the_message(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(504, text="<html>gateway timeout</html>"))
        with pytest.raises(AbyssaleAPIError) as caught:
            client.list_fonts()
        assert "gateway timeout" in caught.value.message

    def test_retry_after_reaches_the_exception(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(
            return_value=httpx.Response(429, json=error_body("request_rate_limited"), headers={"retry-after": "30"})
        )
        with pytest.raises(AbyssaleRateLimitError) as caught:
            client.list_fonts()
        assert caught.value.retry_after == 30.0

    def test_rate_limit_headers_are_reachable(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(
            return_value=httpx.Response(
                429, json=error_body("request_rate_limited"), headers={"x-ratelimit-remaining": "0"}
            )
        )
        with pytest.raises(AbyssaleRateLimitError) as caught:
            client.list_fonts()
        assert caught.value.response.headers["x-ratelimit-remaining"] == "0"


class TestTransport:
    def test_a_network_failure_is_not_an_api_error(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(side_effect=httpx.ConnectError("no route to host"))
        with pytest.raises(AbyssaleConnectionError):
            client.list_fonts()

    def test_a_timeout_is_a_connection_error(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.get(f"{BASE_URL}/fonts").mock(side_effect=httpx.ReadTimeout("too slow"))
        with pytest.raises(AbyssaleConnectionError):
            client.list_fonts()


class TestResponseTolerance:
    """A 200 the API sent must reach the caller, whatever the published spec claims."""

    def test_a_missing_required_field_does_not_raise(self) -> None:
        from abyssale.models import DesignDetail

        design = validate(DesignDetail, {"id": "not-even-a-uuid", "name": "Half a design"})
        assert design.name == "Half a design"
        # The field the spec calls required is simply absent, not defaulted to a lie.
        assert getattr(design, "created_at", None) is None

    def test_an_unknown_field_is_kept(self) -> None:
        from abyssale.models import AuthResult

        result = validate(AuthResult, {"company": "acme", "something_new": True})
        assert result.company == "acme"
        assert result.something_new is True  # type: ignore[attr-defined]

    def test_a_nested_failure_stays_local(self) -> None:
        """One bad element must not turn the whole response into raw dicts.

        Reproduces the real case: `GET /designs/{id}?i=advanced` returns `group` layers with no
        `attributes`, which the spec marks required. Everything else must stay typed — otherwise
        `design.formats[0].id` silently becomes a KeyError on a dict, and which shape you get
        depends on the data.
        """
        from abyssale.models import DesignDetail, DesignElement, DesignFormat

        design = validate(
            DesignDetail,
            {
                "id": "64238d01-d402-474b-8c2d-fbc957e9d290",
                "name": "Has a group layer",
                "type": "static",
                "created_at": 1649942114,
                "updated_at": 1649942114,
                "project_id": "8f14e45f-ceea-467a-9a1b-1e0b0e0e0e0e",
                "formats": [
                    {"id": "300x250", "uid": "9b57d65e-eb2c-4a74-a51e-4482917c248a", "width": 300, "height": 250}
                ],
                "elements": [
                    {"name": "title", "type": "text", "attributes": {}},
                    # A group layer: no `attributes`, exactly as the API sends it.
                    {"name": "group-frame-4", "type": "group", "layer_ids": ["a", "b"]},
                ],
            },
        )

        assert isinstance(design.formats[0], DesignFormat)
        assert design.formats[0].id == "300x250"
        assert all(isinstance(e, DesignElement) for e in design.elements)
        assert design.elements[1].name == "group-frame-4"
        assert getattr(design.elements[1], "attributes", None) is None

    def test_unknown_fields_survive_the_fallback(self) -> None:
        from abyssale.models import DesignDetail

        design = validate(DesignDetail, {"id": "x", "invented_next_quarter": 42})
        assert design.invented_next_quarter == 42  # type: ignore[attr-defined]
