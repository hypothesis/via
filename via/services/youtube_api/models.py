from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VideoDetails:
    id: str
    title: str
    short_description: str
    author: str
    thumbnails: List[dict]

    @classmethod
    def from_json(cls, data):
        return VideoDetails(
            id=data["videoId"],
            title=data["title"],
            short_description=data["shortDescription"],
            author=data["author"],
            thumbnails=data["thumbnail"]["thumbnails"],
        )


@dataclass
class CaptionTrack:
    id: str
    name: str
    language_code: str
    kind: str
    is_translatable: bool
    url: str = None

    @classmethod
    def from_json(cls, data):
        return CaptionTrack(
            id=data["vssId"],
            language_code=data["languageCode"],
            name=data["name"]["simpleText"],
            kind=data.get("kind", None),
            is_translatable=data.get("isTranslatable", False),
            url=data["baseUrl"],
        )

    @property
    def is_auto_generated(self):
        return self.kind == "asr"


@dataclass
class Captions:
    tracks: List[CaptionTrack]
    translation_languages: List[dict]

    @classmethod
    def from_json(cls, data):
        return Captions(
            tracks=[
                CaptionTrack.from_json(track) for track in data.get("captionTracks", [])
            ],
            translation_languages=[
                {"code": language["languageCode"], "name": language["languageName"]}
                for language in data.get("translationLanguages", [])
            ],
        )


def safe_get(data, path, default=None):
    for key in path:
        if key not in data:
            return default

        data = data[key]

    return data


@dataclass
class Video:
    url: str = None
    details: Optional[VideoDetails] = None
    caption: Optional[Captions] = None
    playability_status: str = None

    @classmethod
    def from_json(cls, url, data):
        captions = safe_get(data, ["captions", "playerCaptionsTracklistRenderer"])

        return Video(
            url=url,
            details=VideoDetails.from_json(data["videoDetails"]),
            caption=Captions.from_json(captions) if captions else None,
            playability_status=safe_get(data, ["playabilityStatus", "status"]),
        )

    @property
    def is_playable(self):
        return self.playability_status == "OK"

    @property
    def has_captions(self):
        return self.caption and self.caption.tracks

    @property
    def id(self):
        return self.details.id


@dataclass
class TranscriptText:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    track: CaptionTrack
    text: List[TranscriptText]
