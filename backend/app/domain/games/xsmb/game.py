from datetime import time
from decimal import Decimal

from app.domain.entities.game_result import GameResult
from app.domain.games.base import AbstractGame, BetTypeDefinition
from app.domain.games.xsmb.bet_types import XSMB_BET_TYPES


class XSMBGame(AbstractGame):
    game_id = "xsmb"
    game_name = "XSMB Số Đề"
    cutoff_time = time(18, 10)
    result_time = time(18, 30)
    is_active = True

    def get_bet_types(self) -> list[BetTypeDefinition]:
        return XSMB_BET_TYPES

    def validate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal) -> None:
        bet_type = self.get_bet_type(bet_type_id)
        if bet_type is None:
            raise ValueError(f"Loại cược '{bet_type_id}' không hợp lệ.")

        if len(numbers) < bet_type.min_numbers or len(numbers) > bet_type.max_numbers:
            raise ValueError(
                f"'{bet_type.display_name}' yêu cầu {bet_type.min_numbers} số, "
                f"bạn nhập {len(numbers)} số."
            )

        for num in numbers:
            if not num.isdigit() or not (0 <= int(num) <= 99):
                raise ValueError(f"Số '{num}' không hợp lệ. Phải là số từ 00 đến 99.")
            if len(num) > 2:
                raise ValueError(f"Số '{num}' không hợp lệ. Tối đa 2 chữ số.")

        if len(numbers) != len(set(numbers)):
            raise ValueError("Không được chọn số trùng nhau.")

        if stake <= 0:
            raise ValueError("Số tiền đặt phải lớn hơn 0.")

        if stake % 1000 != 0:
            raise ValueError("Số tiền đặt phải là bội số của 1,000 VND.")

    def evaluate_bet(
        self,
        bet_type_id: str,
        numbers: list[str],
        stake: Decimal,
        result: GameResult,
    ) -> tuple[bool, Decimal]:
        parsed = result.parsed_data
        all_last2: list[str] = parsed["all_last2"]  # LIST có duplicate
        special_last2: str = parsed["special_last2"]

        # Normalize numbers sang định dạng 2 chữ số
        nums = [n.zfill(2) for n in numbers]

        if bet_type_id == "lo":
            # Đếm số lần xuất hiện — thắng N lần nếu xuất hiện N lần
            count = sum(1 for n in all_last2 if n == nums[0])
            if count == 0:
                return False, Decimal(0)
            return True, stake * Decimal(75) * count

        elif bet_type_id == "de":
            won = nums[0] == special_last2
            return (True, stake * Decimal(75)) if won else (False, Decimal(0))

        elif bet_type_id == "xien2":
            result_set = set(all_last2)
            won = all(n in result_set for n in nums)
            return (True, stake * Decimal(10)) if won else (False, Decimal(0))

        elif bet_type_id == "xien3":
            result_set = set(all_last2)
            won = all(n in result_set for n in nums)
            return (True, stake * Decimal(40)) if won else (False, Decimal(0))

        raise ValueError(f"Loại cược không xác định: {bet_type_id}")
