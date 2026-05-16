"""
Parse raw XSMB API response thành normalized GameResult data.

Schema xosonhanh.vn (uppercase keys):
{
  "DB": "19404",                     ← Đặc biệt
  "G1": "88678",                     ← Giải 1 (1 số 5 chữ số)
  "G2": ["39224", "96731"],          ← Giải 2 (2 số 5 chữ số)
  "G3": [6 số 5 chữ số],
  "G4": [4 số 4 chữ số],
  "G5": [6 số 4 chữ số],
  "G6": [3 số 3 chữ số],
  "G7": [4 số 2 chữ số]
}

Parser chấp nhận cả keys lowercase (db, g1, ...) để backwards-compatible.
"""

# Mapping cho normalize keys (uppercase) → fallback (lowercase)
_KEY_ALIASES = {
    "DB": ("DB", "db"),
    "G1": ("G1", "g1"),
    "G2": ("G2", "g2"),
    "G3": ("G3", "g3"),
    "G4": ("G4", "g4"),
    "G5": ("G5", "g5"),
    "G6": ("G6", "g6"),
    "G7": ("G7", "g7"),
}


def _read(raw: dict, key: str):
    for k in _KEY_ALIASES[key]:
        if k in raw:
            return raw[k]
    return None


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x]
    return [str(value)] if value else []


def parse_xsmb_result(raw: dict) -> dict:
    """
    Parse raw API response (đã unwrap khỏi "data" nếu có) → normalized dict.

    Returns:
        {
            "special_prize": "19404",
            "special_last2": "04",         ← dùng cho Đề
            "all_last2": ["04", "78", ...], ← LIST có duplicate, dùng cho Lô
            "prizes": { "DB": [...], "G1": [...], ... }
        }
    """
    # Unwrap "data" nếu raw vẫn chứa wrapper
    if "data" in raw and isinstance(raw["data"], dict):
        raw = raw["data"]

    prizes: dict[str, list[str]] = {
        key: _as_list(_read(raw, key)) for key in _KEY_ALIASES
    }

    # Collect all_last2 AS LIST WITH DUPLICATES (cho Lô counting)
    all_last2: list[str] = []
    for prize_numbers in prizes.values():
        for num in prize_numbers:
            if num and len(num) >= 2:
                all_last2.append(num[-2:].zfill(2))

    special_prize_list = prizes.get("DB", [])
    special_prize = special_prize_list[0] if special_prize_list else ""
    special_last2 = special_prize[-2:].zfill(2) if len(special_prize) >= 2 else ""

    return {
        "special_prize": special_prize,
        "special_last2": special_last2,
        "all_last2": all_last2,
        "prizes": prizes,
    }
