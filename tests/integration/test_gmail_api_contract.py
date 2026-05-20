"""Contract tests for GmailVacationManager against the real google-api-python-client.

These tests use ``googleapiclient.http.HttpMockSequence`` so the actual client
library handles discovery doc parsing, URL construction, and parameter
validation. They catch mistakes (wrong kwarg names, missing parameters,
incompatible request bodies) that a pure ``MagicMock`` would silently accept.

Marked ``integration`` so they're skipped unless run with ``pytest -m integration``.
"""

import json
from unittest.mock import MagicMock

import pytest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMockSequence

from auth import BaseAuth
from gmail_api import GmailVacationManager

pytestmark = pytest.mark.integration

# Note: google-api-python-client ships its own cached discovery docs for popular
# APIs (static_discovery=True is the default), so build() does not hit the
# network for the discovery doc. We only need to mock the actual API calls.
# A vendored copy lives at tests/fixtures/gmail-discovery-v1.json for reference
# and for future tests that may need static_discovery=False.


def _make_manager(http: HttpMockSequence, user_email: str) -> GmailVacationManager:
    """Build a GmailVacationManager whose service uses the supplied mock HTTP."""
    service = build("gmail", "v1", http=http, developerKey="test-key")
    auth = MagicMock(spec=BaseAuth)
    manager = GmailVacationManager(auth, user_email=user_email)
    manager._service = service
    return manager


def _response(status: str, body: dict) -> tuple[dict, bytes]:
    return ({"status": status}, json.dumps(body).encode())


class TestGetVacationSettings:
    def test_returns_payload_from_api(self) -> None:
        http = HttpMockSequence(
            [
                _response(
                    "200",
                    {
                        "enableAutoReply": True,
                        "responseSubject": "Out of Office",
                        "responseBodyHtml": "<p>Back Monday</p>",
                        "restrictToContacts": False,
                        "restrictToDomain": True,
                    },
                ),
            ]
        )
        manager = _make_manager(http, user_email="user@example.com")

        result = manager.get_vacation_settings()

        assert result["enableAutoReply"] is True
        assert result["responseSubject"] == "Out of Office"
        assert result["restrictToDomain"] is True


class TestSetVacationMessage:
    def test_sends_well_formed_update_request(self) -> None:
        http = HttpMockSequence(
            [
                _response("200", {"enableAutoReply": True}),
            ]
        )
        manager = _make_manager(http, user_email="user@example.com")

        # If the call shape is wrong (bad kwarg, missing required field, etc.)
        # the real client raises before we get here.
        success = manager.set_vacation_message(
            subject="Hello",
            message="<p>Body</p>",
        )

        assert success is True


class TestDelegates:
    def test_create_delegate_returns_true_on_success(self) -> None:
        http = HttpMockSequence(
            [
                _response(
                    "200",
                    {
                        "delegateEmail": "helper@example.com",
                        "verificationStatus": "accepted",
                    },
                ),
            ]
        )
        manager = _make_manager(http, user_email="user@example.com")

        assert manager.create_delegate("helper@example.com") is True

    def test_create_delegate_returns_false_on_http_error(self) -> None:
        http = HttpMockSequence(
            [
                _response("403", {"error": {"code": 403, "message": "Forbidden"}}),
            ]
        )
        manager = _make_manager(http, user_email="user@example.com")

        assert manager.create_delegate("helper@example.com") is False
