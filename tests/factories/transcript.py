from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from via.models import Transcript


class TranscriptFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Transcript

    video_id = Sequence(lambda n: f"video_id_{n}")
    transcript_id = Sequence(lambda n: f"transcript_id_{n}")
    transcript = Sequence(
        lambda n: [{"text": "[Music]", "start": float(n), "duration": float(n + 1)}]
    )
