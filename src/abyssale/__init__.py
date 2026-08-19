"""Official Python SDK for the Abyssale API — image, video and PDF generation.

    from abyssale import Abyssale

    with Abyssale() as client:            # reads ABYSSALE_API_KEY
        design = client.get_design("64238d01-d402-474b-8c2d-fbc957e9d290")
        banner = client.generate_image(design.id, {
            "elements": {"title": {"payload": "Hello World"}},
            "template_format_name": "facebook-post",
        })
        print(banner.file.cdn_url)

Async is the same surface: ``from abyssale import AsyncAbyssale``.

Errors raise. Every failure is an :class:`AbyssaleError`; a non-2xx is an :class:`AbyssaleAPIError`
carrying the API's machine-readable ``id``, which is what you branch on.

Docs: https://developers.abyssale.com/sdks/python
"""

from ._async_client import AsyncAbyssale
from ._client import Abyssale
from ._errors import (
    AbyssaleAPIError,
    AbyssaleAuthError,
    AbyssaleConfigError,
    AbyssaleConnectionError,
    AbyssaleError,
    AbyssaleNotFoundError,
    AbyssalePollingError,
    AbyssaleRateLimitError,
)
from ._version import __version__
from .models import (
    AuthResult,
    Banner,
    Design,
    DesignAnimation,
    DesignDetail,
    DesignElement,
    DesignFormat,
    DesignFormatDetail,
    DesignListItem,
    DesignPage,
    DesignPageElement,
    DuplicatedDesign,
    DuplicationRequest,
    DuplicationRequestStatus,
    DynamicImageResponse,
    ErrorResponse,
    ExportAccepted,
    Font,
    GenerationRequestAccepted,
    GenerationRequestStatus,
    Project,
    ProjectSummary,
    TextToImageProperties,
    WorkspaceTemplate,
    WorkspaceTemplateCategory,
)

__all__ = [
    "Abyssale",
    "AsyncAbyssale",
    "__version__",
    # Errors
    "AbyssaleAPIError",
    "AbyssaleAuthError",
    "AbyssaleConfigError",
    "AbyssaleConnectionError",
    "AbyssaleError",
    "AbyssaleNotFoundError",
    "AbyssalePollingError",
    "AbyssaleRateLimitError",
    # Models
    "AuthResult",
    "Banner",
    "Design",
    "DesignAnimation",
    "DesignDetail",
    "DesignElement",
    "DesignFormat",
    "DesignFormatDetail",
    "DesignListItem",
    "DesignPage",
    "DesignPageElement",
    "DuplicatedDesign",
    "DuplicationRequest",
    "DuplicationRequestStatus",
    "DynamicImageResponse",
    "ErrorResponse",
    "ExportAccepted",
    "Font",
    "GenerationRequestAccepted",
    "GenerationRequestStatus",
    "Project",
    "ProjectSummary",
    "TextToImageProperties",
    "WorkspaceTemplate",
    "WorkspaceTemplateCategory",
]
