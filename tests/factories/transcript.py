from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from via.models import Transcript


class TranscriptFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Transcript

    video_id = Sequence(lambda n: f"video_id_{n}")
    transcript_id = Sequence(lambda n: f"transcript_id_{n}")
    transcript = Sequence(
        lambda n: [
            {
                "text": f"This is the first line of transcript {n}",
                "start": 0.0,
                "duration": 7.52,
            },
            {
                "text": f"This is the second line of transcript {n}",
                "start": 5.6,
                "duration": 4.72,
            },
        ]
    )
