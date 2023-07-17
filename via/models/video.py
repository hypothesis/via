from sqlalchemy.orm import Mapped, mapped_column

from via.db import Base
from via.models._mixins import AutoincrementingIntegerIDMixin, CreatedUpdatedMixin


class Video(AutoincrementingIntegerIDMixin, CreatedUpdatedMixin, Base):
    __tablename__ = "video"

    video_id: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(repr=False)
