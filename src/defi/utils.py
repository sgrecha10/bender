from hexbytes import HexBytes


def decode_hexbytes(value: HexBytes, kind: str = "auto") -> str:
    """
    Преобразует HexBytes в строку без незначащих нулей.

    :param value: HexBytes объект
    :param kind: один из 'auto', 'int', 'address', 'hash', 'raw'
    :return: человекочитаемая строка
    """
    if not isinstance(value, HexBytes):
        value = HexBytes(value)

    # Преобразование по типу
    if kind == "int":
        return str(int.from_bytes(value, byteorder='big'))
    elif kind == "address":
        # Адрес — последние 20 байт (40 hex-символов)
        return '0x' + value.hex()[-40:]
    elif kind == "hash":
        # Просто hex-представление
        return '0x' + value.hex()
    elif kind == "raw":
        return value.hex()
    elif kind == "auto":
        # Автоопределение: если длина ≤ 32 байт и int не 0 — это число
        try:
            as_int = int(value)
            if 0 < as_int < 2 ** 160:
                return str(as_int)
        except:
            pass
        # Если 20 байт — скорее всего адрес
        if len(value) == 20:
            return '0x' + value.hex()
        return '0x' + value.hex()
    else:
        raise ValueError(f"Unknown kind: {kind}")
