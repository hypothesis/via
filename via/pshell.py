from h_testkit import set_factoryboy_sqlalchemy_session  # type: ignore

from tests import factories
from via import models


def setup(env):
    env["tm"] = env["request"].tm
    env["tm"].__doc__ = "Active transaction manager (a transaction is already begun)."
    env["request"].tm.begin()

    env["db"] = env["request"].db
    env["db"].__doc__ = "Active DB session."

    env["m"] = env["models"] = models
    env["m"].__doc__ = "The via.models package."

    env["f"] = env["factories"] = factories
    env["f"].__doc__ = "The test factories for quickly creating objects."
    set_factoryboy_sqlalchemy_session(env["request"].db)
