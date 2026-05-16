"""Unit tests cho XSMBGame.evaluate_bet() — financial critical."""
from datetime import date
from decimal import Decimal

import pytest

from app.domain.entities.game_result import GameResult
from app.domain.games.xsmb.game import XSMBGame
from app.domain.games.xsmb.result_parser import parse_xsmb_result


@pytest.fixture
def game():
    return XSMBGame()


@pytest.fixture
def sample_raw_result():
    """XSMB kết quả mẫu: giải ĐB = 84623, số "23" xuất hiện 3 lần"""
    return {
        "db": "84623",  # last2 = "23"
        "g1": "12345",  # last2 = "45"
        "g2": ["11123", "56789"],  # last2 = "23", "89"
        "g3": ["12334", "45623", "78901", "11111", "22222", "33333"],  # "34","23","01","11","22","33"
        "g4": ["1234", "5678"],  # "34","78"
        "g5": ["12378", "45612", "78945", "11134", "22256", "33378"],  # "78","12","45","34","56","78"
        "g6": ["123", "456"],  # "23","56"
        "g7": ["12", "34", "56", "78"],  # "12","34","56","78"
    }


@pytest.fixture
def game_result(sample_raw_result):
    parsed = parse_xsmb_result(sample_raw_result)
    return GameResult(
        id=1,
        game_id="xsmb",
        draw_date=date(2026, 5, 16),
        parsed_data=parsed,
        raw_json="{}",
        fetched_at=None,
    )


class TestParseXSMBResult:
    def test_special_last2_extracted(self, sample_raw_result):
        parsed = parse_xsmb_result(sample_raw_result)
        assert parsed["special_last2"] == "23"

    def test_all_last2_is_list(self, sample_raw_result):
        parsed = parse_xsmb_result(sample_raw_result)
        assert isinstance(parsed["all_last2"], list)

    def test_all_last2_has_duplicates(self, sample_raw_result):
        parsed = parse_xsmb_result(sample_raw_result)
        count_23 = parsed["all_last2"].count("23")
        assert count_23 >= 3, f"'23' phải xuất hiện >= 3 lần, thực tế: {count_23}"


class TestLoEvaluate:
    def test_lo_wins_single_occurrence(self, game, game_result):
        # "89" xuất hiện đúng 1 lần (g2: "56789")
        won, amount = game.evaluate_bet("lo", ["89"], Decimal("1000"), game_result)
        assert won is True
        assert amount == Decimal("75000")  # 1000 * 75 * 1

    def test_lo_wins_multiple_occurrences(self, game, game_result):
        # "23" xuất hiện nhiều lần → nhân số lần
        won, amount = game.evaluate_bet("lo", ["23"], Decimal("1000"), game_result)
        all_last2 = game_result.parsed_data["all_last2"]
        count = all_last2.count("23")
        assert won is True
        assert amount == Decimal("1000") * 75 * count

    def test_lo_loses_when_not_present(self, game, game_result):
        won, amount = game.evaluate_bet("lo", ["99"], Decimal("5000"), game_result)
        assert won is False
        assert amount == Decimal(0)

    def test_lo_numbers_normalized_to_2_digits(self, game, game_result):
        # Input "1" phải được xử lý thành "01"
        won1, _ = game.evaluate_bet("lo", ["1"], Decimal("1000"), game_result)
        won2, _ = game.evaluate_bet("lo", ["01"], Decimal("1000"), game_result)
        assert won1 == won2


class TestDeEvaluate:
    def test_de_wins_matching_special_prize(self, game, game_result):
        # special_last2 = "23"
        won, amount = game.evaluate_bet("de", ["23"], Decimal("5000"), game_result)
        assert won is True
        assert amount == Decimal("375000")  # 5000 * 75

    def test_de_loses_not_matching(self, game, game_result):
        won, amount = game.evaluate_bet("de", ["99"], Decimal("5000"), game_result)
        assert won is False
        assert amount == Decimal(0)

    def test_de_does_not_count_other_prizes(self, game, game_result):
        # "45" có trong g1 nhưng KHÔNG phải giải ĐB → Đề phải thua
        won, _ = game.evaluate_bet("de", ["45"], Decimal("1000"), game_result)
        # "45" không phải "23" (special) → thua
        assert won is False


class TestXien2Evaluate:
    def test_xien2_wins_both_present(self, game, game_result):
        # "23" và "45" đều có trong kết quả
        won, amount = game.evaluate_bet("xien2", ["23", "45"], Decimal("10000"), game_result)
        assert won is True
        assert amount == Decimal("100000")  # 10000 * 10

    def test_xien2_loses_one_missing(self, game, game_result):
        won, amount = game.evaluate_bet("xien2", ["23", "99"], Decimal("10000"), game_result)
        assert won is False
        assert amount == Decimal(0)

    def test_xien2_loses_both_missing(self, game, game_result):
        won, amount = game.evaluate_bet("xien2", ["97", "98"], Decimal("10000"), game_result)
        assert won is False


class TestXien3Evaluate:
    def test_xien3_wins_all_present(self, game, game_result):
        # "23", "45", "34" đều có trong kết quả
        won, amount = game.evaluate_bet("xien3", ["23", "45", "34"], Decimal("10000"), game_result)
        assert won is True
        assert amount == Decimal("400000")  # 10000 * 40

    def test_xien3_loses_one_missing(self, game, game_result):
        won, amount = game.evaluate_bet("xien3", ["23", "45", "99"], Decimal("10000"), game_result)
        assert won is False


class TestValidateBet:
    def test_valid_lo_bet(self, game):
        game.validate_bet("lo", ["23"], Decimal("1000"))  # should not raise

    def test_invalid_number_out_of_range(self, game):
        with pytest.raises(ValueError, match="không hợp lệ"):
            game.validate_bet("lo", ["100"], Decimal("1000"))

    def test_invalid_bet_type(self, game):
        with pytest.raises(ValueError, match="không hợp lệ"):
            game.validate_bet("invalid_type", ["23"], Decimal("1000"))

    def test_xien2_requires_exactly_2_numbers(self, game):
        with pytest.raises(ValueError):
            game.validate_bet("xien2", ["23"], Decimal("1000"))

    def test_xien3_requires_exactly_3_numbers(self, game):
        with pytest.raises(ValueError):
            game.validate_bet("xien3", ["23", "45"], Decimal("1000"))

    def test_duplicate_numbers_rejected(self, game):
        with pytest.raises(ValueError, match="trùng"):
            game.validate_bet("xien2", ["23", "23"], Decimal("1000"))

    def test_stake_must_be_multiple_of_1000(self, game):
        with pytest.raises(ValueError, match="1,000"):
            game.validate_bet("lo", ["23"], Decimal("1500"))

    def test_zero_stake_rejected(self, game):
        with pytest.raises(ValueError):
            game.validate_bet("lo", ["23"], Decimal("0"))
