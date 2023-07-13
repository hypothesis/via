from dataclasses import dataclass
from typing import List



@dataclass
class TranscriptInfo:
    id: str
    name: str
    language_code: str
    is_auto_generated: bool
    is_translatable: bool
    url: str = None


@dataclass
class TranscriptText:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    text: List[TranscriptText]
    info: TranscriptInfo
