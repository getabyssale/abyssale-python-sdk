"""Models generated from the Abyssale OpenAPI spec. DO NOT EDIT.

Regenerate with `python scripts/generate.py`. See AGENTS.md.

Every model allows unknown fields (`extra="allow"`): the API ships ahead of the published spec,
and a response carrying a field this SDK has never heard of must not raise.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, RootModel


class SigningSecret(BaseModel):
    """
    The workspace's webhook signing secret and the state of any rotation in progress.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    secret: Annotated[
        str,
        Field(
            description='The secret to verify `X-Abyssale-Signature` with. Prefixed `whsec_` so it is\nrecognisable if it turns up somewhere it should not.\n',
            examples=[
                'whsec_2f1a8c4e6b9d0a7c3e5f8b1d4a6c9e2f0b3d5a7c1e4f6b8d0a2c5e7f9b1d3a5c'
            ],
        ),
    ]
    created_at_ts: Annotated[
        int,
        Field(
            description='Unix second the secret was first issued.',
            examples=[1755561234],
        ),
    ]
    rotated_at_ts: Annotated[
        int | None,
        Field(
            description='Unix second of the most recent rotation, or `null` if the secret has never been rotated.\n',
            examples=[None],
        ),
    ] = None
    previous_secret_expires_at_ts: Annotated[
        int | None,
        Field(
            description="When the previous secret stops being honoured — 24 hours after the rotation that\ndemoted it. `null` when there is no overlap in progress, either because nothing was\nrotated, because the window has lapsed, or because it was ended with\n`POST /signing-secret/revoke`.\n\nWhile this is set, deliveries carry **two** `v1` hashes and a receiver holding either\nsecret verifies. The previous secret's value is never returned — only its expiry.\n",
            examples=[None],
        ),
    ] = None


class Warning(BaseModel):
    """
    One non-fatal note attached to an otherwise successful response — the `warnings` array on
    `GET /designs/{designId}/as-import` and on the import status endpoint. Only `message` is
    guaranteed: an entry with no `code` is informational and carries no stable machine
    identity, so branch only on entries that have one.

    Same field meanings as `Problem`; split from it because `code` is required there.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    message: Annotated[str, Field(description='Human-readable explanation.')]
    code: Annotated[
        str | None,
        Field(
            description='Stable, machine-readable code, when the warning has one. Absent on purely\ninformational entries.\n',
            examples=['color_converted'],
        ),
    ] = None
    path: Annotated[
        str | None,
        Field(
            description='Where in the payload the warning applies, same syntax as `Problem.path`.',
            examples=['layers[2].properties.color'],
        ),
    ] = None
    layer: Annotated[
        str | None,
        Field(
            description='Name of the layer the entry belongs to, when it was raised while transforming a\nlayer. An index in `path` identifies a position in the emitted array, which is not\nthe name the caller sees in the editor — group on this rather than parsing `path`.\n',
            examples=['headline'],
        ),
    ] = None


class Expected(BaseModel):
    """
    Bounds, for a range problem — `{ min, max }`.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    min: float | None = None
    max: float | None = None


class Problem(BaseModel):
    """
    One field-level error inside `ErrorResponse.errors`. `code` and `message` are always
    present; `path` is omitted when the error is not about a particular field (an unhandled
    `500`, for instance). Informational warnings are a DIFFERENT shape — see `Warning` —
    because a warning may legitimately carry no `code`, and one schema cannot say
    "required here, optional there".

    """

    model_config = ConfigDict(
        extra='allow',
    )
    path: Annotated[
        str | None,
        Field(
            description='Path into the request body where the problem applies. **Syntax (normative):** object\nkeys are dotted, array indices are bracketed — `formats[0].width`,\n`pages[2].layers[7].layout.x`, `target.project_uuid`. A whole array/object is named\nbare (`layers`, `pages`, `body`, `uploads`), as are the document-level\n`printer_multipage` print settings (`unit`, `width`, `height`, `dpi`).\n',
            examples=['layers[2].properties.font_size'],
        ),
    ] = None
    code: Annotated[
        str,
        Field(
            description="Stable, machine-readable code. Agents should branch on `code`, not on `message`.\n\nPayload/validation codes: `missing_required`, `unknown_field`, `wrong_type`,\n`out_of_range`, `unknown_enum_value`, `unknown_format_key`, `duplicate_layer_name`,\n`duplicate_format_name`, `reserved_format_name`, `project_not_found` (**400**),\n`conditional_dependency_missing`, `invalid_payload`, `unsupported_for_type`,\n`unknown_font`, `unreachable_src`, `mutually_exclusive` (two fields that cannot be\ncombined were both supplied).\nUpload/lifecycle codes: `missing_assets`, `template_import_already_processed`,\n`not_found` (**404** — the import does not exist for this company).\nExport code: `not_round_trippable`.\nTransport codes: `invalid_query_param` (an unparseable query-parameter value; `path`\nis the parameter name), `internal_error` (an unhandled server-side error, returned in\nthis same envelope with a 500 status).\nBuild-phase failure codes (surfaced in the status response's `error`):\n`text_fit_failed`, `image_processing_failed` (genuine image failures only),\n`media_processing_failed` (a video/audio container could not be resolved or\nprocessed), `invalid_asset` (an asset arrived but could not be decoded — truncated or\ncorrupt), `font_resolution_failed`, `import_failed` (fallback for a processing failure\nwith no more specific code).\n",
            examples=['out_of_range'],
        ),
    ]
    message: Annotated[str, Field(examples=['font_size must be between 2 and 1000'])]
    expected: Annotated[
        list[str] | Expected | str | None,
        Field(
            description='Type-dependent. For enums an array of allowed values; for ranges `{ min, max }`; for\n`missing_assets` the list of unfulfilled upload targets. Present on `out_of_range` and\n`unknown_enum_value` for schema-derived problems as well as hand-written ones.\n'
        ),
    ] = None
    received: Annotated[
        str | float | bool | dict[str, Any] | list[Any] | None,
        Field(
            description='The offending value, echoed back as it arrived — any JSON type. Omitted when not meaningful.'
        ),
    ] = None


class Project(BaseModel):
    """
    The design's project — present when the design has one.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    id: UUID | None = None
    name: str | None = None
    created_at_ts: int | None = None


class Image(BaseModel):
    """
    Deprecated — same information as `file.type` / `file.url`.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    type: str | None = None
    url: AnyUrl | None = None


class VisualStatus(BaseModel):
    """
    Present when the visual carries a review status.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    status: str | None = None
    status_updated_at_ts: int | None = None
    reason: str | None = None
    content_to_replace: Annotated[
        str | None,
        Field(
            description='Review feedback — content the reviewer asked to be replaced.'
        ),
    ] = None
    content_to_hide: Annotated[
        str | None,
        Field(description='Review feedback — content the reviewer asked to be hidden.'),
    ] = None


class Type(Enum):
    """
    File type. `webp` and `avif` are returned when `image_file_type` asked for them; an `html5` generation is delivered as `zip`.
    """

    jpeg = 'jpeg'
    png = 'png'
    webp = 'webp'
    avif = 'avif'
    pdf = 'pdf'
    gif = 'gif'
    mp4 = 'mp4'
    zip = 'zip'


class File(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[
        Type,
        Field(
            description='File type. `webp` and `avif` are returned when `image_file_type` asked for them; an `html5` generation is delivered as `zip`.',
            examples=['jpeg'],
        ),
    ]
    url: Annotated[
        str,
        Field(
            description='URL of the banner (useful to download the image).',
            examples=[
                'https://production-banners.s3.eu-west-1.amazonaws.com/demo/996739f4-b563-428a-a6e8-ec3cb8bd03d4.jpeg'
            ],
        ),
    ]
    cdn_url: Annotated[
        str | None,
        Field(
            description='The CDN URL of the banner (useful to host the image; on a website for instance). (A bandwidth usage limit applies, related to your plan). (Not available for zip)',
            examples=[
                'https://cdn.abyssale.com/demo/996739f4-b563-428a-a6e8-ec3cb8bd03d4.jpeg'
            ],
        ),
    ] = None
    filename: Annotated[
        str | None,
        Field(
            description='Name of the file. If the related design contains a custom naming scheme, the custom name will be available from this property.',
            examples=['996739f4-b563-428a-a6e8-ec3cb8bd03d4.jpeg'],
        ),
    ] = None
    fallback_image_url: Annotated[
        str | None,
        Field(
            description='Backup JPEG URL — present only when `type` is `zip` (HTML5 output).'
        ),
    ] = None


class Format(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str | None,
        Field(
            description='Identifier/name of the format. Absent on multi-page print visuals.',
            examples=['facebook-post'],
        ),
    ] = None
    unit: Annotated[
        str | None,
        Field(
            description='Unit of `width`/`height` — `px`, or `mm`/`in` on print designs.',
            examples=['px'],
        ),
    ] = None
    width: Annotated[
        float,
        Field(
            description='Width of the format, in `unit`. A float on print designs (mm/in).',
            examples=[1200],
        ),
    ]
    height: Annotated[
        float,
        Field(
            description='Height of the format, in `unit`. A float on print designs (mm/in).',
            examples=[1200],
        ),
    ]


class Type1(Enum):
    """
    Type of the design
    """

    static = 'static'
    printer = 'printer'
    animated = 'animated'
    printer_multipage = 'printer_multipage'


class Design(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Unique identifier (UUID) of the design.',
            examples=['64238d01-d402-474b-8c2d-fbc957e9d290'],
        ),
    ]
    template_id: Annotated[
        UUID | None,
        Field(
            description='Deprecated duplicate of `id`, equal to it. Present on the single-design read; **not** emitted by the `GET /designs` listing. Kept for existing clients — read `id`.',
            examples=['64238d01-d402-474b-8c2d-fbc957e9d290'],
        ),
    ] = None
    name: Annotated[
        str,
        Field(description='Name of the design.', examples=['Ad campaign fall 2025']),
    ]
    type: Annotated[Type1, Field(description='Type of the design', examples=['static'])]
    created_at: Annotated[
        int,
        Field(
            description='Timestamp of when the design has been created.',
            examples=[1649942114],
        ),
    ]
    updated_at: Annotated[
        int,
        Field(
            description='Timestamp of when the design has been updated for the last time.',
            examples=[1649942114],
        ),
    ]
    project_id: Annotated[
        UUID,
        Field(
            description='Unique identifier (UUID) of the project the design belongs to. `null` when the project cannot be resolved.',
            examples=['9d1f2b7c-5a44-4c3e-9f21-0b8e6d4a1c73'],
        ),
    ]
    project_name: Annotated[
        str,
        Field(
            description='Name of the project the design belongs to. `null` when the project cannot be resolved.',
            examples=['Fall campaigns'],
        ),
    ]
    category_id: Annotated[
        UUID | None,
        Field(
            deprecated=True,
            description='Deprecated, superseded by `project_id`, and always equal to it on a design. `category_id` properly names the grouping of a WORKSPACE TEMPLATE — a design belongs to a project, so read `project_id`.',
            examples=['9d1f2b7c-5a44-4c3e-9f21-0b8e6d4a1c73'],
        ),
    ] = None
    category_name: Annotated[
        str | None,
        Field(
            deprecated=True,
            description='Deprecated, superseded by `project_name`, which it mirrors on every read — the platform reads both from the same `company_template_category` row, the table that holds projects. `null` when the design is in no project. `category_*` names the grouping of a WORKSPACE TEMPLATE — a design belongs to a project, so read `project_name`.',
            examples=['Fall campaigns'],
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class Type2(Enum):
    """
    Type of the workspace template
    """

    static = 'static'
    printer = 'printer'
    animated = 'animated'
    printer_multipage = 'printer_multipage'


class WorkspaceTemplate(BaseModel):
    """
    A workspace template — an organisation-level master design. Same underlying object
    as a Design, but grouped into a *category* rather than a *project*, and not
    addressable through the Designs API until duplicated into a project.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Unique identifier (UUID) of the workspace template.',
            examples=['64238d01-d402-474b-8c2d-fbc957e9d290'],
        ),
    ]
    name: Annotated[
        str,
        Field(description='Name of the workspace template.', examples=['Brand master']),
    ]
    type: Annotated[
        Type2, Field(description='Type of the workspace template', examples=['static'])
    ]
    created_at: Annotated[
        int,
        Field(
            description='Timestamp of when the workspace template has been created.',
            examples=[1649942114],
        ),
    ]
    updated_at: Annotated[
        int,
        Field(
            description='Timestamp of when the workspace template has been updated for the last time.',
            examples=[1649942114],
        ),
    ]
    preview_url: Annotated[
        AnyUrl | None, Field(description='Preview Image URL of the first format')
    ] = None
    category_id: Annotated[
        UUID | None,
        Field(
            description="Unique identifier (UUID) of the workspace category it belongs to, or `null` when the\ntemplate sits at the root of the workspace. Unlike a design's project, a category is\n**optional** — most workspace templates have none.\n",
            examples=['1c7a9e35-0b62-4d18-8f4a-2e5c7b90d146'],
        ),
    ] = None
    category_name: Annotated[
        str | None,
        Field(
            description='Name of the workspace category, or `null` when the template is at the root.',
            examples=['Brand assets'],
        ),
    ] = None


