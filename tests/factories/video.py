from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from via.models import Video


class VideoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Video

    video_id = Sequence(lambda n: f"video_id_{n}")
    title = Sequence(lambda n: f"video_title_{n}")
