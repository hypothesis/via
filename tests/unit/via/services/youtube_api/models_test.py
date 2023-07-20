from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pytest import param

from via.services.youtube_api import (
    Captions,
    CaptionTrack,
    Channel,
    PlayabilityStatus,
    Video,
    VideoDetails,
)


class TestVideoDetails:
    def test_from_v1_json(self):
        video_details = VideoDetails.from_v1_json(
            {
                "videoId": "VIDEO_ID",
                "title": sentinel.title,
                "author": sentinel.channel_name,
                "channelId": sentinel.channel_id,
            }
        )

        assert video_details == Any.instance_of(VideoDetails).with_attrs(
            {
                "id": "VIDEO_ID",
                "title": sentinel.title,
                "url": "https://www.youtube.com/watch?v=VIDEO_ID",
                "channel": Channel(id=sentinel.channel_id, name=sentinel.channel_name),
            }
        )

    def test_from_v1_json_minimal(self):
        # Just check we don't explode.
        assert VideoDetails.from_v1_json({})

    @pytest.mark.parametrize(
        "video_id,expected_url",
        [
            ("x8TO-nrUtSI", "https://www.youtube.com/watch?v=x8TO-nrUtSI"),
            # YouTube video IDs don't actually contain any characters that
            # require escaping, but this is not guaranteed for the future.
            # See https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video.
            ("foo bar", "https://www.youtube.com/watch?v=foo+bar"),
            ("foo/bar", "https://www.youtube.com/watch?v=foo%2Fbar"),
        ],
    )
    def test_canonical_video_url(self, video_id, expected_url):
        assert expected_url == VideoDetails.canonical_video_url(video_id)


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


class TestPlayabilityStatus:
    @pytest.mark.parametrize(
        "data,expected",
        (
            (
                {
                    "microformat": {"playerMicroformatRenderer": {"embed": Any()}},
                    "playabilityStatus": {
                        "status": "LOGIN_REQUIRED",
                        "reason": "Anything blah verify age blah",
                    },
                },
                PlayabilityStatus(is_embeddable=True, is_age_restricted=True),
            ),
            (
                {"playabilityStatus": {"playableInEmbed": True}},
                PlayabilityStatus(is_embeddable=True, is_age_restricted=False),
            ),
            ({}, PlayabilityStatus(is_embeddable=False, is_age_restricted=False)),
        ),
    )
    def test_from_v1_json(self, data, expected):
        assert PlayabilityStatus.from_v1_json(data) == expected


class TestVideo:
    def test_from_v1_json(self, Captions, VideoDetails, PlayabilityStatus):
        data = {
            "videoDetails": sentinel.video_details,
            "captions": {"playerCaptionsTracklistRenderer": sentinel.captions},
        }

        video = Video.from_v1_json(data=data)

        Captions.from_v1_json.assert_called_once_with(sentinel.captions)
        VideoDetails.from_v1_json.assert_called_once_with(sentinel.video_details)
        PlayabilityStatus.from_v1_json.assert_called_once_with(data)

        assert video == Any.instance_of(Video).with_attrs(
            {
                "caption": Captions.from_v1_json.return_value,
                "details": VideoDetails.from_v1_json.return_value,
                "status": PlayabilityStatus.from_v1_json.return_value,
            }
        )

    def test_from_v1_json_minimal(self, Captions, VideoDetails, PlayabilityStatus):
        Video.from_v1_json({})

        Captions.from_v1_json.assert_called_once_with({})
        VideoDetails.from_v1_json.assert_called_once_with({})
        PlayabilityStatus.from_v1_json.assert_called_once_with({})

    @pytest.fixture
    def Captions(self, patch):
        return patch("via.services.youtube_api.models.Captions")

    @pytest.fixture
    def VideoDetails(self, patch):
        return patch("via.services.youtube_api.models.VideoDetails")

    @pytest.fixture
    def PlayabilityStatus(self, patch):
        return patch("via.services.youtube_api.models.PlayabilityStatus")
