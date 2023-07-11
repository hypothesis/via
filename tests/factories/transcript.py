from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from via.models import Transcript


class TranscriptFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Transcript

    video_id = Sequence(lambda n: f"video_id_{n}")
    transcript_id = Sequence(lambda n: f"transcript_id_{n}")
    transcript = [
        {
            "text": "[Music]",
            "start": 0.0,
            "duration": 7.52,
        },
        {
            "text": "how many of you remember the first time",
            "start": 5.6,
            "duration": 4.72,
        },
        {
            "text": "you saw a playstation 1 game if you were",
            "start": 7.52,
            "duration": 4.72,
        },
    ]
