"""The three ``/signing-secret`` endpoints.

``force`` is the only query parameter on this surface and it exists to override a ``409``, so what
matters is that it reaches the wire when asked for and is **absent** otherwise: an explicit
``force=false`` in a server log reads as an override the caller never requested.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from abyssale import Abyssale, AbyssaleAPIError, AsyncAbyssale

from .conftest import API_KEY, BASE_URL

SECRET = {"secret": "whsec_" + "a" * 64, "created_at_ts": 1755561234, "rotated_at_ts": None}


class TestGetSigningSecret:
    def test_it_reads_the_secret(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.get(f"{BASE_URL}/signing-secret").mock(return_value=httpx.Response(200, json=SECRET))

        result = client.get_signing_secret()

        assert result.secret == SECRET["secret"]
        assert not route.calls.last.request.url.params


class TestRotateSigningSecret:
    def test_an_ordinary_rotate_sends_no_query_at_all(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(return_value=httpx.Response(200, json=SECRET))

        client.rotate_signing_secret()

        assert not route.calls.last.request.url.params

    def test_force_reaches_the_wire(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(return_value=httpx.Response(200, json=SECRET))

        client.rotate_signing_secret(force=True)

        assert route.calls.last.request.url.params["force"] == "true"

    def test_force_false_is_omitted_rather_than_sent(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(return_value=httpx.Response(200, json=SECRET))

        client.rotate_signing_secret(force=False)

        assert not route.calls.last.request.url.params

    def test_a_refused_second_rotate_raises_with_the_machine_readable_id(
        self, client: Abyssale, respx_mock: respx.MockRouter
    ) -> None:
        """Rotating twice inside the 24-hour window is a 409, and the caller has to be able to
        branch on it — the message is prose and will change."""
        respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(
            return_value=httpx.Response(
                409,
                json={
                    "id": "previous_secret_still_active",
                    "message": "A previous signing secret is still valid.",
                },
            )
        )

        with pytest.raises(AbyssaleAPIError) as raised:
            client.rotate_signing_secret()

        assert raised.value.id == "previous_secret_still_active"
        assert raised.value.status == 409

    def test_a_409_is_not_retried(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        """It is a state conflict, not a transient failure: repeating it cannot succeed, and the
        override is an explicit `force=true`, never an automatic retry."""
        route = respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(
            return_value=httpx.Response(409, json={"id": "previous_secret_still_active", "message": "x"})
        )

        with pytest.raises(AbyssaleAPIError):
            client.rotate_signing_secret()

        assert route.call_count == 1


class TestRevokeSigningSecret:
    def test_it_posts_with_no_body_and_no_query(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.post(f"{BASE_URL}/signing-secret/revoke").mock(return_value=httpx.Response(200, json=SECRET))

        client.revoke_signing_secret()

        request = route.calls.last.request
        assert not request.url.params
        assert not request.content


class TestTheAsyncClientAgrees:
    async def test_the_three_methods_hit_the_same_paths(self, respx_mock: respx.MockRouter) -> None:
        get = respx_mock.get(f"{BASE_URL}/signing-secret").mock(return_value=httpx.Response(200, json=SECRET))
        rotate = respx_mock.post(f"{BASE_URL}/signing-secret/rotate").mock(
            return_value=httpx.Response(200, json=SECRET)
        )
        revoke = respx_mock.post(f"{BASE_URL}/signing-secret/revoke").mock(
            return_value=httpx.Response(200, json=SECRET)
        )

        async with AsyncAbyssale(api_key=API_KEY, base_url=BASE_URL) as client:
            await client.get_signing_secret()
            await client.rotate_signing_secret(force=True)
            await client.revoke_signing_secret()

        assert get.called and revoke.called
        assert rotate.calls.last.request.url.params["force"] == "true"
