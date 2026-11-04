from src.core.config import settings
from typing import Any


class CookieConfig:
    @property
    def options(self) -> dict[str, Any]:
        env = settings.APP_ENV.strip().lower()

        if env not in ("development", "staging", "production"):
            raise ValueError(f"Invalid environment: {env}")

        is_production = env == "production"
        is_secure = env == "production" or env == "staging"
        max_age = {
            "development": 3600,
            "staging": 86400,
            "production": 604800,
        }[env]

        return {
            "key": settings.REFRESH_TOKEN_KEY,
            "httponly": True,
            "secure": is_secure,
            "samesite": "strict" if is_production else "lax",
            "max_age": max_age,
        }


cookie_config = CookieConfig()
