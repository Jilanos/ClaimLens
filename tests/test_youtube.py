from claimlens.youtube import _extract_json_object, _extract_videos


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
