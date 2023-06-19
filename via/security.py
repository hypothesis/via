from datetime import datetime, timedelta, timezone

import jwt
from pyramid.security import Allowed, Denied


class ViaSecurityPolicy:
    def permits(self, request, _context, permission):
        try:
            encoded_jwt = request.headers["Authorization"][len("Bearer ") :]
        except KeyError:
            return Denied("No Authorization header")

        try:
            jwt.decode(
                encoded_jwt,
                self._get_jwt_secret(request),
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
        except jwt.InvalidTokenError:
            return Denied("Invalid JWT")

        if permission == "api":
            return Allowed("Valid JWT provided")

        return Denied("Unknown permission")

    @classmethod
    def encode_jwt(cls, request):
        return jwt.encode(
            {"exp": datetime.now(tz=timezone.utc) + timedelta(hours=48)},
            cls._get_jwt_secret(request),
            algorithm="HS256",
        )

    @staticmethod
    def _get_jwt_secret(request):
        return request.registry.settings["api_jwt_secret"]
