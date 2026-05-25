import json
from typing import Optional


def clean_none_value(d: dict) -> dict:
    out = {}
    for k in d.keys():
        if d[k] is not None:
            out[k] = d[k]
    return out


def convert_list_to_json_array(symbols):
    if symbols is None:
        return symbols
    res = json.dumps(symbols)
    return res.replace(" ", "")


def rpc_hex_to_int(value: Optional[str]) -> Optional[int]:
    """Преобразовывает hexadecimal в int.

    Нужен для того, что бы не падать на None
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value

    return int(value, 16)
