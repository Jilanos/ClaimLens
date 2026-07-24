import io
from urllib.error import HTTPError

import pytest

from claimlens.youtube import (
    SupadataClient,
    SupadataQuotaError,
    _extract_json_object,
    _extract_videos,
)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_extract_json_object_balances_strings():
    html = 'x ytInitialData = {"title":"brace } in string","items":[{"id":1}]}; y'

    assert _extract_json_object(html, "ytInitialData") == {
        "title": "brace } in string",
        "items": [{"id": 1}],
    }


def test_extract_videos_supports_lockup_view_model():
    data = {
        "richItemRenderer": {
            "content": {
                "lockupViewModel": {
                    "contentId": "video123",
                    "metadata": {
                        "lockupMetadataViewModel": {
                            "title": {"content": "Video title"},
                            "metadata": {
                                "contentMetadataViewModel": {
                                    "metadataRows": [
                                        {
                                            "metadataParts": [
                                                {"text": {"content": "11K views"}},
                                                {"text": {"content": "3 days ago"}},
                                            ]
                                        }
                                    ]
                                }
                            },
                        }
                    },
                    "contentImage": {
                        "thumbnailViewModel": {
                            "overlays": [
                                {
                                    "thumbnailBottomOverlayViewModel": {
                                        "badges": [
                                            {
                                                "thumbnailBadgeViewModel": {
                                                    "text": "8:58",
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                }
            }
        }
    }

    videos = _extract_videos(data)

    assert len(videos) == 1
    assert videos[0].id == "video123"
    assert videos[0].title == "Video title"
    assert videos[0].published_text == "3 days ago"
    assert videos[0].duration_text == "8:58"


def test_supadata_native_transcript_request_and_parse(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["key"] = request.headers["X-api-key"]
        return Response(
            b"""
            {
              "content": [
                {"text": "hello", "offset": 1200, "duration": 300, "lang": "en"},
                {"text": "world", "offset": 1600, "duration": 400, "lang": "en"}
              ],
              "lang": "en",
              "availableLangs": ["en"]
            }
            """
        )

    monkeypatch.setattr("claimlens.youtube.urlopen", fake_urlopen)

    transcript = SupadataClient(api_key="supadata-secret").fetch_native_transcript(
        video_url="https://www.youtube.com/watch?v=abc123XYZ_",
        video_id="abc123XYZ_",
        language="en",
    )

    assert "mode=native" in seen["url"]
    assert "mode=auto" not in seen["url"]
    assert "mode=generate" not in seen["url"]
    assert "text=false" in seen["url"]
    assert seen["key"] == "supadata-secret"
    assert transcript.source == "supadata-native"
    assert transcript.text == "hello\nworld"
    assert transcript.segments[0].start_seconds == 1.2
    assert transcript.segments[0].end_seconds == 1.5


def test_supadata_account_info_and_quota_error(monkeypatch):
    def ok_urlopen(request, timeout):
        if request.full_url.endswith("/me"):
            return Response(b'{"maxCredits": 100, "usedCredits": 99}')
        raise AssertionError(request.full_url)

    monkeypatch.setattr("claimlens.youtube.urlopen", ok_urlopen)
    account = SupadataClient(api_key="supadata-secret").account_info()
    assert account.max_credits == 100
    assert account.used_credits == 99

    def quota_urlopen(request, timeout):
        raise HTTPError(
            request.full_url,
            429,
            "too many",
            {},
            io.BytesIO(b'{"message": "limit exceeded"}'),
        )

    monkeypatch.setattr("claimlens.youtube.urlopen", quota_urlopen)
    with pytest.raises(SupadataQuotaError, match="limit exceeded"):
        SupadataClient(api_key="supadata-secret").account_info()
