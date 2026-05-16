from decimal import Decimal

from app.domain.games.base import BetTypeDefinition

XSMB_BET_TYPES: list[BetTypeDefinition] = [
    BetTypeDefinition(
        type_id="lo",
        display_name="Lô",
        odds=Decimal("75"),
        min_numbers=1,
        max_numbers=1,
        description="Chọn 1 số (00-99). Thắng nếu số xuất hiện trong bất kỳ giải nào. Tỷ lệ 1:75.",
        number_range=(0, 99),
    ),
    BetTypeDefinition(
        type_id="de",
        display_name="Đề",
        odds=Decimal("75"),
        min_numbers=1,
        max_numbers=1,
        description="Chọn 1 số (00-99). Thắng nếu khớp 2 số cuối giải Đặc Biệt. Tỷ lệ 1:75.",
        number_range=(0, 99),
    ),
    BetTypeDefinition(
        type_id="xien2",
        display_name="Lô Xiên 2",
        odds=Decimal("10"),
        min_numbers=2,
        max_numbers=2,
        description="Chọn 2 số. Cả 2 phải xuất hiện trong kết quả. Tỷ lệ 1:10.",
        number_range=(0, 99),
    ),
    BetTypeDefinition(
        type_id="xien3",
        display_name="Lô Xiên 3",
        odds=Decimal("40"),
        min_numbers=3,
        max_numbers=3,
        description="Chọn 3 số. Cả 3 phải xuất hiện trong kết quả. Tỷ lệ 1:40.",
        number_range=(0, 99),
    ),
]
