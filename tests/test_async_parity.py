"""The async client is a hand-written mirror of the sync one, so something has to hold the mirror.

These are reflection tests: they fail when a method is added to one client and not the other, or
when the two disagree about an argument name. A per-method test cannot do that — it can only check
the methods someone remembered to write it for.
"""

from __future__ import annotations

import inspect

import pytest

from abyssale import Abyssale, AsyncAbyssale


def public_methods(cls: type) -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(cls, inspect.isfunction)
        if not name.startswith("_") and name not in {"close", "aclose"}
    }


SYNC_METHODS = public_methods(Abyssale)
ASYNC_METHODS = public_methods(AsyncAbyssale)


def test_the_two_clients_expose_the_same_methods() -> None:
    assert SYNC_METHODS == ASYNC_METHODS


def test_the_surface_is_the_eighteen_endpoints_plus_two_helpers() -> None:
    # Pinned so that adding an endpoint is a deliberate act, in both clients and in the docs.
    assert SYNC_METHODS == {
        "verify_api_key",
        "list_designs",
        "get_design",
        "get_design_format",
        "generate_image",
        "generate_multi_format_media",
        "generate_multipage_pdf",
        "get_generation_request",
        "get_file",
        "list_fonts",
        "list_projects",
        "create_project",
        "export_banners",
        "create_dynamic_image_url",
        "list_workspace_templates",
        "list_workspace_template_categories",
        "duplicate_workspace_template",
        "get_duplication_request",
        "wait_for_generation_request",
        "wait_for_duplication_request",
    }


@pytest.mark.parametrize("name", sorted(SYNC_METHODS))
def test_signatures_match(name: str) -> None:
    sync = inspect.signature(getattr(Abyssale, name))
    async_ = inspect.signature(getattr(AsyncAbyssale, name))
    assert list(sync.parameters) == list(async_.parameters)
    for parameter in sync.parameters:
        assert sync.parameters[parameter].default == async_.parameters[parameter].default
        assert sync.parameters[parameter].kind == async_.parameters[parameter].kind


@pytest.mark.parametrize("name", sorted(ASYNC_METHODS))
def test_every_async_method_is_actually_a_coroutine(name: str) -> None:
    assert inspect.iscoroutinefunction(getattr(AsyncAbyssale, name))


@pytest.mark.parametrize("name", sorted(SYNC_METHODS))
def test_every_method_is_documented(name: str) -> None:
    # The docstring is the IDE-visible reference for this SDK; the docs site is one click further
    # away than the developer already is.
    assert (getattr(Abyssale, name).__doc__ or "").strip()
    assert (getattr(AsyncAbyssale, name).__doc__ or "").strip()


def test_the_constructors_agree() -> None:
    sync = inspect.signature(Abyssale.__init__)
    async_ = inspect.signature(AsyncAbyssale.__init__)
    assert list(sync.parameters) == list(async_.parameters)
