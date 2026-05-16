from app.domain.games.base import AbstractGame


class GameRegistry:
    _games: dict[str, AbstractGame] = {}

    @classmethod
    def register(cls, game: AbstractGame) -> None:
        cls._games[game.game_id] = game

    @classmethod
    def get(cls, game_id: str) -> AbstractGame:
        if game_id not in cls._games:
            raise ValueError(f"Game '{game_id}' không tồn tại hoặc chưa được đăng ký.")
        return cls._games[game_id]

    @classmethod
    def all_active(cls) -> list[AbstractGame]:
        return [g for g in cls._games.values() if g.is_active]

    @classmethod
    def all_games(cls) -> list[AbstractGame]:
        return list(cls._games.values())
