"""The asynchronous client — a mirror of :mod:`abyssale._client`.

Deliberately a mirror rather than an abstraction. All the logic that could actually diverge
(retry classification, the poll schedule, response parsing, config) lives in shared transport-free
modules; what is duplicated here is a set of one-line delegations, and eighty trivial lines are
cheaper than the indirection needed to generate them. ``tests/test_async_parity.py`` fails if a
method is added to one client and not the other — and if either drifts from the spec's
``operationId`` list — so the mirror cannot silently rot.

Read :mod:`abyssale._client` for the per-method documentation; the docstrings here are short on
purpose to keep the two files diffable.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any

import httpx

from ._config import resolve_api_key, resolve_base_url, resolve_max_retries, resolve_timeout
from ._errors import AbyssaleConnectionError, AbyssaleError
from ._polling import PollLoop, check_generation_result, resolve_poll_options
from ._retry import retry_schedule
from ._transport import clean_query, default_headers, encode_path, raise_for_status, validate, validate_list
from ._version import __version__
from .models import (
    AuthResult,
    Banner,
    DesignDetail,
    DesignFormatDetail,
    DesignListItem,
    DuplicationRequest,
    DuplicationRequestStatus,
    DynamicImageResponse,
    ExportAccepted,
    Font,
    GenerationRequestAccepted,
    GenerationRequestStatus,
    Project,
    ProjectSummary,
    WorkspaceTemplate,
    WorkspaceTemplateCategory,
)

Body = Mapping[str, Any]


class AsyncAbyssale:
    """Async client for the Abyssale API. Same surface as :class:`~abyssale.Abyssale`.

    Example
    -------
    ::

        import asyncio
        from abyssale import AsyncAbyssale

        async def main():
            async with AsyncAbyssale() as client:
                accepted = await client.generate_multi_format_media(design_id, {...})
                result = await client.wait_for_generation_request(accepted.generation_request_id)

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(base_url)
        self.timeout = resolve_timeout(timeout)
        self.max_retries = resolve_max_retries(max_retries)
        self._headers = default_headers(self._api_key, __version__)
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def aclose(self) -> None:
        """Close the underlying connection pool, unless it was passed in."""
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncAbyssale:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    # ── Transport ─────────────────────────────────────────────────────────────

    async def _send(self, method: str, path: str, query: Any, json: Any) -> httpx.Response:
        try:
            return await self._http.request(
                method,
                f"{self.base_url}{path}",
                params=query,
                json=json,
                headers=self._headers,
                timeout=self.timeout,
            )
        except httpx.HTTPError as err:
            raise AbyssaleConnectionError(f"[abyssale] request to {path} failed: {err}") from err

    async def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json: Body | None = None,
    ) -> Any:
        query = clean_query(query)
        response = await self._send(method, path, query, json)

        schedule = retry_schedule(response, method, self.max_retries)
        delay = next(schedule, None)
        while delay is not None:
            await asyncio.sleep(delay)
            response = await self._send(method, path, query, json)
            try:
                delay = schedule.send(response)
            except StopIteration:
                break

        return raise_for_status(response)

    # ── Authentication ────────────────────────────────────────────────────────

    async def verify_api_key(self) -> AuthResult:
        """Verify the API key and return the workspace it belongs to."""
        return validate(AuthResult, await self._request("POST", "/auth"))

    # ── Designs ───────────────────────────────────────────────────────────────

    async def list_designs(
        self,
        *,
        project_id: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> list[DesignListItem]:
        """List all designs in the workspace."""
        query = {"project_id": project_id, "type": type}
        return validate_list(DesignListItem, await self._request("GET", "/designs", query=query))

    async def get_design(self, design_id: str, *, advanced: bool = False) -> DesignDetail:
        """Get the full specification of a design. ``advanced=True`` includes ``group`` layers."""
        path = encode_path("/designs/{design_id}", design_id=design_id)
        return validate(DesignDetail, await self._request("GET", path, query={"i": "advanced"} if advanced else None))

    async def get_design_format(self, design_id: str, format_specifier: str) -> DesignFormatDetail:
        """Get one format of a design, by name or UUID. Always the advanced view."""
        path = encode_path(
            "/designs/{design_id}/formats/{format_specifier}",
            design_id=design_id,
            format_specifier=format_specifier,
        )
        return validate(DesignFormatDetail, await self._request("GET", path))

    # ── Asset generation ──────────────────────────────────────────────────────

    async def generate_image(self, design_id: str, body: Body) -> Banner:
        """Synchronously generate a single image and get the result immediately."""
        path = encode_path("/banner-builder/{design_id}/generate", design_id=design_id)
        return validate(Banner, await self._request("POST", path, json=body))

    async def generate_multi_format_media(self, design_id: str, body: Body) -> GenerationRequestAccepted:
        """Asynchronously generate one or more formats (image, GIF, video, HTML5, PDF)."""
        path = encode_path("/async/banner-builder/{design_id}/generate", design_id=design_id)
        return validate(GenerationRequestAccepted, await self._request("POST", path, json=body))

    async def generate_multi_page_pdf(self, design_id: str, body: Body) -> GenerationRequestAccepted:
        """Asynchronously generate a multi-page PDF from a ``printer_multipage`` design."""
        path = encode_path("/async/banner-builder/{design_id}/generate-multipage-pdf", design_id=design_id)
        return validate(GenerationRequestAccepted, await self._request("POST", path, json=body))

    async def get_generation_request(self, generation_request_id: str) -> GenerationRequestStatus:
        """Poll the status of an async generation request once."""
        path = encode_path("/generation-request/{generation_request_id}", generation_request_id=generation_request_id)
        return validate(GenerationRequestStatus, await self._request("GET", path))

    # ── Files ─────────────────────────────────────────────────────────────────

    async def get_file(self, banner_id: str) -> Banner:
        """Get metadata and download URLs for a previously generated file."""
        path = encode_path("/banners/{banner_id}", banner_id=banner_id)
        return validate(Banner, await self._request("GET", path))

    # ── Fonts ─────────────────────────────────────────────────────────────────

    async def list_fonts(self) -> list[Font]:
        """List all fonts available in the workspace."""
        return validate_list(Font, await self._request("GET", "/fonts"))

    # ── Projects ──────────────────────────────────────────────────────────────

    async def list_projects(self) -> list[ProjectSummary]:
        """List all projects in the workspace."""
        return validate_list(ProjectSummary, await self._request("GET", "/projects"))

    async def create_project(self, body: Body) -> Project:
        """Create a project to organise your designs."""
        return validate(Project, await self._request("POST", "/projects", json=body))

    # ── Exports ───────────────────────────────────────────────────────────────

    async def export_banners(self, body: Body) -> ExportAccepted:
        """Asynchronously package a set of banners into a single ZIP archive."""
        return validate(ExportAccepted, await self._request("POST", "/async/banners/export", json=body))

    # ── Dynamic images ────────────────────────────────────────────────────────

    async def create_dynamic_image_url(self, design_id: str, body: Body | None = None) -> DynamicImageResponse:
        """Create (or retrieve the existing) dynamic image URL for a design."""
        path = encode_path("/designs/{design_id}/dynamic-image-url", design_id=design_id)
        return validate(DynamicImageResponse, await self._request("POST", path, json=body or {}))

    # ── Workspace templates ───────────────────────────────────────────────────

    async def list_workspace_templates(
        self,
        *,
        category_id: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> list[WorkspaceTemplate]:
        """List the organisation-level master designs shared across the workspace."""
        query = {"category_id": category_id, "type": type}
        return validate_list(WorkspaceTemplate, await self._request("GET", "/workspace-templates", query=query))

    async def list_workspace_template_categories(self) -> list[WorkspaceTemplateCategory]:
        """List the categories that group workspace templates."""
        return validate_list(WorkspaceTemplateCategory, await self._request("GET", "/workspace-template-categories"))

    async def duplicate_workspace_template(self, company_template_id: str, body: Body) -> DuplicationRequest:
        """Duplicate a shared workspace template into one of your projects."""
        path = encode_path("/workspace-templates/{company_template_id}/use", company_template_id=company_template_id)
        return validate(DuplicationRequest, await self._request("POST", path, json=body))

    async def get_duplication_request(self, duplicate_request_id: str) -> DuplicationRequestStatus:
        """Poll the status of an async template duplication once."""
        path = encode_path(
            "/design-duplication-requests/{duplicate_request_id}", duplicate_request_id=duplicate_request_id
        )
        return validate(DuplicationRequestStatus, await self._request("GET", path))

    # ── Polling helpers ───────────────────────────────────────────────────────

    async def wait_for_generation_request(
        self,
        generation_request_id: str,
        *,
        interval: float | None = None,
        max_interval: float | None = None,
        timeout: float | None = None,
    ) -> GenerationRequestStatus:
        """Wait for an async generation to complete. Partial success resolves; see the sync client."""
        loop = PollLoop(resolve_poll_options(interval, max_interval, timeout))
        while True:
            try:
                data = await self.get_generation_request(generation_request_id)
            except AbyssaleError as err:
                loop.absorb(err)
            else:
                loop.succeeded()
                if data.is_finalized:
                    return check_generation_result(data)
            await asyncio.sleep(loop.next_wait())

    async def wait_for_duplication_request(
        self,
        duplicate_request_id: str,
        *,
        interval: float | None = None,
        max_interval: float | None = None,
        timeout: float | None = None,
    ) -> DuplicationRequestStatus:
        """Wait for a template duplication to reach ``COMPLETED`` or ``ERROR``."""
        loop = PollLoop(resolve_poll_options(interval, max_interval, timeout))
        while True:
            try:
                data = await self.get_duplication_request(duplicate_request_id)
            except AbyssaleError as err:
                loop.absorb(err)
            else:
                loop.succeeded()
                if str(getattr(data.status, "value", data.status)) in ("COMPLETED", "ERROR"):
                    return data
            await asyncio.sleep(loop.next_wait())