class WorkspaceTemplateCategory(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Unique identifier (UUID) of the workspace category.',
            examples=['1c7a9e35-0b62-4d18-8f4a-2e5c7b90d146'],
        ),
    ]
    name: Annotated[
        str,
        Field(description='Name of the workspace category.', examples=['Brand assets']),
    ]
    color: Annotated[
        str | None,
        Field(description='Display colour of the category.', examples=['#4F46E5']),
    ] = None
    icon: Annotated[
        str | None,
        Field(description='Display icon of the category.', examples=['star']),
    ] = None
    created_at: Annotated[
        int | None,
        Field(
            description='Timestamp of when the category has been created.',
            examples=[1649942114],
        ),
    ] = None


class DesignSummary(BaseModel):
    """
    A short reference to a design, nested inside another resource. Deliberately narrower than `Design` — only the fields the parent resource carries.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Unique identifier (UUID) of the design.',
            examples=['64238d01-d402-474b-8c2d-fbc957e9d290'],
        ),
    ]
    name: Annotated[
        str,
        Field(description='Name of the design.', examples=['Ad campaign fall 2025']),
    ]
    created_at: Annotated[int | None, Field(examples=[1649942114])] = None
    updated_at: Annotated[int | None, Field(examples=[1649942114])] = None


class Type3(Enum):
    static = 'static'
    printer = 'printer'
    animated = 'animated'
    printer_multipage = 'printer_multipage'


class DesignFormatSummary(DesignSummary):
    """
    The design a format belongs to, as returned nested in `GET /designs/{designId}/formats/{formatSpecifier}`.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Type3 | None, Field(examples=['static'])] = None
    category_name: Annotated[
        str | None,
        Field(
            deprecated=True,
            description='Deprecated alias of the project name — see `Design.category_name`.',
        ),
    ] = None


class DesignFormat(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str,
        Field(
            description='Unique identifier (name) of the format.',
            examples=['facebook-post'],
        ),
    ]
    uid: Annotated[
        UUID,
        Field(
            description='Unique UUID of the format',
            examples=['9b57d65e-eb2c-4a74-a51e-4482917c248a'],
        ),
    ]
    width: Annotated[float, Field(description='Width of the format', examples=[1200])]
    height: Annotated[float, Field(description='Height of the format', examples=[1200])]
    unit: Annotated[
        str | None,
        Field(description='Unit of measurement for dimensions', examples=['px']),
    ] = None
    preview_url: Annotated[
        AnyUrl | None,
        Field(
            description='Preview Image URL of the format',
            examples=[
                'https://production-banners.s3-eu-west-1.amazonaws.com/templates/e0d292f2-ec21-11e9-a539-3c408bf94155/a9b3c668-7b84-4924-adf0-815dae727d32.png'
            ],
        ),
    ] = None
    dynamic_image_url: Annotated[
        AnyUrl | None,
        Field(
            description='URL of the existing dynamic image for this format.',
            examples=[
                'https://img.abyssale.com/ecf1fe8c-5392-48c2-b6d2-665183a18fe5/9b57d65e-eb2c-4a74-a51e-4482917c248a'
            ],
        ),
    ] = None
    dpi: Annotated[
        int | None,
        Field(
            description="Printer designs only. Render DPI of the format, computed at import time (capped at 300; large formats degrade to stay within the renderer's pixel budget). Read-only — not an import field.",
            examples=[300],
        ),
    ] = None
    bleed_size: Annotated[
        float | None,
        Field(
            description="Printer designs only. Bleed size as a float in the design's unit (mm/in). Always present on a printer format; `0` means the zone is off.",
            examples=[3.5],
        ),
    ] = None
    safe_size: Annotated[
        float | None,
        Field(
            description="Printer designs only. Safe-zone size as a float in the design's unit (mm/in). Always present on a printer format; `0` means the zone is off.",
            examples=[5],
        ),
    ] = None


class Unit(Enum):
    """
    The document's physical authoring unit.
    """

    mm = 'mm'
    in_ = 'in'


class DesignPage(BaseModel):
    """
    One page of a `printer_multipage` design, as returned in `pages[]`.

    Deliberately **not** `DesignFormat`. A multipage design is one document with no formats —
    each page is addressed by `id` (`page_1 … page_N`), has no format `uid`, and cannot carry
    a dynamic image, so `GET /designs/{designId}/formats/{formatSpecifier}` answers
    `404 format_not_found` for every specifier.

    **A page carries no print settings.** `dpi`, `bleed_size` and `safe_size` belong to the
    document and are returned once, at the root of the design read. `width` / `height` /
    `unit` appear here because a page is a thing with dimensions, but every page of the
    document has the same ones.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str,
        Field(
            description='Page identifier, `page_1 … page_N`, in document order.',
            examples=['page_1'],
        ),
    ]
    width: Annotated[
        float,
        Field(
            description='Page width as a float in `unit`. Every page of the document shares it.',
            examples=[210],
        ),
    ]
    height: Annotated[
        float,
        Field(
            description='Page height as a float in `unit`. Every page of the document shares it.',
            examples=[297],
        ),
    ]
    unit: Annotated[
        Unit | None,
        Field(description="The document's physical authoring unit.", examples=['mm']),
    ] = None
    preview_url: Annotated[
        AnyUrl | None, Field(description='Preview image URL of this page.')
    ] = None


class DesignAnimation(BaseModel):
    """
    Animated designs only. The design's timeline, read-only (all values in seconds).

    """

    model_config = ConfigDict(
        extra='allow',
    )
    duration: Annotated[
        float | None, Field(description='Timeline length in seconds.', examples=[8.0])
    ] = None
    screenshot_at_s: Annotated[
        float | None,
        Field(
            description='The moment the HTML5 backup screenshot is taken (seconds). Null on designs created before it was recorded\nthat never stored it; always set on imported designs.\n',
            examples=[8.0],
        ),
    ] = None


class Type4(Enum):
    """
    Layer type. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `group` elements are injected only on the platform advanced view (`i=advanced`); a masked group reports `group` too, with a `mask` block. `code` is listed last because it is marginal: a custom HTML/JS layer that exists only on `animated` designs, read-only like `container` — it carries no customisable attributes, so it can never be targeted in a generation request.
    """

    container = 'container'
    text = 'text'
    button = 'button'
    image = 'image'
    logo = 'logo'
    shape = 'shape'
    illustration = 'illustration'
    rating = 'rating'
    qrcode = 'qrcode'
    video = 'video'
    audio = 'audio'
    group = 'group'
    code = 'code'


class Type5(Enum):
    slide = 'slide'
    fade = 'fade'
    scale = 'scale'
    rotate = 'rotate'
    audioFade = 'audioFade'
    textEffect = 'textEffect'


class Data(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[str | None, Field(examples=['start'])] = None
    time: Annotated[float | None, Field(examples=[0])] = None


class Keyframe(BaseModel):
    """
    One keyframe. Several keyframe generations coexist in stored designs, so extra keys are permitted rather than rejected.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    attr: Annotated[
        dict[str, Any] | None,
        Field(
            description='The properties this keyframe sets, as a map of property name to value: `{"opacity": 0}` (fade), `{"left": 1021, "top": 347}` (slide — always both), `{"scale": 120}` (scale), `{"angle": -100}` (rotate), `{"volumeEffect": 0}` (audioFade), `{"typewriting": 100, "textEffectType": "classic"}` (textEffect). Values are numbers, except `textEffectType` which is a string.',
            examples=[{'left': 1021, 'top': 347}],
        ),
    ] = None
    data: Data | None = None


class Tween(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(examples=['tb-text_0-slide_2'])] = None
    type: Type5 | None = None
    keyframes: list[Keyframe] | None = None


class Animation(BaseModel):
    """
    Animated designs only; present when the element carries timeline timing or tweens.
    An injected `group` layer carries `start_at_s` / `end_at_s` only — never `tweens`.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    start_at_s: Annotated[float | None, Field(examples=[0.79])] = None
    end_at_s: Annotated[float | None, Field(examples=[8.0])] = None
    tweens: list[Tween] | None = None


class Attribute(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The attribute name', examples=['payload'])]
    help: Annotated[
        str | None,
        Field(
            description='An helper to understand what is this attribute',
            examples=['Text content (i.e. Lorem ipsum)'],
        ),
    ] = None
    values: Annotated[
        dict[str, str | float | bool | dict[str, Any]],
        Field(examples=[{'facebook-post': 'My image title'}]),
    ]


class ElementLayout(BaseModel):
    """
    An element's box. Integers in pixels on `static`/`animated`; floats in the design's physical unit (mm/in) on `printer`.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    x: Annotated[float | None, Field(examples=[0])] = None
    y: Annotated[float | None, Field(examples=[0])] = None
    width: Annotated[float | None, Field(examples=[3333])] = None
    height: Annotated[float | None, Field(examples=[666])] = None


