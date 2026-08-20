"""The public model surface.

Two kinds of model live here:

1. **Re-exports** of the generated component schemas (``Banner``, ``Design``, ``Font``, …). These
   are the spec's own named schemas, so they are stable across releases and safe to import.
2. **Response models** for the handful of endpoints whose 2xx body is an *inline* schema in the
   spec — an ``allOf`` of a named schema plus a few extra fields. Code generation names those after
   the request path (``DesignsDesignIdFormatsFormatSpecifierGetResponse``), which is both unreadable
   and unstable, so they are written by hand here as thin subclasses instead. Adding a field to one
   of those responses in the spec means adding it here too; every model allows unknown fields, so
   the SDK keeps working in the meantime and the field is simply untyped until it is declared.

Everything else in ``abyssale._generated`` is private. Import from ``abyssale`` or
``abyssale.models``, never from ``abyssale._generated``.
"""

from __future__ import annotations

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

from ._generated import (
    Banner,
    Design,
    DesignAnimation,
    DesignElement,
    DesignFormat,
    DesignFormatElement,
    DesignFormatSummary,
    DesignPage,
    DesignPageElement,
    DesignSummary,
    DesignVariables,
    DuplicatedDesign,
    DuplicationRequest,
    DuplicationRequestStatus,
    DynamicImageFormat,
    DynamicImageResponse,
    Elements,
    ErrorResponse,
    Font,
    GenerationRequestStatus,
    Pages,
    Problem,
    ProjectSummary,
    SigningSecret,
    TextToImageProperties,
    WorkspaceTemplate,
    WorkspaceTemplateCategory,
)
from ._generated import Warning as ResponseWarning


class _Response(BaseModel):
    """Base for the hand-written response models.

    ``extra="allow"`` for the same reason the generated models have it: the API ships ahead of the
    published spec, and a response carrying a field this SDK has never heard of must not raise.
    """

    model_config = ConfigDict(extra="allow")


class DesignListItem(Design):
    """One entry of :meth:`Abyssale.list_designs` — a design plus its first format's preview."""

    preview_url: AnyUrl | None = Field(default=None, description="Preview image URL of the first design format.")


class DesignDetail(Design):
    """The full specification of a design: formats, elements and variables.

    Multipage print designs (``printer_multipage``) have no formats — they carry :attr:`pages` and
    :attr:`elements_per_page` (keyed ``page_1 … page_N``) instead of :attr:`formats`,
    :attr:`elements` and :attr:`variables`.
    """

    formats: list[DesignFormat] | None = None
    elements: list[DesignElement] | None = None
    variables: DesignVariables | None = None
    animation: DesignAnimation | None = None
    dpi: int | None = None
    bleed_size: float | None = None
    safe_size: float | None = None
    pages: list[DesignPage] | None = None
    #: ``printer_multipage`` only — page id → that page's elements. Values are
    #: :class:`DesignPageElement`, *not* :class:`DesignElement`: a page is a single format, so they
    #: are flat rather than keyed by format name.
    elements_per_page: dict[str, list[DesignPageElement]] | None = None


class DesignFormatDetail(DesignFormat):
    """One format of a design, always in the advanced view."""

    animation: DesignAnimation | None = None
    design: DesignFormatSummary | None = None
    elements: list[DesignFormatElement] | None = None
    variables: DesignVariables | None = None
    version: str | None = None


class Project(ProjectSummary):
    """A project, as returned by :meth:`Abyssale.create_project`."""

    version: str | None = None


class AuthResult(_Response):
    """The workspace an API key belongs to."""

    company: str
    version: str | None = None


class GenerationRequestAccepted(_Response):
    """The receipt for an async generation — poll :attr:`generation_request_id`."""

    generation_request_id: str
    version: str | None = None


class ExportAccepted(_Response):
    """The receipt for an async export."""

    export_id: str
    version: str | None = None


__all__ = [
    # Hand-written response models
    "AuthResult",
    "DesignDetail",
    "DesignFormatDetail",
    "DesignListItem",
    "ExportAccepted",
    "GenerationRequestAccepted",
    "Project",
    # Generated component schemas
    "Banner",
    "Design",
    "DesignAnimation",
    "DesignElement",
    "DesignFormat",
    "DesignFormatElement",
    "DesignFormatSummary",
    "DesignPage",
    "DesignPageElement",
    "DesignSummary",
    "DesignVariables",
    "DuplicatedDesign",
    "DuplicationRequest",
    "DuplicationRequestStatus",
    "DynamicImageFormat",
    "DynamicImageResponse",
    "Elements",
    "ErrorResponse",
    "Font",
    "GenerationRequestStatus",
    "Pages",
    "Problem",
    "ProjectSummary",
    "SigningSecret",
    "ResponseWarning",
    "TextToImageProperties",
    "WorkspaceTemplate",
    "WorkspaceTemplateCategory",
]
