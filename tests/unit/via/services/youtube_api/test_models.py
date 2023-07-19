from unittest.mock import sentinel

import pytest
from _pytest.mark import param
from h_matchers import Any

from via.services.youtube_api import Captions, CaptionTrack, Video, VideoDetails


class TestVideoDetails:
    def test_from_json(self):
        video_details = VideoDetails.from_json(
            {
                "videoId": sentinel.id,
                "title": sentinel.title,
                "shortDescription": sentinel.short_description,
                "author": sentinel.author,
                # All of this is quite speculative at the moment in terms of whether
                # it's useful, so we aren't carefully controlling the sub-items
                "thumbnail": {"thumbnails": sentinel.thumbnails},
            }
        )

        assert video_details == Any.instance_of(VideoDetails).with_attrs(
            {
                "id": sentinel.id,
                "title": sentinel.title,
                "short_description": sentinel.short_description,
                "author": sentinel.author,
                "thumbnails": sentinel.thumbnails,
            }
        )


class TestCaptionTrack:
    @pytest.mark.parametrize("kind", (None, True))
    @pytest.mark.parametrize("is_translatable", (False, True))
    def test_from_json(self, kind, is_translatable):
        data = {
            "name": {"simpleText": "English (British) - Name"},
            "languageCode": "en-GB",
            "isTranslatable": is_translatable,
            "baseUrl": sentinel.url,
        }
        if kind:
            data["kind"] = kind
        if is_translatable:
            data["isTranslatable"] = True

        caption_track = CaptionTrack.from_json(data)

        assert caption_track == Any.instance_of(CaptionTrack).with_attrs(
            {
                "name": "Name",
                "language_code": "en-gb",
                "label": "English (British) - Name",
                "kind": kind,
                "is_translatable": is_translatable,
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
    def test_from_json(self, CaptionTrack):
        captions = Captions.from_json(
            {
                "captionTracks": [{"track": "fake_dict"}],
                "translationLanguages": [
                    {"languageCode": "en", "languageName": "English"},
                    {"languageCode": "en-GB", "languageName": "English (British)"},
                ],
            }
        )

        CaptionTrack.from_json.assert_called_once_with({"track": "fake_dict"})
        assert captions == Any.instance_of(Captions).with_attrs(
            {
                "tracks": [CaptionTrack.from_json.return_value],
                "translation_languages": [
                    {"code": "en", "name": "English"},
                    {"code": "en-gb", "name": "English (British)"},
                ],
            }
        )

    def test_from_json_minimal(self, CaptionTrack):
        captions = Captions.from_json({})

        assert not captions.tracks
        assert not captions.translation_languages
        CaptionTrack.assert_not_called()

    def test_is_translation_supported(self):
        captions = Captions(
            translation_languages=[{"code": "en-gb", "name": "English (British)"}]
        )

        assert captions.is_translation_supported("en-GB")
        assert captions.is_translation_supported("en-gb")
        assert not captions.is_translation_supported("en")

    def test_is_translation_supported_with_no_languages(self):
        assert not Captions().is_translation_supported("any")

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
            param(
                [CaptionTrack("en", translated_language_code="fr")],
                None,
                id="translation_without_languages",
            ),
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

    @pytest.mark.parametrize(
        "desired_language_code,expected_label",
        (
            param("en", "plain_de", id="translatable"),
            param("en-gb", None, id="untranslatable"),
        ),
    )
    def test_find_matching_track_with_translation(
        self, desired_language_code, expected_label
    ):
        captions = Captions(
            tracks=[
                CaptionTrack("fr", label="plain_fr", is_translatable=False),
                CaptionTrack("de", label="plain_de", is_translatable=True),
            ],
            translation_languages=[{"code": "en", "name": "English"}],
        )

        caption_track = captions.find_matching_track(
            [
                CaptionTrack(
                    language_code=Any(),
                    name=Any(),
                    kind=Any(),
                    translated_language_code=desired_language_code,
                )
            ]
        )

        if expected_label:
            assert caption_track.label == expected_label
            assert caption_track.translated_language_code == desired_language_code
        else:
            assert not caption_track

    @pytest.fixture
    def CaptionTrack(self, patch):
        return patch("via.services.youtube_api.models.CaptionTrack")


class TestVideo:
    def test_from_json(self, Captions, VideoDetails):
        video = Video.from_json(
            url=sentinel.url,
            data={
                "videoDetails": sentinel.video_details,
                "captions": {"playerCaptionsTracklistRenderer": sentinel.captions},
                "playabilityStatus": {"status": "OK"},
            },
        )

        Captions.from_json.assert_called_once_with(sentinel.captions)
        VideoDetails.from_json.assert_called_once_with(sentinel.video_details)

        assert video == Any.instance_of(Video).with_attrs(
            {
                "caption": Captions.from_json.return_value,
                "details": VideoDetails.from_json.return_value,
                "playability_status": "OK",
                "url": sentinel.url,
            }
        )

    def test_from_json_minimal(self):
        video = Video.from_json(sentinel.url, {})

        assert not video.caption
        assert not video.details
        assert not video.playability_status

    @pytest.mark.parametrize(
        "data,is_playable",
        (
            ({"playabilityStatus": {"status": "OK"}}, True),
            ({"playabilityStatus": {"status": "Other"}}, False),
            ({"playabilityStatus": None}, False),
            ({}, False),
        ),
    )
    def test_is_playable(self, data, is_playable):
        assert Video.from_json(sentinel.url, data).is_playable == is_playable

    @pytest.mark.usefixtures("Captions")
    @pytest.mark.parametrize(
        "data,has_captions",
        (
            (
                {"captions": {"playerCaptionsTracklistRenderer": sentinel.captions}},
                True,
            ),
            ({"captions": {"playerCaptionsTracklistRenderer": None}}, False),
            ({"captions": None}, False),
            ({}, False),
        ),
    )
    def test_has_captions(self, data, has_captions):
        assert Video.from_json(sentinel.url, data).has_captions == has_captions

    @pytest.mark.parametrize(
        "video,expected_id",
        (
            (Video(details=VideoDetails(id="1234")), "1234"),
            (Video(details=None), None),
        ),
    )
    def test_id(self, video, expected_id):
        assert video.id == expected_id

    @pytest.fixture
    def Captions(self, patch):
        return patch("via.services.youtube_api.models.Captions")

    @pytest.fixture
    def VideoDetails(self, patch):
        return patch("via.services.youtube_api.models.VideoDetails")
