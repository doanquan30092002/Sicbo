"""Shared fixtures cho pytest. Import GameRegistry để đảm bảo games được đăng ký."""
import pytest

import app.domain.games  # noqa: F401 — side-effect: register XSMBGame
