from os import environ

import httpretty
import pytest
from h_matchers import Any
from pytest_factoryboy import register
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.factories import TranscriptFactory
from tests.factories.factoryboy_sqlalchemy_session import (
    clear_factoryboy_sqlalchemy_session,
    set_factoryboy_sqlalchemy_session,
)
from via.db import Base

# Each factory has to be registered with pytest_factoryboy.
register(TranscriptFactory)


@pytest.fixture
def pyramid_settings():
    return {
        "client_embed_url": "http://hypothes.is/embed.js",
        "nginx_server": "http://via.hypothes.is",
        "via_html_url": "https://viahtml.hypothes.is/proxy",
        "checkmate_url": "http://localhost:9099",
        "nginx_secure_link_secret": "not_a_secret",
        "via_secret": "not_a_secret",
        "signed_urls_required": False,
        "checkmate_api_key": "dev_api_key",
        "checkmate_ignore_reasons": None,
        "checkmate_allow_all": False,
        "enable_front_page": True,
        "data_directory": "tests/data_directory",
        "dev": False,
        "youtube_transcripts": True,
        "api_jwt_secret": "secret",
        "youtube_api_key": "test_youtube_api_key",
        "database_url": environ["DATABASE_URL"],
    }


def assert_cache_control(headers, cache_parts):
    """Assert that all parts of the Cache-Control header are present."""
    assert dict(headers) == Any.dict.containing({"Cache-Control": Any.string()})
    assert (
        headers["Cache-Control"].split(", ") == Any.list.containing(cache_parts).only()
    )


@pytest.fixture(autouse=True)
def httpretty_():
    """Monkey-patch Python's socket core module to mock all HTTP responses.

    We never want real HTTP requests to be sent by the tests so replace them
    all with mock responses. This handles requests sent using the standard
    urllib2 library and the third-party httplib2 and requests libraries.
    """
    httpretty.enable(allow_net_connect=False)

    yield

    httpretty.disable()
    httpretty.reset()


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(environ["DATABASE_URL"])

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine


@pytest.fixture(scope="session")
def db_sessionfactory():
    return sessionmaker()


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """Return the SQLAlchemy database session.

    This returns a session that is wrapped in an external transaction that is
    rolled back after each test, so tests can't make database changes that
    affect later tests.  Even if the test (or the code under test) calls
    session.commit() this won't touch the external transaction.

    This is the same technique as used in SQLAlchemy's own CI:
    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = db_sessionfactory(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    set_factoryboy_sqlalchemy_session(session)

    yield session

    clear_factoryboy_sqlalchemy_session()
    session.close()
    transaction.rollback()
    connection.close()
