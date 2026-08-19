"""Request construction and response handling, shared by the sync and async clients.

Everything here is pure: it takes an ``httpx.Response`` and gives back parsed data or an exception.
The two clients differ only in how they *send*, which is the one thing not in this module.
"""

from __future__ import annotations

from functools import cache
from typing import Any, TypeVar, get_args
from urllib.parse import quote

from pydantic import BaseModel, TypeAdapter, ValidationError

from ._errors import AbyssaleAPIError, error_from_response
from ._retry import retry_after_seconds

USER_AGENT = "abyssale-python"

M = TypeVar("M", bound=BaseModel)


def default_headers(api_key: str, version: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "accept": "application/json",
        "user-agent": f"{USER_AGENT}/{version}",
    }


def encode_path(template: str, **params: str) -> str:
    """Fill a path template, percent-encoding each segment.

    Ids are UUIDs and format specifiers can be arbitrary names ("summer sale 2026"), so a raw
    f-string would produce a malformed URL for a perfectly legal argument.
    """
    return template.format(**{k: quote(str(v), safe="") for k, v in params.items()})


def clean_query(query: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop unset filters so they are not sent as empty query parameters."""
    if not query:
        return None
    cleaned = {k: v for k, v in query.items() if v is not None}
    return cleaned or None


def parse_body(response: Any) -> Any:
    """The response body as JSON, or ``None`` when it has none or is not JSON.

    A 204 and a proxy's HTML error page both land here; neither should raise from the parse.
    """
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def raise_for_status(response: Any) -> Any:
    """Return the parsed body for a 2xx, or raise the matching :class:`AbyssaleAPIError`."""
    body = parse_body(response)
    if 200 <= response.status_code < 300:
        return body
    raise error_from_response(response.status_code, body, response, retry_after_seconds(response))


@cache
def _adapter(annotation: Any) -> TypeAdapter[Any]:
    return TypeAdapter(annotation)


def _coerce(annotation: Any, value: Any) -> Any:
    """Validate one field, degrading only as far as that field's own failure requires.

    Tried in order: validate the value as declared; if it is a list, validate each item so one bad
    entry does not cost the rest; if it is an object with a model type, rebuild it field by field;
    otherwise hand back the raw value.
    """
    try:
        return _adapter(annotation).validate_python(value)
    except (ValidationError, TypeError):
        pass

    if isinstance(value, list):
        args = get_args(annotation)
        item_type = args[0] if args else Any
        return [_coerce(item_type, item) for item in value]

    if isinstance(value, dict):
        for candidate in (annotation, *get_args(annotation)):
            if isinstance(candidate, type) and issubclass(candidate, BaseModel):
                return _tolerant(candidate, value)

    return value


def _tolerant(model: type[M], data: dict[str, Any]) -> M:
    """Rebuild a model whose payload does not validate, keeping every part that does.

    Failure stays **local to the field that failed**. The obvious implementation —
    ``model_construct(**data)`` — is a trap: it does not build nested models either, so one missing
    field anywhere turns the whole response into raw dictionaries and ``design.formats[0].id``
    silently becomes a ``KeyError`` on a dict. Which shape you get would then depend on the data,
    which is worse than either always validating or always raising.
    """
    values: dict[str, Any] = {}
    consumed = set()
    for name, field in model.model_fields.items():
        key = field.alias if field.alias and field.alias in data else name
        if key not in data:
            continue
        consumed.add(key)
        values[name] = _coerce(field.annotation, data[key])
    # `extra="allow"` keeps unknown fields readable; model_construct does not add them for us.
    extras = {k: v for k, v in data.items() if k not in consumed}
    built = model.model_construct(**values)
    for key, value in extras.items():
        setattr(built, key, value)
    return built


def validate(model: type[M], data: Any) -> M:
    """Parse a response body into a model.

    **Parsing never fails a successful response.** Two layers of tolerance, both deliberate:

    - Unknown fields are kept, not rejected (``extra="allow"`` on every model), so an API that has
      moved ahead of the published spec still parses and the new field is readable.
    - A field the spec calls required but the response omits does not raise. The spec is
      hand-maintained and the API is the authority: if it answered 200, the caller gets the data.
      Raising here would turn a documentation lag into an outage. The attribute is simply absent, so
      ``getattr(obj, "x", None)`` is the safe read for anything you are not sure of.

    The fallback is field-local: everything that validates is still a typed model, and only the
    part that failed degrades. This is not hypothetical — ``GET /designs/{id}?i=advanced`` returns
    `group` layers with no ``attributes``, which the spec marks required, and that is the one call
    the docs tell you to make to see group layers.

    This is the same leniency the API itself applies to element names, and for the same reason:
    live integrations depend on responses continuing to be readable.
    """
    if not isinstance(data, dict):
        raise AbyssaleAPIError(200, f"expected an object, got {type(data).__name__}", body=data)
    try:
        return model.model_validate(data)
    except ValidationError:
        return _tolerant(model, data)


def validate_list(model: type[M], data: Any) -> list[M]:
    if not isinstance(data, list):
        raise AbyssaleAPIError(200, f"expected a list, got {type(data).__name__}", body=data)
    return [validate(model, item) for item in data]
