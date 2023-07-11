from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class CreatedUpdatedMixin(MappedAsDataclass):
    created: Mapped[datetime] = mapped_column(
        init=False,
        repr=False,
        server_default=func.now(),  # pylint:disable=not-callable
        sort_order=-10,
    )
    updated: Mapped[datetime] = mapped_column(
        init=False,
        repr=False,
        server_default=func.now(),  # pylint:disable=not-callable
        onupdate=func.now(),  # pylint:disable=not-callable
        sort_order=-10,
    )
