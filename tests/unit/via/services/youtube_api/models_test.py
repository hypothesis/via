from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pytest import param

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

    CAPTION_TRACK_IDS = (
        (CaptionTrack(language_code="en"), "en"),
        (CaptionTrack(language_code="en", kind="asr"), "en.a"),
        (CaptionTrack(language_code="en", name="Hello"), "en..SGVsbG8="),
        (CaptionTrack(language_code="en", translated_language_code="fr"), "en...fr"),
        # This combination isn't actually possible, but let's try everything at
        # once
        (
            CaptionTrack(
                language_code="en-gb",
                kind="asr",
                name="Name",
                translated_language_code="fr",
            ),
            "en-gb.a.TmFtZQ==.fr",
        ),
    )

    @pytest.mark.parametrize("caption_track,id_string", CAPTION_TRACK_IDS)
    def test_from_id(self, caption_track, id_string):
        assert CaptionTrack.from_id(id_string) == caption_track

    @pytest.mark.parametrize("caption_track,id_string", CAPTION_TRACK_IDS)
    def test_id(self, caption_track, id_string):
        assert caption_track.id == id_string

    def test_is_auto_generated(self):
        caption_track = CaptionTrack("en", kind="asr")
        assert caption_track.is_auto_generated

        caption_track.kind = None
        assert not caption_track.is_auto_generated

        caption_track.is_auto_generated = True
        assert caption_track.is_auto_generated
        assert caption_track.kind == "asr"

        caption_track.is_auto_generated = False
        assert not caption_track.is_auto_generated
        assert not caption_track.kind

    @pytest.mark.parametrize(
        "caption_track,url",
        (
            (
                CaptionTrack("en", base_url="http://example.com?a=1"),
                "http://example.com?a=1",
            ),
            (
                CaptionTrack(
                    "en",
                    base_url="http://example.com?a=1",
                    translated_language_code="fr",
                ),
                "http://example.com?a=1&tlang=fr",
            ),
            (CaptionTrack("en", base_url=None), None),
            (CaptionTrack("en", base_url=None, translated_language_code="fr"), None),
        ),
    )
    def test_url(self, caption_track, url):
        assert caption_track.url == url


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

    @pytest.mark.parametrize(
        "preferences,expected_label",
        (
            param(
                [CaptionTrack("en")],
                "plain_en",
                id="direct_match",
            ),
            param(
                [CaptionTrack("de"), CaptionTrack("en-gb")],
                "plain_en_gb",
                id="miss_then_hit",
            ),
            param(
                [
                    CaptionTrack("de"),
                    CaptionTrack(Any.string.matching("^en-.*"), name="Name"),
                ],
                "named_en_gb",
                id="wild_cards",
            ),
            param(
                [CaptionTrack("fr", kind=None), CaptionTrack("en", kind="asr")],
                "en_auto",
                id="fallback_to_auto",
            ),
            param(
                [CaptionTrack(Any(), name="Name")],
                "named_en_gb",
                id="same_level_sorting",
            ),
            param([CaptionTrack("fr")], None, id="miss"),
        ),
    )
    def test_find_matching_track(self, preferences, expected_label):
        captions = Captions(
            tracks=[
                CaptionTrack("en", label="plain_en"),
                CaptionTrack("en-gb", label="plain_en_gb"),
                CaptionTrack("en-us", name="Name", label="named_en_us"),
                CaptionTrack("en-gb", name="Name", label="named_en_gb"),
                CaptionTrack("en", kind="asr", label="en_auto"),
            ]
        )

        caption_track = captions.find_matching_track(preferences)

        assert (
            caption_track.label == expected_label
            if expected_label
            else not caption_track
        )

    def test_find_matching_track_with_translation(self):
        captions = Captions(tracks=[CaptionTrack("fr", label="plain_fr")])

        caption_track = captions.find_matching_track(
            [
                CaptionTrack(
                    language_code=Any(),
                    name=Any(),
                    kind=Any(),
                    translated_language_code="de",
                )
            ]
        )

        assert caption_track.label == "plain_fr"
        assert caption_track.translated_language_code == "de"

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
