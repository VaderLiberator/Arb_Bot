from typing import Tuple, Dict

def best_price(book: Dict, required_volume: float) -> Tuple[float, float]:
    """
    Из книги ордеров берём максимальную bid-цену и минимальную ask-цену,
    причём учитываем только те уровни, где объём >= required_volume.
    :param book: словарь с ключами 'bids' и 'asks'
    :param required_volume: минимальный объём для сделки
    :return: (best_bid_price, best_ask_price)
    """
    # фильтруем bids и asks по объёму
    valid_bids = [level for level in book['bids'] if level[1] >= required_volume]
    valid_asks = [level for level in book['asks'] if level[1] >= required_volume]
    if not valid_bids or not valid_asks:
        raise ValueError(f"No order book entries satisfy required volume {required_volume}")
    best_bid = max(valid_bids, key=lambda x: x[0])[0]
    best_ask = min(valid_asks, key=lambda x: x[0])[0]
    return best_bid, best_ask


def profit_pct(a_bid: float, a_ask: float, b_ask: float, b_bid: float) -> Tuple[float, str]:
    """
    Рассчитываем процент прибыли от арбитража в обоих направлениях:
    - A→B: покупаем по спектру A (a_ask), продаём по спектру B (b_bid)
    - B→A: покупаем по спектру B (b_ask), продаём по спектру A (a_bid)
    Возвращаем наибольшую прибыль и направление.
    """
    profit_ab = round((b_bid - a_ask) / a_ask * 100, 2)   # A>B
    profit_ba = round((a_bid - b_ask) / b_ask * 100, 2)  # B>A
    if profit_ab >= profit_ba:
        return profit_ab, "A>B"
    else:
        return profit_ba, "B>A"