class GroupLayout(BaseModel):
    """
    Auto-layout settings of a `group` layer. **Empty on animated designs** — the platform stores no auto-layout there. `direction`, `placement` and `gap` appear only when `auto_layout` is on.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    auto_layout: bool | None = None
    direction: str | None = None
    placement: str | None = None
    gap: Annotated[
        float | None,
        Field(
            description='Pixels on static/animated; a physical-unit float on printer.'
        ),
    ] = None


class Radius(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    tl: float | None = None
    tr: float | None = None
    br: float | None = None
    bl: float | None = None


class GroupMask(BaseModel):
    """
    Mask geometry of a masked `group` layer.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    shape: str
    width: float | None = None
    height: float | None = None
    center_x: float | None = None
    center_y: float | None = None
    rx: float | None = None
    ry: float | None = None
    rotation: float | None = None
    radius: float | Radius | None = None


class ElementAnimationTiming(BaseModel):
    """
    Animated designs only — the element's own timeline window, in seconds.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    start_at_s: float | None = None
    end_at_s: float | None = None


class Type6(Enum):
    """
    Layer type. Narrower than the other reads: a page belongs to a print document, so `video` and `audio` — which exist only on `animated` designs — never appear here. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `group` elements are injected only on the advanced view (`i=advanced`).
    """

    container = 'container'
    text = 'text'
    button = 'button'
    image = 'image'
    logo = 'logo'
    shape = 'shape'
    illustration = 'illustration'
    rating = 'rating'
    qrcode = 'qrcode'
    group = 'group'


class Settings(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    is_mandatory: Annotated[bool | None, Field(examples=[False])] = None


class Attributes(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(examples=['payload'])] = None
    help: Annotated[str | None, Field(examples=['Text content (i.e. Lorem ipsum)'])] = (
        None
    )
    value: Annotated[
        str | float | bool | dict[str, Any] | None,
        Field(
            description='The attribute\'s single value on this page. `mask_properties` and `filter_properties` carry an **object** rather than a scalar (e.g. `{"radius": {"tl": 1000, "tr": 1000, "bl": 1000, "br": 1000}}`); their inner keys vary by mask and filter and are not enumerated here.',
            examples=['Spring Catalogue'],
        ),
    ] = None


class DesignPageElement(BaseModel):
    """
    One element of a `printer_multipage` page, as returned in `elements_per_page`.

    A page is a single format, so the per-format maps are collapsed exactly as they are on
    `GET /designs/{designId}/formats/{formatSpecifier}`: `layout` is that page's box and an
    attribute carries one `value`, not `values` keyed by format name.

    **`attributes` is an object here, keyed by attribute id — every other read returns an
    array.** That is the one difference from `DesignFormatElement`, which this schema
    otherwise matches field for field. It is an inconsistency, not a feature: the two
    single-format reads convert the platform's attribute map into an array and this path does
    not. It is documented rather than corrected because the current shape is live and in use.
    Expect it to be unified with `DesignFormatElement` in a future dated version, announced
    in the changelog — write your attribute lookup so it can tolerate both, e.g. by
    normalising with `Object.values(attributes)` / `list(attributes.values())` when it is not
    already an array.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str,
        Field(
            description='Layer name (`root` is the special element carrying the page background color).',
            examples=['headline'],
        ),
    ]
    type: Annotated[
        Type6,
        Field(
            description="Layer type. Narrower than the other reads: a page belongs to a print document, so `video` and `audio` — which exist only on `animated` designs — never appear here. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `group` elements are injected only on the advanced view (`i=advanced`).",
            examples=['text'],
        ),
    ]
    settings: Settings | None = None
    attributes: Annotated[
        dict[str, Attributes] | None,
        Field(
            description="The element's customisable attributes, **keyed by attribute id**. Each value carries\nthat attribute's `id`, an optional `help` string, and its single `value` on this page.\n",
            examples=[
                {
                    'payload': {
                        'id': 'payload',
                        'help': 'Text content',
                        'value': 'Spring Catalogue',
                    },
                    'font_size': {
                        'id': 'font_size',
                        'help': 'Font size in pt',
                        'value': 36,
                    },
                }
            ],
        ),
    ] = None
    layout: Annotated[
        ElementLayout | None,
        Field(description="The element's box on this page, in the document's unit."),
    ] = None
    layer_ids: Annotated[
        list[str] | None,
        Field(
            description='`group` layers only — the names of the layers this group contains.'
        ),
    ] = None
    hidden: Annotated[
        bool | None,
        Field(description='`group` layers only — computed visibility on this page.'),
    ] = None
    locked: Annotated[
        bool | None,
        Field(description='`group` layers only — computed lock state on this page.'),
    ] = None
    group: Annotated[
        GroupLayout | None,
        Field(description='`group` layers only — auto-layout settings on this page.'),
    ] = None
    mask: Annotated[
        GroupMask | None,
        Field(
            description='Masked `group` layers only — the mask geometry on this page.'
        ),
    ] = None


class Type7(Enum):
    """
    Layer type. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `code`, listed last, is a marginal `animated`-only custom HTML/JS layer, read-only in the same way.
    """

    container = 'container'
    text = 'text'
    button = 'button'
    image = 'image'
    logo = 'logo'
    shape = 'shape'
    illustration = 'illustration'
    rating = 'rating'
    qrcode = 'qrcode'
    video = 'video'
    audio = 'audio'
    group = 'group'
    code = 'code'


