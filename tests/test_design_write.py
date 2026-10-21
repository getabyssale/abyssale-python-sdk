"""The three design write operations (API ``v2026-10-21``).

They are one-liners over ``_request``; what can go wrong is the HTTP method, the path and the body
reaching the wire, and the error envelope mapping — so that is what is asserted.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from abyssale import Abyssale, AbyssaleAPIError, AsyncAbyssale

from .conftest import BASE_URL

RESULT = {"id": "d1", "name": "Summer sale", "version": "v2026-10-21"}


class TestRenameDesign:
    def test_it_puts_the_name(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.put(f"{BASE_URL}/designs/d1/name").mock(return_value=httpx.Response(200, json=RESULT))

        result = client.rename_design("d1", {"name": "Summer sale"})

        assert result.name == "Summer sale"
        assert json.loads(route.calls.last.request.content) == {"name": "Summer sale"}

    def test_an_unknown_design_raises_template_not_found(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        body = {"id": "template_not_found", "message": "Template UUID 'd1' not found"}
        respx_mock.put(f"{BASE_URL}/designs/d1/name").mock(return_value=httpx.Response(404, json=body))

        with pytest.raises(AbyssaleAPIError) as exc:
            client.rename_design("d1", {"name": "x"})

        assert exc.value.id == "template_not_found"


class TestMoveDesign:
    def test_it_puts_the_project_id(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.put(f"{BASE_URL}/designs/d1/project").mock(return_value=httpx.Response(200, json=RESULT))

        client.move_design("d1", {"project_id": "p1"})

        assert json.loads(route.calls.last.request.content) == {"project_id": "p1"}


class TestDeleteDesign:
    def test_it_deletes_with_no_body(self, client: Abyssale, respx_mock: respx.MockRouter) -> None:
        route = respx_mock.delete(f"{BASE_URL}/designs/d1").mock(return_value=httpx.Response(200, json=RESULT))

        result = client.delete_design("d1")

        assert result.id == "d1"
        assert route.calls.last.request.content == b""

    async def test_the_async_client_mirrors_it(self, async_client: AsyncAbyssale, respx_mock: respx.MockRouter) -> None:
        respx_mock.delete(f"{BASE_URL}/designs/d1").mock(return_value=httpx.Response(200, json=RESULT))

        result = await async_client.delete_design("d1")

        assert result.name == "Summer sale"
