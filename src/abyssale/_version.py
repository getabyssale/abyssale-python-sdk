"""The SDK's own version — sent in the ``User-Agent`` and exported as ``abyssale.__version__``.

Kept in step with ``version`` in ``pyproject.toml`` by hand; there are two of them and a release
that bumps only one ships a User-Agent that lies.
"""

__version__ = "1.0.0"