class Settings1(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    is_mandatory: Annotated[
        bool | None,
        Field(description='Whether the element is mandatory', examples=[False]),
    ] = None


class Attribute1(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str | None,
        Field(description='Attribute identifier', examples=['background_color']),
    ] = None
    help: Annotated[
        str | None,
        Field(
            description='Help text for the attribute',
            examples=[
                '6 or 8 digits hexadecimal background color (i.e. #F3F3F3) of the banner'
            ],
        ),
    ] = None
    value: Annotated[
        str | float | bool | None,
        Field(
            description="The attribute's value in the requested format. Usually a string; a `video`/`audio` layer's media attributes are typed (`video_duration`/`max_volume` numbers, `video_muted`/`audio_muted` booleans).",
            examples=['#FFFFFF'],
        ),
    ] = None


class DesignFormatElement(BaseModel):
    """
    An element as `GET /designs/{designId}/formats/{formatSpecifier}` returns it — the
    **single-format projection** of `DesignElement`.

    The endpoint answers for one format, so the per-format maps are collapsed: an attribute
    carries a single `value` instead of `values` keyed by format name, and `layout` is that
    format's box instead of a map. This is deliberate, not drift — do not "align" it with
    `DesignElement`. An attribute the requested format does not define is omitted entirely.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str,
        Field(
            description='Layer name (`root` is a special element that allows to customize the image background color.)',
            examples=['headline'],
        ),
    ]
    type: Annotated[
        Type7,
        Field(
            description="Layer type. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `code`, listed last, is a marginal `animated`-only custom HTML/JS layer, read-only in the same way.",
            examples=['text'],
        ),
    ]
    settings: Settings1 | None = None
    attributes: list[Attribute1] | None = None
    layout: Annotated[
        ElementLayout | None,
        Field(description="The element's box in the requested format."),
    ] = None
    layer_ids: Annotated[
        list[str] | None,
        Field(
            description='`group` layers only — the names of the layers this group contains.'
        ),
    ] = None
    hidden: Annotated[
        bool | None,
        Field(description='`group` layers only — computed visibility in this format.'),
    ] = None
    locked: Annotated[
        bool | None,
        Field(description='`group` layers only — computed lock state in this format.'),
    ] = None
    group: Annotated[
        GroupLayout | None,
        Field(description='`group` layers only — auto-layout settings in this format.'),
    ] = None
    mask: Annotated[
        GroupMask | None,
        Field(
            description='Masked `group` layers only — the mask geometry in this format.'
        ),
    ] = None
    animation: Annotated[
        ElementAnimationTiming | None,
        Field(description='`group` layers on animated designs only.'),
    ] = None


class DesignVariables(RootModel[dict[str, str]]):
    """
    Variables used within the text layers of the design. Keys are variable names (without
    braces), values are the placeholder as written in the design (e.g. `"{name}"`).

    """

    root: dict[str, str]


class AvailableWeights(Enum):
    """
    The list of weights supported by this font
    """

    number_100 = 100
    number_200 = 200
    number_300 = 300
    number_400 = 400
    number_500 = 500
    number_600 = 600
    number_700 = 700
    number_800 = 800
    number_900 = 900


class AvailableWeights1(Enum):
    """
    The list of weights supported by this font
    """

    field_100_italic = '100-italic'
    field_200_italic = '200-italic'
    field_300_italic = '300-italic'
    field_400_italic = '400-italic'
    field_500_italic = '500-italic'
    field_600_italic = '600-italic'
    field_700_italic = '700-italic'
    field_800_italic = '800-italic'
    field_900_italic = '900-italic'


class Type8(Enum):
    """
    Either `google` for the Google fonts or `custom` for your uploaded fonts.
    """

    google = 'google'
    custom = 'custom'


class Font(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Font unique ID, this parameter can be used to force a specific font on a text or a button element.',
            examples=['61568e7c-33c5-11ea-9877-92672c1b8195'],
        ),
    ]
    name: Annotated[str, Field(description='The font name', examples=['Ubuntu Mono'])]
    available_weights: list[AvailableWeights | AvailableWeights1]
    type: Annotated[
        Type8,
        Field(
            description='Either `google` for the Google fonts or `custom` for your uploaded fonts.'
        ),
    ]


class SharedElementProperties(BaseModel):
    """
    Properties every layer type accepts, whatever its type. Composed into `Element` and `AsyncElement` with `allOf` so they survive the per-type `anyOf` — declared as a sibling of `anyOf` they would be dropped from every branch.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    hidden: Annotated[
        bool | None,
        Field(description='`true`, `false`. If true it hides the current element'),
    ] = None
    shadow_color: Annotated[
        str | None, Field(description='6-8 digits hexadecimal color')
    ] = None
    shadow_blur: Annotated[
        float | None, Field(description='Blur in pixels', ge=0.0)
    ] = None
    shadow_offset_x: Annotated[
        float | None,
        Field(
            description='Horizontal offset in pixels (can be negative)',
            ge=-200.0,
            le=200.0,
        ),
    ] = None
    shadow_offset_y: Annotated[
        float | None,
        Field(
            description='Vertical offset in pixels (can be negative)',
            ge=-200.0,
            le=200.0,
        ),
    ] = None


class Element1(SharedElementProperties):
    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement1(SharedElementProperties):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class SideBorder(Enum):
    """
    Defines the side on which a border is rendered. Use `none` to disable an existing side border.
    """

    left = 'left'
    right = 'right'
    top = 'top'
    bottom = 'bottom'
    none = 'none'


class TextAlign(Enum):
    """
    Alignment of the **label** inside the button box. Default `center`. A button is the one layer type where these are two separate settings — on a `text` layer the alignment *is* the position.
    """

    left = 'left'
    center = 'center'
    right = 'right'


class RemoveBgProperties(BaseModel):
    """
    Additional settings for background removal. Deprecated here for the same reason as `remove_bg`.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    remove_bg_crop: Annotated[
        bool | None,
        Field(
            description='Trims the edges of the image after background removal. Default is false.'
        ),
    ] = None


class Model(Enum):
    """
    Model used for focusing. `generic` for objects, `people` for human subjects.
    Default is `generic`.

    **`face` is deprecated** — use `people` with `focus_framing: "face"`, which
    detects faces with the same model and additionally honours `focus_zoom` and
    `focus_target`. `face` ignores all three. `face` keeps working; no removal date
    is set.

    """

    generic = 'generic'
    people = 'people'
    face = 'face'


class FocusFraming(Enum):
    """
    Specific to `people` model. Defines which part of the subject to frame. Default is `face`, which is why `people` alone replaces the deprecated `face` model.
    """

    face = 'face'
    head = 'head'
    shoulders = 'shoulders'
    full_body = 'full_body'


class FocusZoom(Enum):
    """
    Specific to `people` model. Controls the zoom level applied. Default is `max`.
    """

    False_ = False
    low = 'low'
    medium = 'medium'
    max = 'max'


class FocusTarget(Enum):
    """
    Specific to `people` model. When multiple subjects are detected, defines which one to target. Default is `all`.
    """

    largest = 'largest'
    left = 'left'
    middle = 'middle'
    right = 'right'
    all = 'all'


class AutoFocusProperties(BaseModel):
    """
    Additional settings for auto-focus.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    model: Annotated[
        Model | None,
        Field(
            description='Model used for focusing. `generic` for objects, `people` for human subjects.\nDefault is `generic`.\n\n**`face` is deprecated** — use `people` with `focus_framing: "face"`, which\ndetects faces with the same model and additionally honours `focus_zoom` and\n`focus_target`. `face` ignores all three. `face` keeps working; no removal date\nis set.\n'
        ),
    ] = None
    focus_objects: Annotated[
        list[str] | None,
        Field(
            description='List of object labels to focus on (generic model only). Uses Open Images Dataset labels.'
        ),
    ] = None
    focus_framing: Annotated[
        FocusFraming | None,
        Field(
            description='Specific to `people` model. Defines which part of the subject to frame. Default is `face`, which is why `people` alone replaces the deprecated `face` model.'
        ),
    ] = None
    focus_zoom: Annotated[
        FocusZoom | None,
        Field(
            description='Specific to `people` model. Controls the zoom level applied. Default is `max`.'
        ),
    ] = None
    focus_target: Annotated[
        FocusTarget | None,
        Field(
            description='Specific to `people` model. When multiple subjects are detected, defines which one to target. Default is `all`.'
        ),
    ] = None


class Model1(Enum):
    """
    Background removal model to use. Default is `bria-rmbg-2-0`.
    """

    bria_rmbg_2_0 = 'bria-rmbg-2-0'
    birefnet = 'birefnet'
    pixelcut = 'pixelcut'
    imageUtils = 'imageUtils'
    ideogram = 'ideogram'


class RemoveBgProperties1(BaseModel):
    """
    Additional settings for background removal.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    remove_bg_crop: Annotated[
        bool | None,
        Field(
            description='Trims the edges of the image after background removal. Default is false.'
        ),
    ] = None
    model: Annotated[
        Model1 | None,
        Field(
            description='Background removal model to use. Default is `bria-rmbg-2-0`.'
        ),
    ] = None


class Model2(Enum):
    """
    Model used for focusing. `generic` for objects, `people` for human subjects.
    Default is `generic`.

    **`face` is deprecated** — use `people` with `focus_framing: "face"`, which
    detects faces with the same model and additionally honours `focus_zoom` and
    `focus_target`. `face` ignores all three. `face` keeps working; no removal date
    is set.

    """

    generic = 'generic'
    people = 'people'
    face = 'face'


class AutoFocusProperties1(BaseModel):
    """
    Additional settings for auto-focus.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    model: Annotated[
        Model2 | None,
        Field(
            description='Model used for focusing. `generic` for objects, `people` for human subjects.\nDefault is `generic`.\n\n**`face` is deprecated** — use `people` with `focus_framing: "face"`, which\ndetects faces with the same model and additionally honours `focus_zoom` and\n`focus_target`. `face` ignores all three. `face` keeps working; no removal date\nis set.\n'
        ),
    ] = None
    focus_objects: Annotated[
        list[str] | None,
        Field(
            description='List of object labels to focus on (generic model only). Uses Open Images Dataset labels.'
        ),
    ] = None
    focus_framing: Annotated[
        FocusFraming | None,
        Field(
            description='Specific to `people` model. Defines which part of the subject to frame. Default is `face`, which is why `people` alone replaces the deprecated `face` model.'
        ),
    ] = None
    focus_zoom: Annotated[
        FocusZoom | None,
        Field(
            description='Specific to `people` model. Controls the zoom level applied. Default is `max`.'
        ),
    ] = None
    focus_target: Annotated[
        FocusTarget | None,
        Field(
            description='Specific to `people` model. When multiple subjects are detected, defines which one to target. Default is `all`.'
        ),
    ] = None


class Model3(Enum):
    """
    Model used for generation. Default is `nano-banana-2`.
    Allowed `ratio` and `quality` values depend on the selected model — see the
    [Text to Image & Inpainting guide](https://developers.abyssale.com/rest-api/generation/element-properties/image#text-to-image-inpainting) for the full table.

    """

    gemini_3_pro = 'gemini-3-pro'
    gemini_2_5_flash = 'gemini-2.5-flash'
    gemini_3_1_flash = 'gemini-3.1-flash'
    kling_image_o3 = 'kling-image-o3'
    wan_2_7 = 'wan-2.7'
    gpt_image_1_5 = 'gpt-image-1.5'
    flux_2_pro = 'flux-2-pro'
    qwen_2511 = 'qwen-2511'
    nano_banana = 'nano-banana'
    nano_banana_2 = 'nano-banana-2'
    nano_banana_pro = 'nano-banana-pro'
    seedream_4_5 = 'seedream-4.5'
    gpt_image_2 = 'gpt-image-2'
    grok_imagine = 'grok-imagine'
    flux_2_klein_9b = 'flux-2-klein-9b'


class TextToImageProperties(BaseModel):
    """
    Settings for AI image generation or inpainting.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    prompt: Annotated[
        str,
        Field(
            description='Description of the image to generate, or of the edit to apply when `inpaint_images` is provided. **At least 3 whitespace-separated words** — a shorter prompt is rejected.',
            examples=[
                'A sleek, modern glass villa situated in the middle of a minimalist lavender field.'
            ],
        ),
    ]
    model: Annotated[
        Model3 | None,
        Field(
            description='Model used for generation. Default is `nano-banana-2`.\nAllowed `ratio` and `quality` values depend on the selected model — see the\n[Text to Image & Inpainting guide](https://developers.abyssale.com/rest-api/generation/element-properties/image#text-to-image-inpainting) for the full table.\n'
        ),
    ] = None
    ratio: Annotated[
        str | None,
        Field(
            description='Aspect ratio or size of the output (e.g. `16:9`, `square_hd`, `1024x1024`).\nAllowed values depend on the selected `model` — see the\n[Text to Image & Inpainting guide](https://developers.abyssale.com/rest-api/generation/element-properties/image#text-to-image-inpainting).\n'
        ),
    ] = None
    quality: Annotated[
        str | None,
        Field(
            description='Output quality/resolution (e.g. `1K`, `high`). Only supported by some models — see the\n[Text to Image & Inpainting guide](https://developers.abyssale.com/rest-api/generation/element-properties/image#text-to-image-inpainting).\nIgnored if the selected model does not support it.\n'
        ),
    ] = None
    inpaint_images: Annotated[
        list[AnyUrl] | None,
        Field(
            description='URL(s) of the image(s) to edit. When provided, switches generation to inpainting mode instead of pure text-to-image.'
        ),
    ] = None


class AudioElement(BaseModel):
    """
    Audio layer element. Only available for animated designs with MP4 output.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    audio_url: Annotated[
        AnyUrl | None,
        Field(
            description='**HTTP(s) URL of the audio file.**\n\nIt must be a publicly accessible link with a filesize of 25 MB maximum.\n\nSupported files: mp3, wav\n'
        ),
    ] = None
    audio_encoded: Annotated[
        str | None,
        Field(
            description='**Base64-encoded audio**, as a data URI or raw base64. Ignored when `audio_url` is given. Same 25 MB ceiling.'
        ),
    ] = None
    max_volume: Annotated[
        float | None,
        Field(
            description='Volume level. 1 = default volume, 0.5 = half volume, 0 = silent. Default is 1.',
            examples=[1],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    speed: Annotated[
        float | None,
        Field(
            description='Playback speed. 1 = 100%, 0.5 = 50%. Default is 1.',
            examples=[1],
            ge=0.25,
            le=2.0,
        ),
    ] = None


class DuplicationRequest(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    duplication_request_id: Annotated[
        UUID,
        Field(
            description='Unique identifier for tracking the duplication process',
            examples=['40c32a4e-4869-11f0-96f2-0a00d9eb8f78'],
        ),
    ]
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class Status(Enum):
    """
    Current status of the duplication request
    """

    INIT = 'INIT'
    IN_PROGRESS = 'IN_PROGRESS'
    ERROR = 'ERROR'
    COMPLETED = 'COMPLETED'


class ProjectSummary(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID,
        Field(
            description='Unique identifier of the project',
            examples=['d59adee9-4867-11f0-96f2-0a00d9eb8f78'],
        ),
    ]
    name: Annotated[
        str, Field(description='Name of the project', examples=['HTML5 Tests'])
    ]
    created_at_ts: Annotated[
        int,
        Field(
            description='Unix timestamp when the project was created',
            examples=[1749827125],
        ),
    ]
    category_name: Annotated[
        str | None,
        Field(
            deprecated=True,
            description='Deprecated alias of `name` — the same string, under the old noun. It does **not** describe a category the project belongs to: a project has no parent category. Returned by the `GET /projects` listing only; the `POST /projects` read-back omits it. Read `name`.',
            examples=['HTML5 Tests'],
        ),
    ] = None


class DuplicatedDesign(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    original_design_id: Annotated[
        UUID,
        Field(
            description='ID of the original workspace template',
            examples=['0c967bd0-4137-4690-ad70-249aa021c68b'],
        ),
    ]
    target_design_id: Annotated[
        UUID,
        Field(
            description='ID of the newly created template in your project',
            examples=['afb1a61a-6c50-4bc3-a49b-3381822d4e81'],
        ),
    ]
    target_design_name: Annotated[
        str,
        Field(description='Name of the duplicated template', examples=['Design Name']),
    ]


class Error(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    template_format_name: Annotated[
        str | None, Field(description='The format name that failed to generate')
    ] = None
    reason: Annotated[str | None, Field(description='The error reason')] = None


class DynamicImageFormat(BaseModel):
    """
    One format of a dynamic image. Deliberately **not** `DesignFormat`: this endpoint is `static`-only (anything else answers `400 template_not_static`), so it never carries `preview_url` or the printer settings, and every field below is always present.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str,
        Field(
            description='Identifier (name) of the format.', examples=['facebook-post']
        ),
    ]
    uid: Annotated[
        UUID,
        Field(
            description='Unique UUID of the format — the last path segment of `dynamic_image_url`.',
            examples=['9b57d65e-eb2c-4a74-a51e-4482917c248a'],
        ),
    ]
    width: Annotated[float, Field(examples=[1200])]
    height: Annotated[float, Field(examples=[1200])]
    unit: Annotated[
        str,
        Field(
            description='Always `px` here; a dynamic image is only available on static designs.',
            examples=['px'],
        ),
    ]
    dynamic_image_url: Annotated[
        AnyUrl,
        Field(
            description='The dynamic image URL for this format.',
            examples=[
                'https://img.abyssale.com/ecf1fe8c-5392-48c2-b6d2-665183a18fe5/9b57d65e-eb2c-4a74-a51e-4482917c248a'
            ],
        ),
    ]


class DynamicImageResponse(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[UUID, Field(description='Unique ID of the dynamic image')]
    design_id: Annotated[
        UUID, Field(description='Design ID associated with this dynamic image')
    ]
    formats: Annotated[
        list[DynamicImageFormat],
        Field(description='List of formats available for this dynamic image'),
    ]
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class FontWeight(Enum):
    """
    **Force a font weight**. *Example: 500*

    | Value | Corresponding name |
    |-----|-----|
    | 100   | Thin   |
    | 200   | Extra Light   |
    | 300   | Light   |
    | 400   | Regular   |
    | 500   | Medium   |
    | 600   | Semi Bold   |
    | 700   | Bold   |
    | 800   | Extra Bold   |
    | 900   | Black   |

    _If the font does not contain the given font weight, the nearest weight will be used._

    """

    number_100 = 100
    number_200 = 200
    number_300 = 300
    number_400 = 400
    number_500 = 500
    number_600 = 600
    number_700 = 700
    number_800 = 800
    number_900 = 900


class TextAlignment(Enum):
    """
    **The text alignment.** *Example: left*

    __If given, the text position will be computed from the text bounding box defined within the design.__

    """

    top = 'top'
    middle = 'middle'
    bottom = 'bottom'
    left = 'left'
    center = 'center'
    right = 'right'
    top_left = 'top left'
    top_center = 'top center'
    top_right = 'top right'
    middle_left = 'middle left'
    middle_center = 'middle center'
    middle_right = 'middle right'
    bottom_left = 'bottom left'
    bottom_right = 'bottom right'
    bottom_center = 'bottom center'
    top_custom = 'top custom'
    middle_custom = 'middle custom'
    bottom_custom = 'bottom custom'
    custom_left = 'custom left'
    custom_center = 'custom center'
    custom_right = 'custom right'
    custom_custom = 'custom custom'


class TextTransform(Enum):
    """
    **Text transformation style.** Force the text to be transformed to one of the following options: - `uppercase`: All letters become uppercase (e.g., `EXAMPLE`) - `lowercase`: All letters become lowercase (e.g., `example`) - `titlecase`: The first letter of each word is capitalized (e.g., `Example Text`) - `capitalize`: Only the first letter of the entire text is capitalized (e.g., `Example text`) - `none`: No transformation — send it to clear one set on the design

    """

    none = 'none'
    uppercase = 'uppercase'
    lowercase = 'lowercase'
    titlecase = 'titlecase'
    capitalize = 'capitalize'


class FittingType(Enum):
    """
    **Defines the way the image will be inserted in the bounding box**

    Two properties are supported:

    - `cover`: It will force the image to fill entirely the area without changing the aspect ratio (hence the image will be cropped if its ratio is not the same as the container)
    - `fill`: The image will be displayed entirely within the box.

    """

    cover = 'cover'
    fill = 'fill'


class Alignment(Enum):
    """
    **The image alignment.** *Example: left*. A `custom` component resolves to the **centre** of that axis: `custom custom`, `custom center` and `middle custom` all place at the box centre, while `custom left` is the middle of the left edge. It is the value the editor stores for a hand-positioned layer, not a way to preserve one.
    """

    top = 'top'
    middle = 'middle'
    bottom = 'bottom'
    left = 'left'
    center = 'center'
    right = 'right'
    top_left = 'top left'
    top_center = 'top center'
    top_right = 'top right'
    middle_left = 'middle left'
    middle_center = 'middle center'
    middle_right = 'middle right'
    bottom_left = 'bottom left'
    bottom_right = 'bottom right'
    bottom_center = 'bottom center'
    top_custom = 'top custom'
    middle_custom = 'middle custom'
    bottom_custom = 'bottom custom'
    custom_left = 'custom left'
    custom_center = 'custom center'
    custom_right = 'custom right'
    custom_custom = 'custom custom'


class MaskName(Enum):
    """
    **A mask can be added to the image**.

    8 masks are available. Only `rounded_corners` takes a `mask_properties`; the other
    seven are shapes with no additional property.

    - `circle`: The image will be rendered as a circle.
    - `rounded_corners`: Corners of the image will be rounded. It requires another property: `mask_properties`.
    - `blob`: The image will be rendered as a blob.
    - `squircle`: The image will be rendered as a squircle.
    - `pentagon`: The image will be rendered as a pentagon.
    - `hexagon`: The image will be rendered as a hexagon.
    - `parallelogram`: The image will be rendered as a parallelogram.
    - `window`: The image will be rendered as a window (an arch — flat base, rounded top).

    """

    circle = 'circle'
    rounded_corners = 'rounded_corners'
    blob = 'blob'
    squircle = 'squircle'
    pentagon = 'pentagon'
    hexagon = 'hexagon'
    parallelogram = 'parallelogram'
    window = 'window'


class Radius1(RootModel[float]):
    root: Annotated[float, Field(ge=0.0)]


class Radius2(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    tl: Annotated[float | None, Field(ge=0.0)] = None
    tr: Annotated[float | None, Field(ge=0.0)] = None
    br: Annotated[float | None, Field(ge=0.0)] = None
    bl: Annotated[float | None, Field(ge=0.0)] = None


class MaskProperties(BaseModel):
    """
    **When the rounded_corners mask is applied, this parameter allows to define the radius**.

    Two types of radius is supported:
    - A number, that allows to define all corners' radius at once. *Example: {"radius": 20}*
    - An object, that allows to customize each corner's radius individually.
      4 properties are available: (`tl` = top left, `tr` = top right, `br` = bottom right, `bl` = bottom left)

    *Example: {"radius": {
      "tl": 0,
      "tr": 56,
      "br": 56,
      "bl": 20
    }}*

    """

    model_config = ConfigDict(
        extra='allow',
    )
    radius: Radius1 | Radius2 | None = None
    skew_y: Annotated[
        float | None,
        Field(description='Slant the mask on the y axis.', ge=-22.0, le=22.0),
    ] = None


class FilterName(Enum):
    """
    **A filter can be added to the image.** *Example: grayscale*

    2 filters are available:
    - `grayscale`: It converts the input image to grayscale. No additional property is available.
    - `duotone`: Apply a duotone filter to the image. It requires another property: `filter_properties`

    """

    grayscale = 'grayscale'
    duotone = 'duotone'


class Name(Enum):
    blue_green = 'blue_green'
    blue_orange = 'blue_orange'
    deep_green_light_green = 'deep_green_light_green'
    BrightRed_light_yellow = 'BrightRed_light_yellow'
    brown_pale_green = 'brown_pale_green'
    brown_beige = 'brown_beige'
    deep_blue_green = 'deep_blue_green'
    deep_blue_red = 'deep_blue_red'
    deep_purple_orange = 'deep_purple_orange'
    deep_purple_beige = 'deep_purple_beige'
    deep_purple_pale_green = 'deep_purple_pale_green'
    deep_blue_pale_green = 'deep_blue_pale_green'


class FilterProperties(BaseModel):
    """
    **When the duotone mask is applied, this parameter allows to define the duotone filter to apply**.
    *Example: { "name": "blue_orange" }*

    """

    model_config = ConfigDict(
        extra='allow',
    )
    name: Name | None = None


class PatternName(Enum):
    """
    **A pattern can be added to the shape**.

    (List of patterns)[]

    """

    bubbles = 'bubbles'
    cage = 'cage'
    cross = 'cross'
    doubleCircle = 'doubleCircle'
    drops = 'drops'
    parkay = 'parkay'
    pills = 'pills'
    plus = 'plus'
    star = 'star'
    ticTac = 'ticTac'
    ticTacFilled = 'ticTacFilled'
    triangle = 'triangle'
    wiggle = 'wiggle'


class OverlayDirection(Enum):
    """
    Direction of the overlay.
    """

    horizontal = 'horizontal'
    vertical = 'vertical'
    diagonal = 'diagonal'


class IllustrationProperties(BaseModel):
    """
    **Only `Undraw`, `feather` and `material icons` support `illustration_properties`.**

    """

    model_config = ConfigDict(
        extra='allow',
    )
    primary_color: Annotated[
        str | None,
        Field(
            description='**Color of the illustration** \n\n*A 6 or 8 hexadecimal shape color starting with a **#**.** *Example: #EAEAEA or #FF00FF55_*\n'
        ),
    ] = None


class ErrorResponse(BaseModel):
    """
    **The error shape for this entire API.** Every failure, on every endpoint, at every
    status, is this object — there is no second envelope to detect and no per-endpoint
    variant. `id` and `message` are always present; `errors` appears only when there is
    field-level detail to give.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    message: Annotated[
        str,
        Field(
            description="Human-readable error message. Prose, not a contract — branch on `id`, never on this.\n\nIt is meant to stand on its own, so when the failure comes down to a SINGLE problem\nthe message is that problem's own text prefixed with its `path`\n(`name: Missing data for required field.`) — you do not have to read `errors` to\nlearn which field was rejected. When several problems disagree it falls back to a\ngeneric sentence and `errors` carries the detail.\n"
        ),
    ]
    id: Annotated[
        str,
        Field(
            description='Machine-readable error code. Branch on this rather than on `message`, which is prose\nand may change. **Present on every error this API returns**, on every endpoint, at\nevery status — there is no second error shape to detect.\n\nWhen `errors` is present, `id` is the response-level code: the shared code if every\nentry agrees, otherwise `invalid_payload`, meaning "read `errors`".\n\nCodes are added over time. Treat one you do not recognise as generic and fall back to\n`message`; that keeps a new code from being a breaking change.\n\nThis covers errors the generation pipeline raises downstream and this API relays:\nthey carry no code of their own, so one is derived (`format_not_found`,\n`template_not_found`, `invalid_payload`, …) and a refusal that matches none of the\nknown cases is reported as `cannot_build_banner` rather than as a bare `message`.\n\nEvery value, as of this release. The list is generated from the API\'s code registry\nand covered by a test, so it cannot drift — but it is a snapshot, not a closed enum:\ntreat an unrecognised code as generic rather than as a parse failure.\n\nGrouped by **what you should do about it**, because that is the only thing that\nchanges your code. The grouping is guidance; the status line is what the response\nactually carries, and a few codes appear twice because they genuinely mean two things.\n\n**Fix the request, then send it again.** The payload, the parameters or the headers\nwere wrong: `invalid_payload`, `invalid_json`, `wrong_type`, `missing_required`,\n`unknown_field`, `unknown_enum_value`, `unknown_format_key`, `out_of_range`,\n`mutually_exclusive`, `conditional_dependency_missing`, `duplicate_format_name`,\n`duplicate_layer_name`, `reserved_format_name`, `unsupported_for_type`,\n`unknown_font`, `unreachable_src`, `invalid_query_param`, `invalid_filetype`,\n`invalid_design_type`, `template_not_static`, `more_than_one_format`,\n`missing_assets`, `not_round_trippable`, `unsupported_media_type`, `not_acceptable`,\n`method_not_allowed`.\n\n**Fix the identifier.** The request was well-formed, but named something that does\nnot exist or does not belong to this workspace: `template_not_found`,\n`format_not_found`, `visual_not_found`, `generation_request_not_found`,\n`duplication_request_not_found`, `workspace_template_not_found`, `project_not_found`,\n`not_related_to_same_template`, `not_related_to_same_format`, `not_found`,\n`endpoint_not_found`.\n\n**Too late.** The job finished, but its result is no longer kept (7 days):\n`generation_request_gone`, `duplication_request_gone`. Generate again, and store the\nresult this time rather than re-polling for it later.\n\n**Back off, then retry.** These two are the only ones worth a retry loop:\n`request_rate_limited`, `rate_limit_exceeded`.\n\n**Retrying never helps — something has to change first.** The plan or the credit\nbalance: `feature_not_in_plan`, `api_access_denied`. Note that `rate_limit_exceeded`\nlands here too when it means "not enough credits"; the message is what tells the two\napart, which is why both entries name it.\n\n**Authenticate.** `unauthorized` for a missing, unknown or revoked key;\n`api_access_denied` when the key is valid but the plan excludes API access. There is\nno 403 in this API.\n\n**The resource is in the wrong state for this call.** Read it back to find out which:\n`template_import_already_processed`, `project_already_exists`, `template_not_active`,\n`previous_secret_still_active`.\n\n**Valid request, unrenderable content.** The engine accepted the call and then\nrefused the artwork — most often text that cannot fit its layer:\n`cannot_build_banner`, `image_fetching_error`.\n\n**Ours, not yours.** Retry once; if it persists, send us the response:\n`internal_error`, `internal_server_error`.\n'
        ),
    ]
    errors: Annotated[
        list[Problem] | None,
        Field(
            description='Field-level detail. **Present only when there is some** — its absence means the error\nis not about a particular field, not that detail was withheld. When present it is\nalways a non-empty FLAT array of problem objects; it is never an object, never null\nand never empty.\n\nObject keys are dotted and array indices bracketed (`formats[0].layers`,\n`elements.root.background_color`), so one parser reads every API error.\n\nThis holds for detail produced downstream too: the generation engine reports its own\nfield errors in a different shape, and they are translated to this one before the\nresponse is written.\n\nEntries may carry keys beyond the three required ones (`expected`, `received`).\nIgnore ones you do not recognise — more may be added.\n',
            min_length=1,
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class Banner(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[UUID, Field(examples=['64238d01-d402-474b-8c2d-fbc957e9d290'])]
    version: Annotated[
        int | None,
        Field(
            description='Version number of the generated file — an integer counter, NOT the API version.\nA banner response reports this counter; the `vYYYY-MM-DD` stamp other responses carry\nnever appears here.\n',
            examples=[1],
        ),
    ] = None
    sharing_id: Annotated[
        UUID | None,
        Field(
            description='Identifier used for sharing this generated file.',
            examples=['5fcec999-2bfb-4dd7-ba38-2d9e16c49149'],
        ),
    ] = None
    file: File
    format: Format | None = None
    template: Annotated[
        DesignSummary | None,
        Field(description='The design this file was generated from.'),
    ] = None
    project: Annotated[
        Project | None,
        Field(description="The design's project — present when the design has one."),
    ] = None
    image: Annotated[
        Image | None,
        Field(
            deprecated=True,
            description='Deprecated — same information as `file.type` / `file.url`.',
        ),
    ] = None
    edit_url: Annotated[
        str | None,
        Field(
            description='Platform edit URL — only for visuals bookmarked or downloaded in the platform.'
        ),
    ] = None
    view_url: Annotated[
        str | None,
        Field(
            description='Platform view URL — only for visuals bookmarked or downloaded in the platform.'
        ),
    ] = None
    visual_status: Annotated[
        VisualStatus | None,
        Field(description='Present when the visual carries a review status.'),
    ] = None


class DesignElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str,
        Field(
            description='Layer name (`root` is a special element that allows to customize the image background color.)',
            examples=['element-name'],
        ),
    ]
    type: Annotated[
        Type4,
        Field(
            description="Layer type. `container` is the design's own root wrapper, not a layer you can author or override — skip it when walking the tree. `group` elements are injected only on the platform advanced view (`i=advanced`); a masked group reports `group` too, with a `mask` block. `code` is listed last because it is marginal: a custom HTML/JS layer that exists only on `animated` designs, read-only like `container` — it carries no customisable attributes, so it can never be targeted in a generation request.",
            examples=['text'],
        ),
    ]
    layout: Annotated[
        dict[str, ElementLayout] | None,
        Field(description="The element's box, **keyed by format name**."),
    ] = None
    layer_ids: Annotated[
        list[str] | None,
        Field(
            description='`group` layers only — the names of the layers this group contains.'
        ),
    ] = None
    hidden: Annotated[
        dict[str, bool] | None,
        Field(
            description='`group` layers only — computed visibility, keyed by format name.'
        ),
    ] = None
    locked: Annotated[
        dict[str, bool] | None,
        Field(
            description='`group` layers only — computed lock state, keyed by format name.'
        ),
    ] = None
    group: Annotated[
        dict[str, GroupLayout] | None,
        Field(
            description='`group` layers only — auto-layout settings, keyed by format name.'
        ),
    ] = None
    mask: Annotated[
        dict[str, GroupMask] | None,
        Field(
            description='Masked `group` layers only — the mask geometry, keyed by format name. Presence is a layer-level fact: a layer is a masked group in every format or in none.'
        ),
    ] = None
    animation: Annotated[
        Animation | None,
        Field(
            description='Animated designs only; present when the element carries timeline timing or tweens.\nAn injected `group` layer carries `start_at_s` / `end_at_s` only — never `tweens`.\n'
        ),
    ] = None
    attributes: Annotated[list[Attribute], Field(description='List of all attributes')]


class RootElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind the element.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)` _i.e. linear-gradient(0% 0% 100% 0%,0% #1a47ff 1,100% #b65151 1)_\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100. _i.e. cmyka(0,100,100,0,100)_\n',
            examples=['#FF0000'],
        ),
    ] = None


class Element11(AudioElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement11(AudioElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class TextElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    payload: Annotated[
        str | None,
        Field(
            description='**The text content**. *Example: Lorem Ipsum*\n\n- [How can I force specific line breaks?](https://developers.abyssale.com/image-generation-properties.html#color)\n- [How can I add decorations to specific parts of a text?](https://developers.abyssale.com/image-generation-properties.html#color)\n',
            max_length=10000,
            min_length=1,
        ),
    ] = None
    color: Annotated[
        str | None,
        Field(
            description='**The text color.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)`\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100.\n'
        ),
    ] = None
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind the element.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)` _i.e. linear-gradient(0% 0% 100% 0%,0% #1a47ff 1,100% #b65151 1)_\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100. _i.e. cmyka(0,100,100,0,100)_\n',
            examples=['#FF0000'],
        ),
    ] = None
    background_padding: Annotated[
        str | None,
        Field(
            description='**The padding of the background color around the text.** *Example: 10*\n\n_This parameter will only be used if a background color is defined._\n\n- String: Two numbers separated by a space: First number represents the vertical padding in pixels & the second the vertical padding. For instance: 0 10 : 0 as vertical padding & 10 as horizontal\n- Number: Paddings (Horizontal & vertical) in pixels. _i.e. 10_\n'
        ),
    ] = None
    font_size: Annotated[
        float | None, Field(description='**Font size in pixels** *Example: 20*', ge=1.0)
    ] = None
    font: Annotated[
        UUID | None,
        Field(
            description='**Force a specific font by ID**. *Example: 6156907e-33c5-11ea-9877-92672c1b8195*\n\nThe fonts list is available by calling the [GET /fonts](#tag/Fonts) API route.\n'
        ),
    ] = None
    font_weight: FontWeight | None = None
    line_height: Annotated[
        float | None,
        Field(
            description='**Force line height in percentage** *Example: 130*\n\n__This parameter is only applied when the text is a multiline one.__\n',
            ge=1.0,
        ),
    ] = None
    skew_y: Annotated[
        float | None,
        Field(
            description='**Slant text on the y axis** *Example: 20*', ge=-20.0, le=20.0
        ),
    ] = None
    alignment: TextAlignment | None = None
    stroke_width: Annotated[
        float | None,
        Field(
            description="**Width of the stroke** *Example: 10*. Text and button top out at 40; a shape layer accepts up to 60 (see `shapeStrokeWidth`). The design **import** allows up to 1000, so a design can hold a stroke this endpoint cannot reproduce — the import bound is the design's, this one is the override's.",
            ge=0.0,
            le=40.0,
        ),
    ] = None
    stroke_color: Annotated[
        str | None,
        Field(
            description="**Stroke Color. 6-8 digits Hexa color.**. *Example: #FF0000*\n\n__If your design does not contain any stroke, this color won't be visible__\n"
        ),
    ] = None
    text_transform: TextTransform | None = None
    auto_resize: Annotated[
        bool | None,
        Field(
            description='Automatically adjusts the text size to fit within its container. When true, `min_font_size` must also be defined.'
        ),
    ] = None
    min_font_size: Annotated[
        float | None,
        Field(
            description='Minimum font size allowed when `auto_resize` is enabled.',
            ge=0.0,
        ),
    ] = None
    max_lines: Annotated[
        float | None, Field(description='Maximum number of lines allowed.', ge=1.0)
    ] = None
    text_harmony: Annotated[
        bool | None,
        Field(
            description='Attempts to balance line lengths with a maximum variance of 20% between lines. Adjusts character spacing (±20), then reduces font size (up to -10px) if needed.'
        ),
    ] = None
    text_truncation: Annotated[
        bool | None,
        Field(
            description='If the text does not fit, it is truncated and an ellipsis (...) is appended.'
        ),
    ] = None
    side_border: Annotated[
        SideBorder | None,
        Field(
            description='Defines the side on which a border is rendered. Use `none` to disable an existing side border.'
        ),
    ] = None
    side_border_thickness: Annotated[
        float | None,
        Field(description='Thickness of the side border in pixels.', ge=0.0),
    ] = None
    side_border_color: Annotated[
        str | None,
        Field(
            description='Color of the side border. 6-8 digits hexadecimal or cmyka (for print).'
        ),
    ] = None
    side_border_rounded: Annotated[
        bool | None,
        Field(
            description='Whether the border corners are rounded (true) or square (false). Default is false.'
        ),
    ] = None
    side_border_padding: Annotated[
        float | None,
        Field(
            description='Distance in pixels between the text content and the side border. Default is 0.',
            ge=0.0,
        ),
    ] = None
    side_border_offset: Annotated[
        float | None,
        Field(
            description='Moves the border along the perpendicular axis. Positive and negative values shift in opposite directions. Default is 0.'
        ),
    ] = None
    side_border_spread: Annotated[
        float | None,
        Field(
            description='Extends the length of the border beyond the text bounding box by the specified number of pixels. Default is 0.',
            ge=0.0,
        ),
    ] = None


class ButtonElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    payload: Annotated[
        str | None,
        Field(
            description="**The button's label.** Same content rules as a text `payload`, but capped at 2 048\ncharacters rather than 10 000 — the validator enforces the two separately.\n",
            max_length=2048,
            min_length=1,
        ),
    ] = None
    color: Annotated[
        str | None,
        Field(
            description='**The text color.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)`\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100.\n'
        ),
    ] = None
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind the element.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)` _i.e. linear-gradient(0% 0% 100% 0%,0% #1a47ff 1,100% #b65151 1)_\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100. _i.e. cmyka(0,100,100,0,100)_\n',
            examples=['#FF0000'],
        ),
    ] = None
    background_padding: Annotated[
        str | None,
        Field(
            description='**The padding of the background color around the text.** *Example: 10*\n\n_This parameter will only be used if a background color is defined._\n\n- String: Two numbers separated by a space: First number represents the vertical padding in pixels & the second the vertical padding. For instance: 0 10 : 0 as vertical padding & 10 as horizontal\n- Number: Paddings (Horizontal & vertical) in pixels. _i.e. 10_\n'
        ),
    ] = None
    font_size: Annotated[
        float | None, Field(description='**Font size in pixels** *Example: 20*', ge=1.0)
    ] = None
    font: Annotated[
        UUID | None,
        Field(
            description='**Force a specific font by ID**. *Example: 6156907e-33c5-11ea-9877-92672c1b8195*\n\nThe fonts list is available by calling the [GET /fonts](#tag/Fonts) API route.\n'
        ),
    ] = None
    font_weight: FontWeight | None = None
    line_height: Annotated[
        float | None,
        Field(
            description='**Force line height in percentage** *Example: 130*\n\n__This parameter is only applied when the text is a multiline one.__\n',
            ge=1.0,
        ),
    ] = None
    text_transform: TextTransform | None = None
    alignment: Annotated[
        Alignment | None,
        Field(
            description='Placement of the **button box** — not of its label. A button keeps the two apart: this moves the box, `text_align` moves the label inside it.'
        ),
    ] = None
    text_align: Annotated[
        TextAlign | None,
        Field(
            description='Alignment of the **label** inside the button box. Default `center`. A button is the one layer type where these are two separate settings — on a `text` layer the alignment *is* the position.'
        ),
    ] = None
    stroke_color: Annotated[
        str | None,
        Field(
            description="**Stroke Color. 6-8 digits Hexa color.**. *Example: #FF0000*\n\n__If your design does not contain any stroke, this color won't be visible__\n"
        ),
    ] = None
    stroke_width: Annotated[
        float | None,
        Field(
            description="**Width of the stroke** *Example: 10*. Text and button top out at 40; a shape layer accepts up to 60 (see `shapeStrokeWidth`). The design **import** allows up to 1000, so a design can hold a stroke this endpoint cannot reproduce — the import bound is the design's, this one is the override's.",
            ge=0.0,
            le=40.0,
        ),
    ] = None
    min_font_size: Annotated[
        float | None,
        Field(
            description='Minimum font size allowed when `auto_resize` is enabled.',
            ge=0.0,
        ),
    ] = None
    auto_resize: Annotated[
        bool | None,
        Field(
            description='Automatically adjusts the label size to fit the button. When true, `min_font_size` must also be defined.'
        ),
    ] = None


class ImageElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    image_url: Annotated[
        AnyUrl | None,
        Field(
            description='**HTTP(s) URL of the image** *Example: https://www.abyssale.com/imge/abyssale_logo.png*\n\n__It must be publicly accessible and at most 20 MB__ (500 MB on `printer` and\n`printer_multipage` designs).\n\nSupported files: jpeg, jpg, png, webp, svg, gif, tiff, tif, avif\n'
        ),
    ] = None
    image_encoded: Annotated[
        str | None,
        Field(
            description='**Base64 encoded image as value.** *Example: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQE...*\n\n__If the image_url is given, this parameter will not be used.__\n'
        ),
    ] = None
    opacity: Annotated[
        float | None,
        Field(description='**Opacity of the image** *Example: 60*', ge=0.0, le=100.0),
    ] = None
    fitting_type: FittingType | None = None
    alignment: Alignment | None = None
    mask_name: MaskName | None = None
    mask_properties: MaskProperties | None = None
    filter_name: FilterName | None = None
    filter_properties: FilterProperties | None = None
    overlay_direction: OverlayDirection | None = None
    overlay_color_1: Annotated[
        str | None,
        Field(description='First color of the overlay. 6-8 Digits Hexa color.'),
    ] = None
    overlay_color_2: Annotated[
        str | None,
        Field(description='Second color of the overlay. 6-8 Digits Hexa color.'),
    ] = None
    remove_bg: Annotated[
        bool | None,
        Field(
            deprecated=True,
            description='Activates AI background removal when set to true.\n\n**Deprecated on this endpoint, and not recommended.** It works and existing\nintegrations keep working, but removing a background is an extra AI round-trip on\ntop of the render, and this endpoint is hard-capped at 10 seconds — a large or slow\nsource image can push the whole call past the cap and fail with\n`500 internal_server_error` instead of returning your asset. Use asynchronous\ngeneration, which has no such bound.\n',
        ),
    ] = None
    remove_bg_properties: Annotated[
        RemoveBgProperties | None,
        Field(
            deprecated=True,
            description='Additional settings for background removal. Deprecated here for the same reason as `remove_bg`.',
        ),
    ] = None
    auto_focus: Annotated[
        bool | None,
        Field(
            description='Activates AI-powered auto-focus to detect and focus on specified objects or people within the image.'
        ),
    ] = None
    auto_focus_properties: Annotated[
        AutoFocusProperties | None,
        Field(description='Additional settings for auto-focus.'),
    ] = None


class AsyncImageElement(BaseModel):
    """
    Image element properties available for asynchronous generation, including AI image generation, inpainting, and background removal model selection.
    """

    model_config = ConfigDict(
        extra='allow',
    )
    image_url: Annotated[
        AnyUrl | None,
        Field(
            description='**HTTP(s) URL of the image** *Example: https://www.abyssale.com/imge/abyssale_logo.png*\n\n__It must be publicly accessible and at most 20 MB__ (500 MB on `printer` and\n`printer_multipage` designs).\n\nSupported files: jpeg, jpg, png, webp, svg, gif, tiff, tif, avif\n'
        ),
    ] = None
    image_encoded: Annotated[
        str | None,
        Field(
            description='**Base64 encoded image as value.** *Example: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQE...*\n\n__If the image_url is given, this parameter will not be used.__\n'
        ),
    ] = None
    opacity: Annotated[
        float | None,
        Field(description='**Opacity of the image** *Example: 60*', ge=0.0, le=100.0),
    ] = None
    fitting_type: FittingType | None = None
    alignment: Alignment | None = None
    mask_name: MaskName | None = None
    mask_properties: MaskProperties | None = None
    filter_name: FilterName | None = None
    filter_properties: FilterProperties | None = None
    overlay_direction: OverlayDirection | None = None
    overlay_color_1: Annotated[
        str | None,
        Field(description='First color of the overlay. 6-8 Digits Hexa color.'),
    ] = None
    overlay_color_2: Annotated[
        str | None,
        Field(description='Second color of the overlay. 6-8 Digits Hexa color.'),
    ] = None
    remove_bg: Annotated[
        bool | None,
        Field(description='Activates AI background removal when set to true.'),
    ] = None
    remove_bg_properties: Annotated[
        RemoveBgProperties1 | None,
        Field(description='Additional settings for background removal.'),
    ] = None
    auto_focus: Annotated[
        bool | None,
        Field(
            description='Activates AI-powered auto-focus to detect and focus on specified objects or people within the image.'
        ),
    ] = None
    auto_focus_properties: Annotated[
        AutoFocusProperties1 | None,
        Field(description='Additional settings for auto-focus.'),
    ] = None
    text_to_image: Annotated[
        bool | str | None,
        Field(
            description='Activates AI image generation (text-to-image) or AI-assisted image editing (inpainting).\nIf `image_url` (except default image) or `image_encoded` is provided, this property is ignored.\n\n`true` uses `text_to_image_properties`. As a shorthand you may instead pass the prompt\n**as a string** — optionally `"prompt,url1[,url2]"` to supply inpainting sources — which\nis expanded into `text_to_image_properties` before validation.\n'
        ),
    ] = None
    text_to_image_properties: TextToImageProperties | None = None


class LogoElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    image_url: Annotated[
        AnyUrl | None,
        Field(
            description='**HTTP(s) URL of the image** *Example: https://www.abyssale.com/imge/abyssale_logo.png*\n\n__It must be publicly accessible and at most 20 MB__ (500 MB on `printer` and\n`printer_multipage` designs).\n\nSupported files: jpeg, jpg, png, webp, svg, gif, tiff, tif, avif\n'
        ),
    ] = None
    image_encoded: Annotated[
        str | None,
        Field(
            description='**Base64 encoded image as value.** *Example: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQE...*\n\n__If the image_url is given, this parameter will not be used.__\n'
        ),
    ] = None
    alignment: Alignment | None = None


class ShapeElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind the element.**\n\n3 filling modes are available:\n- `Monochrome`: 6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n- `Linear Gradient`: `linear-gradient(x1% y1% x2% y2%,offset1% #color1 opacity1,offset2% #color2 opacity2)` _i.e. linear-gradient(0% 0% 100% 0%,0% #1a47ff 1,100% #b65151 1)_\n- `Cmyka` (print only): `cmyka(c,m,y,k)` or `cmyka(c,m,y,k,alpha)` where each value is 0–100. _i.e. cmyka(0,100,100,0,100)_\n',
            examples=['#FF0000'],
        ),
    ] = None
    pattern_name: PatternName | None = None
    pattern_color: Annotated[
        str | None,
        Field(
            description='**A 6 or 8 hexadecimal shape color starting with a `#`.** *Example: #EAEAEA or #FF00FF55*\n\n_If no pattern is applied to the shape, this property will not change anything._\n',
            examples=['#EAEAEA'],
        ),
    ] = None
    stroke_width: Annotated[
        float | None,
        Field(
            description="**Width of the shape's stroke** *Example: 10*. The design **import** allows up to 1000 — see `strokeWidth`.",
            ge=0.0,
            le=60.0,
        ),
    ] = None
    stroke_color: Annotated[
        str | None,
        Field(
            description="**Stroke Color. 6-8 digits Hexa color.**. *Example: #FF0000*\n\n__If your design does not contain any stroke, this color won't be visible__\n"
        ),
    ] = None


class RatingElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    rating_score: Annotated[
        float | None,
        Field(
            description='**Score of the rating on a scale of 100.** *Example: 50*\n\n_For instance, as rating is displayed as five-stars, 50 will give a 2.5/5 score._  \n',
            ge=0.0,
            le=100.0,
        ),
    ] = None
    star_dimension: Annotated[
        float | None,
        Field(
            description='**Size in pixels of one star.** *Example: 100*. The design **import** requires at least 4, so this endpoint accepts smaller stars than a design can be imported with.',
            gt=0.0,
            le=400.0,
        ),
    ] = None
    star_margin: Annotated[
        float | None,
        Field(
            description='**Margins in pixels between stars.** *Example: 60*',
            ge=0.0,
            le=100.0,
        ),
    ] = None
    star_color: Annotated[
        str | None,
        Field(
            description='**The color of the filled stars.**\n\n6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n'
        ),
    ] = None
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind all the stars.**\n\n6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n'
        ),
    ] = None


class IllustrationElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    illustration_type: Annotated[
        str | None,
        Field(
            description='**The illustration library the illustration name is looked up in.** The public libraries are `undraw`, `feather`, `twemoji` and `material_icons`.\nLeft as a free string rather than an enum on purpose: some workspaces have private libraries of their own, and an enum would make a generated client reject a value their API accepts.',
            examples=['undraw'],
        ),
    ] = None
    illustration_file: Annotated[
        str | None, Field(description='**The illustration name.**.')
    ] = None
    illustration_properties: IllustrationProperties | None = None
    alignment: Alignment | None = None
    opacity: Annotated[
        float | None,
        Field(description='**Opacity of the image** *Example: 60*', ge=0.0, le=100.0),
    ] = None


