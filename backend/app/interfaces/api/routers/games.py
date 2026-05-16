"""Games router — list active games + cutoff status."""
from datetime import datetime

import pytz
from fastapi import APIRouter, HTTPException, status

from app.domain.games.registry import GameRegistry
from app.interfaces.api.schemas.bets import BetTypeOut, CutoffStatusOut, GameOut

router = APIRouter(prefix="/api/games", tags=["games"])

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


@router.get("", response_model=list[GameOut])
async def list_games():
    out: list[GameOut] = []
    for game in GameRegistry.all_active():
        out.append(
            GameOut(
                game_id=game.game_id,
                game_name=game.game_name,
                cutoff_time=game.cutoff_time.strftime("%H:%M"),
                result_time=game.result_time.strftime("%H:%M"),
                is_active=game.is_active,
                bet_types=[
                    BetTypeOut(
                        type_id=bt.type_id,
                        display_name=bt.display_name,
                        odds=bt.odds,
                        min_numbers=bt.min_numbers,
                        max_numbers=bt.max_numbers,
                        description=bt.description,
                    )
                    for bt in game.get_bet_types()
                ],
            )
        )
    return out


@router.get("/{game_id}/cutoff-status", response_model=CutoffStatusOut)
async def cutoff_status(game_id: str):
    try:
        game = GameRegistry.get(game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Game '{game_id}' không tồn tại.")

    now_vn = datetime.now(VN_TZ)
    today = now_vn.date()
    cutoff_dt = VN_TZ.localize(datetime.combine(today, game.cutoff_time))

    seconds = int((cutoff_dt - now_vn).total_seconds())
    is_open = seconds > 0

    return CutoffStatusOut(
        game_id=game_id,
        is_open=is_open,
        cutoff_time=game.cutoff_time.strftime("%H:%M"),
        server_time=now_vn.strftime("%Y-%m-%d %H:%M:%S %Z"),
        seconds_until_cutoff=max(seconds, 0),
    )
