"""Game plugin auto-registration.

Khi module này được import, tất cả games (active + stub) được đăng ký vào GameRegistry.
Thứ tự: chỉ register active games đầu để hot path nhẹ; stub games đăng ký sau (is_active=False).
"""
from app.domain.games.registry import GameRegistry
from app.domain.games.xsmb.game import XSMBGame
from app.domain.games.bau_cua.game import BauCuaGame
from app.domain.games.duck_race.game import DuckRaceGame
from app.domain.games.horse_race.game import HorseRaceGame

GameRegistry.register(XSMBGame())
GameRegistry.register(BauCuaGame())
GameRegistry.register(DuckRaceGame())
GameRegistry.register(HorseRaceGame())

__all__ = ["GameRegistry"]
