"""The synchronous client.

Method names, arguments and semantics mirror ``abyssale-nodejs-sdk/src/index.ts`` one for one,
snake_cased. The one deliberate difference is the error contract: these methods return the parsed
result and **raise** on failure, where the Node SDK returns ``{data, error, response}``.

Request bodies are plain dicts, not models. The spec's ``elements`` schema is an ``anyOf`` of ten
deliberately overlapping branches with no discriminator — an element payload carries no type field,
because the layer's type comes from the design — so nothing can validate it offline, and a model
would only mis-coerce. Responses *are* models: their shapes are unambiguous.
"""

from __future__ import annotations

import time
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


class Abyssale:
    """Client for the Abyssale API.

    Parameters
    ----------
    api_key:
        Your workspace API key. Defaults to ``$ABYSSALE_API_KEY``.
    base_url:
        Defaults to ``$ABYSSALE_BASE_URL`` or ``https://api.abyssale.com``.
    timeout:
        Per-attempt timeout in seconds. Defaults to ``$ABYSSALE_TIMEOUT_MS`` (milliseconds) or 30s.
        A retry gets its own fresh window, so a long ``Retry-After`` does not eat the budget of the
        attempt that follows it.
    max_retries:
        Defaults to ``$ABYSSALE_MAX_RETRIES`` or 3. Set to 0 to disable retries entirely.
    http_client:
        Bring your own ``httpx.Client`` — for a proxy, a custom transport, or connection reuse
        across SDKs. Auth headers are set on the request, not on the client, so yours is untouched.

    Example
    -------
    ::

        from abyssale import Abyssale

        with Abyssale() as client:
            banner = client.generate_image(
                design_id,
                {"elements": {"title": {"payload": "Hello World"}}, "template_format_name": "facebook-post"},
            )
            print(banner.file.cdn_url)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(base_url)
        self.timeout = resolve_timeout(timeout)
        self.max_retries = resolve_max_retries(max_retries)
        self._headers = default_headers(self._api_key, __version__)
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying connection pool, unless it was passed in."""
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> Abyssale:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # ── Transport ─────────────────────────────────────────────────────────────

    def _send(self, method: str, path: str, query: Any, json: Any) -> httpx.Response:
        try:
            return self._http.request(
                method,
                f"{self.base_url}{path}",
                params=query,
                json=json,
                headers=self._headers,
                timeout=self.timeout,
            )
        except httpx.HTTPError as err:
            raise AbyssaleConnectionError(f"[abyssale] request to {path} failed: {err}") from err

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json: Body | None = None,
    ) -> Any:
        """Send, retry per :func:`abyssale._retry.retry_schedule`, then parse or raise."""
        query = clean_query(query)
        response = self._send(method, path, query, json)

        schedule = retry_schedule(response, method, self.max_retries)
        delay = next(schedule, None)
        while delay is not None:
            time.sleep(delay)
            response = self._send(method, path, query, json)
            try:
                delay = schedule.send(response)
            except StopIteration:
                break

        return raise_for_status(response)

    # ── Authentication ────────────────────────────────────────────────────────

    def verify_api_key(self) -> AuthResult:
        """Verify the API key and return the workspace it belongs to.

        Takes no body. Every failure is a ``401`` — unknown key, revoked key, or a plan without API
        access (``api_access_denied``); this endpoint never answers ``403``.

        Do not use the health check to test a key: it is exempt from authentication and answers
        ``200`` for a revoked key.
        """
        return validate(AuthResult, self._request("POST", "/auth"))

    # ── Designs ───────────────────────────────────────────────────────────────

    def list_designs(
        self,
        *,
        project_id: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> list[DesignListItem]:
        """List all designs in the workspace.

        Optionally filter by ``project_id`` or ``type`` (``static``, ``animated``, ``printer``,
        ``printer_multipage``).
        """
        query = {"project_id": project_id, "type": type}
        return validate_list(DesignListItem, self._request("GET", "/designs", query=query))

    def get_design(self, design_id: str, *, advanced: bool = False) -> DesignDetail:
        """Get the full specification of a design: formats, elements and variables.

        Use this to discover what data to pass in a generation request.

        Multipage print designs (``printer_multipage``) have no formats — the response carries
        ``pages`` and ``elements_per_page`` (keyed ``page_1 … page_N``) instead of ``formats``,
        ``elements``, ``variables`` and ``dynamic_image_url``.

        Pass ``advanced=True`` to get the full layer set — notably ``group`` layers, which the
        default response omits. :meth:`get_design_format` is always the advanced view and needs no
        flag.
        """
        path = encode_path("/designs/{design_id}", design_id=design_id)
        return validate(DesignDetail, self._request("GET", path, query={"i": "advanced"} if advanced else None))

    def get_design_format(self, design_id: str, format_specifier: str) -> DesignFormatDetail:
        """Get details for one format within a design.

        Always the advanced view: the full property set and the format's ``group`` layers, flattened
        to that one format. ``format_specifier`` can be the format name (e.g. ``"facebook-post"``)
        or its UUID.

        Does not apply to ``printer_multipage`` designs — they have no formats, so every specifier
        answers ``404 format_not_found``. Use :meth:`get_design` instead.
        """
        path = encode_path(
            "/designs/{design_id}/formats/{format_specifier}",
            design_id=design_id,
            format_specifier=format_specifier,
        )
        return validate(DesignFormatDetail, self._request("GET", path))

    # ── Asset generation ──────────────────────────────────────────────────────

    def generate_image(self, design_id: str, body: Body) -> Banner:
        """Synchronously generate a single image and get the result immediately.

        Best for single-asset workflows where you need the URL inline.

        Example
        -------
        ::

            banner = client.generate_image(design_id, {
                "elements": {"title": {"payload": "Hello World"}},
                "template_format_name": "facebook-post",
            })
        """
        path = encode_path("/banner-builder/{design_id}/generate", design_id=design_id)
        return validate(Banner, self._request("POST", path, json=body))

    def generate_multi_format_media(self, design_id: str, body: Body) -> GenerationRequestAccepted:
        """Asynchronously generate one or more formats (image, GIF, video, HTML5, PDF).

        Returns a ``generation_request_id`` to poll with :meth:`wait_for_generation_request`, or
        provide a ``callback_url`` to receive a webhook when it completes.

        Example
        -------
        ::

            accepted = client.generate_multi_format_media(design_id, {
                "elements": {"title": {"payload": "Summer Sale"}},
                "template_format_names": ["facebook-feed", "instagram-post"],
                "callback_url": "https://your-webhook.com/abyssale",
            })
        """
        path = encode_path("/async/banner-builder/{design_id}/generate", design_id=design_id)
        return validate(GenerationRequestAccepted, self._request("POST", path, json=body))

    def generate_multipage_pdf(self, design_id: str, body: Body) -> GenerationRequestAccepted:
        """Asynchronously generate a multi-page print-ready PDF from a ``printer_multipage`` design.

        Each key in ``pages`` defines the element overrides for that page.

        Example
        -------
        ::

            accepted = client.generate_multipage_pdf(design_id, {
                "pages": {
                    "page_1": {"root": {"background_color": "#FFFFFF"}},
                    "page_2": {"root": {"background_color": "#000000"}},
                },
            })
        """
        path = encode_path("/async/banner-builder/{design_id}/generate-multipage-pdf", design_id=design_id)
        return validate(GenerationRequestAccepted, self._request("POST", path, json=body))

    def get_generation_request(self, generation_request_id: str) -> GenerationRequestStatus:
        """Poll the status of an async generation request.

        ``is_finalized`` is ``False`` (HTTP 202) while in progress and ``True`` (HTTP 200) when done.
        Prefer :meth:`wait_for_generation_request`, which handles the schedule for you.
        """
        path = encode_path("/generation-request/{generation_request_id}", generation_request_id=generation_request_id)
        return validate(GenerationRequestStatus, self._request("GET", path))

    # ── Files ─────────────────────────────────────────────────────────────────

    def get_file(self, banner_id: str) -> Banner:
        """Get metadata and download URLs (S3 + CDN) for a previously generated file."""
        return validate(Banner, self._request("GET", encode_path("/banners/{banner_id}", banner_id=banner_id)))

    # ── Fonts ─────────────────────────────────────────────────────────────────

    def list_fonts(self) -> list[Font]:
        """List all fonts available in the workspace (Google Fonts + custom uploads).

        Use a font's ``id`` to override the font in a generation request.
        """
        return validate_list(Font, self._request("GET", "/fonts"))

    # ── Projects ──────────────────────────────────────────────────────────────

    def list_projects(self) -> list[ProjectSummary]:
        """List all projects in the workspace.

        Only designs belonging to a project are accessible via the API.
        """
        return validate_list(ProjectSummary, self._request("GET", "/projects"))

    def create_project(self, body: Body) -> Project:
        """Create a project to organise your designs.

        Example
        -------
        ::

            project = client.create_project({"name": "Summer Campaign 2026"})
        """
        return validate(Project, self._request("POST", "/projects", json=body))

    # ── Exports ───────────────────────────────────────────────────────────────

    def export_banners(self, body: Body) -> ExportAccepted:
        """Asynchronously package a set of banners into a single ZIP archive.

        Provide a ``callback_url`` to receive a webhook when the archive is ready.

        Example
        -------
        ::

            export = client.export_banners({
                "ids": ["uuid-1", "uuid-2"],
                "callback_url": "https://your-webhook.com/export",
            })
        """
        return validate(ExportAccepted, self._request("POST", "/async/banners/export", json=body))

    # ── Dynamic images ────────────────────────────────────────────────────────

    def create_dynamic_image_url(self, design_id: str, body: Body | None = None) -> DynamicImageResponse:
        """Create (or retrieve the existing) dynamic image URL for a design.

        The returned URL can be embedded in emails or websites and customised via query parameters —
        no extra API calls needed. Every field of the body has a default, so it may be omitted.

        Example
        -------
        ::

            dynamic = client.create_dynamic_image_url(design_id, {"enable_production_mode": True})
        """
        path = encode_path("/designs/{design_id}/dynamic-image-url", design_id=design_id)
        return validate(DynamicImageResponse, self._request("POST", path, json=body or {}))

    # ── Workspace templates ───────────────────────────────────────────────────

    def list_workspace_templates(
        self,
        *,
        category_id: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> list[WorkspaceTemplate]:
        """List the organisation-level master designs shared across the workspace.

        Optionally filter by ``category_id`` (see :meth:`list_workspace_template_categories`) or
        ``type``. Workspace templates never appear in :meth:`list_designs` — duplicate one into a
        project with :meth:`duplicate_workspace_template` to work on it as a design.
        """
        query = {"category_id": category_id, "type": type}
        return validate_list(WorkspaceTemplate, self._request("GET", "/workspace-templates", query=query))

    def list_workspace_template_categories(self) -> list[WorkspaceTemplateCategory]:
        """List the categories that group workspace templates.

        Use a category's ``id`` as the ``category_id`` filter on :meth:`list_workspace_templates`.
        Categories are optional — templates at the workspace root have none.
        """
        return validate_list(WorkspaceTemplateCategory, self._request("GET", "/workspace-template-categories"))

    def duplicate_workspace_template(self, company_template_id: str, body: Body) -> DuplicationRequest:
        """Duplicate a shared workspace template into one of your projects.

        Returns a ``duplication_request_id``; poll it with :meth:`wait_for_duplication_request`.

        Example
        -------
        ::

            request = client.duplicate_workspace_template(template_id, {
                "project_id": "your-project-uuid",
                "name": "Holiday Campaign Copy",
            })
        """
        path = encode_path("/workspace-templates/{company_template_id}/use", company_template_id=company_template_id)
        return validate(DuplicationRequest, self._request("POST", path, json=body))

    def get_duplication_request(self, duplicate_request_id: str) -> DuplicationRequestStatus:
        """Poll the status of an async template duplication.

        Status progresses ``INIT`` → ``IN_PROGRESS`` → ``COMPLETED`` (or ``ERROR``).
        """
        path = encode_path(
            "/design-duplication-requests/{duplicate_request_id}", duplicate_request_id=duplicate_request_id
        )
        return validate(DuplicationRequestStatus, self._request("GET", path))

    # ── Polling helpers ───────────────────────────────────────────────────────

    def wait_for_generation_request(
        self,
        generation_request_id: str,
        *,
        interval: float | None = None,
        max_interval: float | None = None,
        timeout: float | None = None,
    ) -> GenerationRequestStatus:
        """Wait for an async generation to complete, polling with exponential backoff.

        All three options are in seconds and are floored: ``interval`` at 2s (default 3),
        ``max_interval`` at 5s (default 30), ``timeout`` at 60s (default 1800 = 30 minutes).

        **Partial success resolves.** A finalized request can carry both ``banners`` and per-format
        ``errors`` — one format failing does not invalidate the others, so check ``result.errors`` if
        you need every requested format. Only a request that finalized with *no* banners at all and
        at least one error raises.

        Raises :class:`~abyssale.AbyssalePollingError` on failure or timeout; the API's error ``id``
        is on the exception, so branch on that rather than on the message.

        Example
        -------
        ::

            result = client.wait_for_generation_request(accepted.generation_request_id)
            for banner in result.banners or []:
                print(banner.file.cdn_url)
        """
        loop = PollLoop(resolve_poll_options(interval, max_interval, timeout))
        while True:
            try:
                data = self.get_generation_request(generation_request_id)
            except AbyssaleError as err:
                loop.absorb(err)
            else:
                loop.succeeded()
                if data.is_finalized:
                    return check_generation_result(data)
            time.sleep(loop.next_wait())

    def wait_for_duplication_request(
        self,
        duplicate_request_id: str,
        *,
        interval: float | None = None,
        max_interval: float | None = None,
        timeout: float | None = None,
    ) -> DuplicationRequestStatus:
        """Wait for a template duplication to reach ``COMPLETED`` or ``ERROR``.

        Note that ``ERROR`` is a *result*, not an exception — check ``result.status``.
        """
        loop = PollLoop(resolve_poll_options(interval, max_interval, timeout))
        while True:
            try:
                data = self.get_duplication_request(duplicate_request_id)
            except AbyssaleError as err:
                loop.absorb(err)
            else:
                loop.succeeded()
                if str(getattr(data.status, "value", data.status)) in ("COMPLETED", "ERROR"):
                    return data
            time.sleep(loop.next_wait())
