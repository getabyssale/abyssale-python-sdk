"""The SDK's own version — sent in the ``User-Agent`` and exported as ``abyssale.__version__``.

Kept in step with ``version`` in ``pyproject.toml`` by hand; there are two of them and a release
that bumps only one ships a User-Agent that lies.
"""

__version__ = "1.1.0"

#: The API version this SDK's models were generated from (`vYYYY-MM-DD`, the API's own scheme).
#:
#: The API stamps its version on every JSON object response, so comparing this against a live
#: response tells you whether the SDK is modelling the contract that answered. They are allowed to
#: differ — the API keeps one version at a time and moves on its own schedule — but a mismatch is
#: the first thing to check when a response does not parse the way the reference says it should.
__api_version__ = "v2026-08-21"
