from __future__ import annotations

import pytest

from abyssale import Abyssale, AsyncAbyssale

BASE_URL = "https://api.test.abyssale.com"
API_KEY = "test-key"


class FakeClock:
    """A clock that only moves when something sleeps.

    The real schedule still runs — every delay is computed by the real code — but time passes in
    jumps, so a test can exercise the 30-minute poll deadline in milliseconds. Without this, a
    poll loop whose sleeps are stubbed out spins against a real deadline for real seconds.
    """

    def __init__(self) -> None:
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Stub out every wait in the SDK and drive :class:`FakeClock` from it."""
    import abyssale._async_client as async_client
    import abyssale._client as client
    import abyssale._polling as polling

    fake = FakeClock()
    monkeypatch.setattr(polling.time, "monotonic", lambda: fake.now)
    monkeypatch.setattr(client.time, "sleep", fake.advance)

    async def _advance(seconds: float) -> None:
        fake.advance(seconds)

    monkeypatch.setattr(async_client.asyncio, "sleep", _advance)
    return fake


@pytest.fixture
def client() -> Abyssale:
    with Abyssale(api_key=API_KEY, base_url=BASE_URL) as instance:
        yield instance


@pytest.fixture
async def async_client() -> AsyncAbyssale:
    async with AsyncAbyssale(api_key=API_KEY, base_url=BASE_URL) as instance:
        yield instance


def error_body(
    error_id: str, message: str = "nope", errors: list[dict[str, object]] | None = None
) -> dict[str, object]:
    """The one error envelope the API answers with, at every status, on every endpoint."""
    body: dict[str, object] = {"id": error_id, "message": message}
    if errors is not None:
        body["errors"] = errors
    return body
