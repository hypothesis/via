from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from via.db import Base
from via.models._mixins import AutoincrementingIntegerIDMixin, CreatedUpdatedMixin


class Transcript(AutoincrementingIntegerIDMixin, CreatedUpdatedMixin, Base):
    __tablename__ = "transcript"
    __table_args__ = (UniqueConstraint("video_id", "transcript_id"),)

    video_id: Mapped[str]
    transcript_id: Mapped[str]
    transcript: Mapped[list] = mapped_column(JSONB, repr=False)
