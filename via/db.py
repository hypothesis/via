import sqlalchemy
import zope.sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Session


class Base(MappedAsDataclass, DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_N_label)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s_%(referred_column_0_N_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def create_engine(settings):  # pragma: no cover
    """Return a SQLAlchemy engine."""
    return sqlalchemy.create_engine(settings["database_url"])


def includeme(config):  # pragma: no cover
    engine = create_engine(config.registry.settings)

    def db_session(request):
        """Return the SQLAlchemy session for the given request."""
        session = Session(engine, info={"request": request})

        # Register the session with pyramid_tm/transaction so that they'll
        # create a new DB transaction for each request and close the session at
        # the end of the request.
        zope.sqlalchemy.register(session, transaction_manager=request.tm)

        return session

    # Make the SQLAlchemy session available as `request.db`.
    # `reify=True` means it'll create only one session per request.
    config.add_request_method(db_session, name="db", reify=True)
