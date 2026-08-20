"""The webhook signature verifier — the receiver's half of the contract.

Pure functions, so no ``respx`` and no client: `abyssale.webhooks` imports nothing that resolves an
API key, which is the point of it being a separate module (a receiver process holds no credential
that can spend credits). ``now`` is injected rather than patched because the module takes it as an
argument for exactly this reason.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from abyssale.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    signature_timestamp,
    verify_webhook_signature,
)

SECRET = "whsec_" + "a" * 64
OTHER_SECRET = "whsec_" + "b" * 64
BODY = b'{"event_type":"NEW_BANNER","banner_ids":["b1"]}'
NOW = 1787232676


def sign(secret: str, timestamp: int, body: bytes) -> str:
    return hmac.new(secret.encode(), f"v1:webhook:{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def header(secret: str = SECRET, timestamp: int = NOW, body: bytes = BODY) -> str:
    return f"t={timestamp},v1={sign(secret, timestamp, body)}"


def verify(value: str | None, secret: str = SECRET, body: bytes | str = BODY) -> bool:
    return verify_webhook_signature(body, value, secret, now=NOW)


class TestAGenuineDelivery:
    def test_it_verifies(self) -> None:
        assert verify(header()) is True

    def test_a_str_body_is_encoded_the_same_way_as_bytes(self) -> None:
        assert verify(header(), body=BODY.decode()) is True

    def test_a_non_ascii_body_verifies(self) -> None:
        """The signer hashes UTF-8 bytes; a receiver that re-encodes differently would not match."""
        body = '{"title":"Prix cassé — 49€"}'.encode()
        assert verify(f"t={NOW},v1={sign(SECRET, NOW, body)}", body=body) is True


class TestAForgedOrStaleDelivery:
    def test_a_body_altered_in_transit_fails(self) -> None:
        assert verify(header(), body=BODY.replace(b"b1", b"b2")) is False

    def test_another_workspaces_secret_fails(self) -> None:
        assert verify(header(OTHER_SECRET)) is False

    def test_a_delivery_older_than_the_tolerance_fails(self) -> None:
        assert verify(header(timestamp=NOW - DEFAULT_TOLERANCE_SECONDS - 1)) is False

    def test_the_boundary_second_is_still_accepted(self) -> None:
        assert verify(header(timestamp=NOW - DEFAULT_TOLERANCE_SECONDS)) is True

    def test_a_timestamp_slightly_ahead_is_accepted_for_clock_skew(self) -> None:
        assert verify(header(timestamp=NOW + 30)) is True

    @pytest.mark.parametrize(("tolerance", "expected"), [(30, False), (120, True)])
    def test_the_tolerance_is_configurable(self, tolerance: int, expected: bool) -> None:
        assert (
            verify_webhook_signature(BODY, header(timestamp=NOW - 60), SECRET, tolerance_seconds=tolerance, now=NOW)
            is expected
        )


class TestAReceiverMidRotation:
    """For 24h after a rotate a delivery carries two ``v1`` values, one per valid secret. Both
    halves must pass or deploying a rotated secret would drop deliveries — the outage the grace
    window exists to prevent."""

    ROTATING = f"t={NOW},v1={sign(SECRET, NOW, BODY)},v1={sign(OTHER_SECRET, NOW, BODY)}"

    def test_the_receiver_still_on_the_old_secret_verifies(self) -> None:
        assert verify(self.ROTATING, OTHER_SECRET) is True

    def test_the_receiver_that_has_deployed_the_new_one_verifies(self) -> None:
        assert verify(self.ROTATING, SECRET) is True

    def test_every_v1_is_checked_not_just_the_first(self) -> None:
        # The matching hash is deliberately last: a receiver that stops at the first `v1` passes
        # the tests above by luck and breaks on the first real rotation.
        assert verify(f"t={NOW},v1={'0' * 64},v1={sign(SECRET, NOW, BODY)}") is True


class TestAMalformedHeaderIsRejectedNotRaised:
    """Anyone who can reach the webhook URL can send any header. An exception in a handler is a
    500 and, with most frameworks, a retried delivery — so every path must return False."""

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("", id="empty"),
            pytest.param(None, id="absent"),
            pytest.param("garbage", id="no separators"),
            pytest.param(f"v1={sign(SECRET, NOW, BODY)}", id="no timestamp"),
            pytest.param(f"t={NOW}", id="no v1"),
            pytest.param(f"t={NOW},v1=", id="empty v1"),
            pytest.param("t=soon,v1=deadbeef", id="non-numeric timestamp"),
            pytest.param(f"t=1.787e9,v1={sign(SECRET, NOW, BODY)}", id="exponent timestamp"),
            pytest.param(f"t= {NOW},v1=x", id="padded timestamp"),
            pytest.param(f"t={NOW},v1=dead", id="truncated v1"),
            # `hmac.compare_digest` RAISES on a str with a non-ASCII character.
            pytest.param(f"t={NOW},v1=deadébeef", id="non-ascii v1"),
        ],
    )
    def test_it_is_false(self, value: str | None) -> None:
        assert verify(value) is False

    def test_no_secret_yet_is_false_rather_than_an_error(self) -> None:
        """A workspace that has never fetched a secret receives unsigned deliveries; a receiver
        configured before that must refuse them, not crash."""
        assert verify_webhook_signature(BODY, header(), "", now=NOW) is False


class TestSignatureTimestamp:
    def test_it_reads_t(self) -> None:
        assert signature_timestamp(header()) == NOW

    @pytest.mark.parametrize("value", ["", None, "v1=abc", "t=soon", "t="])
    def test_it_is_none_when_there_is_nothing_usable(self, value: str | None) -> None:
        assert signature_timestamp(value) is None


def test_the_module_imports_nothing_but_the_standard_library() -> None:
    """`abyssale.webhooks` must stay usable in a receiver process that holds no credential.

    Asserted on the module's own import statements rather than by unsetting the env var: config is
    resolved in a client constructor, so importing a client would not raise today and the
    regression would be silent. A relative import is what would eventually reach one.
    """
    import ast
    import pathlib
    import sys

    import abyssale.webhooks

    source = pathlib.Path(abyssale.webhooks.__file__).read_text()
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `level > 0` is a relative import — the only route back to the clients.
            assert node.level == 0, f"relative import of {node.module!r} would reach a client"
            if node.module:
                imported.add(node.module.split(".")[0])

    assert imported, "parsed no imports — the assertion below would be vacuous"
    assert imported <= set(sys.stdlib_module_names), f"non-stdlib imports: {imported}"
