import pytest
from utils import best_price, profit_pct

# Тест для парсинга книги ордеров: выбираем максимальную ставку и минимальный запрос
def test_best_price_parsing():
    book = {'bids': [[100, 1], [105, 0.5]], 'asks': [[110, 2], [108, 1]]}
    # required_volume=0, чтобы ни один уровень не отфильтровался
    bid, ask = best_price(book, required_volume=0)
    assert (bid, ask) == (105, 108)
    
# Тест для расчёта процента прибыли
def test_profit_pct_ab_direction():
    # Сценарий A>B: покупаем на A по 100, продаём на B по 110
    # profit = (110 - 100) / 100 * 100 = 10.0%
    profit, direction = profit_pct(100, 100, 95, 110)
    assert profit == pytest.approx(10.0)
    assert direction == "A>B"

def test_profit_pct_ba_direction():
    # Сценарий B>A: покупаем на B по 90, продаём на A по 100
    # profit = (100 - 90) / 90 * 100 ≈ 11.11%
    profit, direction = profit_pct(100, 120, 90, 100)
    assert profit == pytest.approx(11.11)
    assert direction == "B>A"