class QRCodeElement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    background_color: Annotated[
        str | None,
        Field(
            description='**The background color displayed behind the qrcode.**\n\n6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n'
        ),
    ] = None
    foreground_color: Annotated[
        str | None,
        Field(
            description='**The color of the qrcode (of all squares).**\n\n6 or 8 hexadecimal colors starting with a **#**. _i.e. #EAEAEA or #FF00FF55_\n'
        ),
    ] = None
    payload: Annotated[
        str | None,
        Field(
            description='**The content of the qrcode. i.e. Lorem Ipsum**\n\nThis content will be displayed once the QR Code is scanned.\n'
        ),
    ] = None
    image_url: Annotated[
        str | None,
        Field(
            description='**HTTP(s) URL of the icon displayed in the middle of the QR Code** *Example: https://www.abyssale.com/imge/abyssale_logo.png*\n\n__It must be a public accessible link and have a filesize of 10 mo maximum.__\n\nSupported files: jpeg, png, webp\n'
        ),
    ] = None
    hide_icon: Annotated[
        bool | None,
        Field(
            description='`true`, `false`. If true it hides the icon in the middle of the QRCode.'
        ),
    ] = None


class VideoElement(BaseModel):
    """
    This element is only available for animated design
    """

    model_config = ConfigDict(
        extra='allow',
    )
    video_url: Annotated[
        AnyUrl | None,
        Field(
            description='**HTTP(s) URL of the video** *Example: https://www.abyssale.com/imge/this_an_example.mp4*\n\n__It must be a public accessible link and have a filesize of 100 mo maximum.__\n\nSupported files: mp4\n'
        ),
    ] = None
    audio_muted: Annotated[
        float | None,
        Field(
            description="Mute the video's audio track. `1` mutes it, `0` keeps it; values in between scale it. Default `0`. **A number, not a boolean** — `true`/`false` answer `400 invalid_payload`. The import spells this `muted` and takes a boolean; a design read returns `video_muted` / `audio_muted`, also booleans.",
            examples=[1],
            ge=0.0,
            le=1.0,
        ),
    ] = None


