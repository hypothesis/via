from unittest.mock import sentinel

import pytest
from h_matchers import Any

from via.services.youtube_api import Captions, CaptionTrack, Video


class TestCaptionTrack:
    @pytest.mark.parametrize("kind", (None, True))
    def test_from_v1_json(self, kind):
        data = {
            "name": {"simpleText": "English (British) - Name"},
            "languageCode": "en-GB",
            "baseUrl": sentinel.url,
        }
        if kind:
            data["kind"] = kind

        caption_track = CaptionTrack.from_v1_json(data)

        assert caption_track == Any.instance_of(CaptionTrack).with_attrs(
            {
                "name": "Name",
                "language_code": "en-gb",
                "label": "English (British) - Name",
                "kind": kind,
                "base_url": sentinel.url,
            }
        )

    def test_is_auto_generated(self):
        caption_track = CaptionTrack("en", kind="asr")
        assert caption_track.is_auto_generated

        caption_track.kind = None
        assert not caption_track.is_auto_generated


class TestCaptions:
    def test_from_v1_json(self, CaptionTrack):
        captions = Captions.from_v1_json({"captionTracks": [{"track": "fake_dict"}]})

        CaptionTrack.from_v1_json.assert_called_once_with({"track": "fake_dict"})
        assert captions == Any.instance_of(Captions).with_attrs(
            {"tracks": [CaptionTrack.from_v1_json.return_value]}
        )

    def test_from_v1_json_minimal(self, CaptionTrack):
        captions = Captions.from_v1_json({})

        assert not captions.tracks
        CaptionTrack.assert_not_called()

    @pytest.fixture
    def CaptionTrack(self, patch):
        return patch("via.services.youtube_api.models.CaptionTrack")


class TestVideo:
    def test_from_v1_json(self, Captions):
        video = Video.from_v1_json(
            data={
                "captions": {"playerCaptionsTracklistRenderer": sentinel.captions},
            },
        )

        Captions.from_v1_json.assert_called_once_with(sentinel.captions)

        assert video == Any.instance_of(Video).with_attrs(
            {"caption": Captions.from_v1_json.return_value}
        )

    def test_from_v1_json_minimal(self, Captions):
        Video.from_v1_json({})

        Captions.from_v1_json.assert_called_once_with({})

    @pytest.fixture
    def Captions(self, patch):
        return patch("via.services.youtube_api.models.Captions")
