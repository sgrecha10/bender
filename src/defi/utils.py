from hexbytes import HexBytes


def decode_hexbytes(value: HexBytes, kind: str = "auto") -> [None | str]:
    """
    Преобразует HexBytes в строку без незначащих нулей.

    :param value: HexBytes объект
    :param kind: один из 'auto', 'int', 'address', 'hash', 'raw'
    :return: человекочитаемая строка
    """
    if not value:
        return

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



# ниже от чат гпт, не проверял
def simulate_swap_v2(reserve_in, reserve_out, amount_in, fee=0.003):
    """
    Смоделировать своп в Uniswap V2 с расчётом цены и проскальзывания.

    reserve_in  - текущий резерв токена, который мы вносим
    reserve_out - текущий резерв токена, который мы получаем
    amount_in   - количество токена, которое вносим
    fee         - комиссия пула (по умолчанию 0.3%)
    """
    # цена до сделки (сколько OUT за 1 IN)
    price_before = reserve_out / reserve_in

    # комиссия (пример: 0.3% => множитель 0.997)
    amount_in_with_fee = amount_in * (1 - fee)

    # расчёт, сколько получим
    amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)

    # новые резервы
    new_reserve_in = reserve_in + amount_in
    new_reserve_out = reserve_out - amount_out

    # цена после сделки
    price_after = new_reserve_out / new_reserve_in

    # проскальзывание (%)
    slippage = (price_before - price_after) / price_before * 100

    return {
        "amount_out": amount_out,
        "new_reserve_in": new_reserve_in,
        "new_reserve_out": new_reserve_out,
        "price_before": price_before,
        "price_after": price_after,
        "slippage_percent": slippage
    }


# === Пример использования ===
reserve_eth = 100  # ETH
reserve_usdc = 200_000  # USDC
amount_in = 1  # хотим продать 1 ETH

result = simulate_swap_v2(reserve_eth, reserve_usdc, amount_in)

print(f"Получим: {result['amount_out']:.2f} USDC")
print(f"Цена до: {result['price_before']:.2f} USDC за ETH")
print(f"Цена после: {result['price_after']:.2f} USDC за ETH")
print(f"Проскальзывание: {result['slippage_percent']:.4f}%")


# а вот еще для серии свопов

import matplotlib.pyplot as plt

def simulate_swap_v2(reserve_in, reserve_out, amount_in, fee=0.003):
    """Моделирование одного свопа в Uniswap V2."""
    price_before = reserve_out / reserve_in
    amount_in_with_fee = amount_in * (1 - fee)
    amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)

    new_reserve_in = reserve_in + amount_in
    new_reserve_out = reserve_out - amount_out

    price_after = new_reserve_out / new_reserve_in
    slippage = (price_before - price_after) / price_before * 100

    return amount_out, new_reserve_in, new_reserve_out, price_before, price_after, slippage


def simulate_multiple_swaps(reserve_in, reserve_out, swap_amounts, fee=0.003):
    """Серия свопов подряд и сбор статистики."""
    prices = []
    slippages = []
    reserves_in = []
    reserves_out = []

    for amt in swap_amounts:
        amount_out, reserve_in, reserve_out, price_before, price_after, slippage = simulate_swap_v2(
            reserve_in, reserve_out, amt, fee
        )
        prices.append(price_after)
        slippages.append(slippage)
        reserves_in.append(reserve_in)
        reserves_out.append(reserve_out)

    return prices, slippages, reserves_in, reserves_out


# === Пример использования ===
reserve_eth = 100
reserve_usdc = 200_000

# Симулируем серию сделок: сначала 1 ETH, потом 2 ETH, потом 5 ETH, потом 10 ETH
swap_amounts = [1, 2, 5, 10]

prices, slippages, reserves_in, reserves_out = simulate_multiple_swaps(reserve_eth, reserve_usdc, swap_amounts)

# === Визуализация ===
plt.figure(figsize=(10, 6))

plt.plot(prices, marker="o", label="Цена (USDC за ETH)")
plt.plot(slippages, marker="x", label="Проскальзывание (%)")

plt.title("Моделирование серии свопов в Uniswap V2")
plt.xlabel("Номер транзакции")
plt.ylabel("Значения")
plt.legend()
plt.grid(True)
plt.show()