class DuplicationRequestStatus(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    request_id: Annotated[
        UUID,
        Field(
            description='Unique identifier of the duplication request',
            examples=['40c32a4e-4869-11f0-96f2-0a00d9eb8f78'],
        ),
    ]
    status: Annotated[
        Status,
        Field(
            description='Current status of the duplication request',
            examples=['COMPLETED'],
        ),
    ]
    created_at_ts: Annotated[
        int,
        Field(
            description='Unix timestamp when the duplication request was created',
            examples=[1749827734],
        ),
    ]
    completed_at_ts: Annotated[
        int | None,
        Field(
            description='Unix timestamp when the duplication was completed (null if not completed)',
            examples=[1749827736],
        ),
    ] = None
    errored_at_ts: Annotated[
        int | None,
        Field(
            description='Unix timestamp when the duplication failed (null if not failed)',
            examples=[None],
        ),
    ] = None
    target_project: ProjectSummary
    designs: Annotated[
        list[DuplicatedDesign],
        Field(description='List of duplicated designs (empty if not completed)'),
    ]
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class GenerationRequestStatus(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        UUID, Field(description='Unique identifier of the generation request')
    ]
    is_finalized: Annotated[
        bool,
        Field(
            description='Whether the generation is complete. `false` when the request returns 202, `true` when it returns 200.'
        ),
    ]
    banners: Annotated[
        list[Banner],
        Field(description='List of generated files (populated once finalized)'),
    ]
    errors: Annotated[
        list[Error] | None,
        Field(description='Per-format errors, if any occurred during generation'),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The API version that produced this response, named by release date (`vYYYY-MM-DD`).\nStamped as a top-level field on JSON object bodies, success and error alike, so a client\ncan always tell which contract answered. There is no version-selection parameter — a\nsingle version is maintained at a time.\n\nTwo kinds of body are **not** stamped. Array bodies (the listings) carry no envelope. And\na body that already has a `version` key of its own is left alone — which in practice means\n`Banner`, whose `version` is the generated file's integer counter. So `GET\n/banners/{bannerId}` and the synchronous generate are the two responses that do not tell\nyou which contract answered.\n\nThe value changes when a new version is released. Match the `vYYYY-MM-DD` shape rather than\npinning today's literal, or your client breaks on the next release.\n",
            examples=['v2026-08-21'],
            pattern='^v\\d{4}-\\d{2}-\\d{2}$',
        ),
    ] = None


