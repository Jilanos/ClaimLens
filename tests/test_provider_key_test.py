from urllib.error import HTTPError

import pytest

from claimlens.api_keys import ApiKeyTestError, validate_provider_api_key


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"data": []}'


def test_provider_key_test_calls_openai(monkeypatch):
    seen = {}

    def fake_open(url_request, timeout):
        seen["url"] = url_request.full_url
        seen["auth"] = url_request.get_header("Authorization")
        return Response()

    monkeypatch.setattr("claimlens.api_keys.urlopen", fake_open)
    validate_provider_api_key("openai", "secret")
    assert seen["url"].endswith("/v1/models")
    assert seen["auth"] == "Bearer secret"


def test_provider_key_test_surfaces_http_rejection(monkeypatch):
    def fake_open(*args, **kwargs):
        raise HTTPError("https://api.openai.com/v1/models", 401, "unauthorized", {}, None)

    monkeypatch.setattr("claimlens.api_keys.urlopen", fake_open)
    with pytest.raises(ApiKeyTestError, match="HTTP 401"):
        validate_provider_api_key("openai", "bad")