class Element2(TextElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element3(ImageElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element4(ButtonElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element5(LogoElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element6(ShapeElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element7(RatingElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element8(IllustrationElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element9(QRCodeElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class Element10(VideoElement, Element1):
    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement2(TextElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement3(AsyncImageElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement4(ButtonElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement5(LogoElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement6(ShapeElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement7(RatingElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement8(IllustrationElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement9(QRCodeElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class AsyncElement10(VideoElement, AsyncElement1):
    """
    Same as `Element`, but its image element also exposes AI generation properties (`text_to_image`, inpainting, background removal model) that are only available for asynchronous generation.
    """

    model_config = ConfigDict(
        extra='allow',
    )


class Elements(
    RootModel[
        dict[
            str,
            RootElement
            | VideoElement
            | AudioElement
            | Element2
            | Element3
            | Element4
            | Element5
            | Element6
            | Element7
            | Element8
            | Element9
            | Element10
            | Element11
            | dict[str, str],
        ]
    ]
):
    """
    A `dictionary` containing all elements with properties you would like to override from
    the default design (keys correspond to layer names). The reserved key `vars` is not a
    layer: it carries the design-wide text variable values.

    **Unknown names are accepted, not rejected — and this is the one thing to know before
    you generate this object programmatically.** The API does not check element names or
    property names against the design: a key naming a layer that does not exist, or a
    property that layer does not have, passes validation and simply does not change the
    output. There is no error and no warning, so a typo shows up as an asset that renders
    with the design's saved content instead of yours.

    This leniency is deliberate and long-standing — live integrations depend on it, so it
    will not be tightened. Two consequences worth designing for:

    - **Check names against `GET /designs/{designId}`** rather than against a `400`. That
      response lists every element and every attribute it accepts.
    - **Offline schema validation cannot help either.** The branches below overlap by design
      (an element payload carries no type field — the layer's type comes from the design), so
      a generic JSON-Schema validator accepts any object here.

    """

    root: dict[
        str,
        RootElement
        | VideoElement
        | AudioElement
        | Element2
        | Element3
        | Element4
        | Element5
        | Element6
        | Element7
        | Element8
        | Element9
        | Element10
        | Element11
        | dict[str, str],
    ]


class Pages(
    RootModel[
        dict[
            str,
            dict[
                str,
                RootElement
                | VideoElement
                | AudioElement
                | AsyncElement2
                | AsyncElement3
                | AsyncElement4
                | AsyncElement5
                | AsyncElement6
                | AsyncElement7
                | AsyncElement8
                | AsyncElement9
                | AsyncElement10
                | AsyncElement11
                | dict[str, str],
            ],
        ]
    ]
):
    """
    Per-page element overrides, keyed by page identifier (`page_1 … page_N`). Each value is a dictionary of element overrides for that page, in the same shape as `elements` on every other generation endpoint — `root` plus any layer of that page, keyed by layer name. This endpoint is asynchronous, so its image layers accept the AI properties too.
    """

    root: dict[
        str,
        dict[
            str,
            RootElement
            | VideoElement
            | AudioElement
            | AsyncElement2
            | AsyncElement3
            | AsyncElement4
            | AsyncElement5
            | AsyncElement6
            | AsyncElement7
            | AsyncElement8
            | AsyncElement9
            | AsyncElement10
            | AsyncElement11
            | dict[str, str],
        ],
    ]
