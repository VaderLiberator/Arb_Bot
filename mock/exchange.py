from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/mock')

# Словарь поддерживаемых символов и заглушек order book для каждой биржи
SUPPORTED_SYMBOLS = {
    "BTC_USDT": {
        "exchange_a": {
            "bids": [[30000.01, 0.5], [29995.00, 1.2]],
            "asks": [[30150.00, 0.3], [30155.00, 0.8]],
        },
        "exchange_b": {
            "bids": [[29900.00, 0.7], [29850.00, 2.0], [30555.00, 0.8]], #добавил выигрышный случай
            "asks": [[30100.00, 0.4], [30150.00, 1.0]],
        }
    },
    # Здесь можно добавить другие символы:
    # "ETH_USDT": { ... },
}

@router.get('/exchange-a/book')
async def book_a(symbol: str):
    """Возвращает заглушечные ордера для биржи A"""
    if symbol in SUPPORTED_SYMBOLS:
        # FastAPI автоматически сериализует dict в JSON, код 200 OK
        return SUPPORTED_SYMBOLS[symbol]["exchange_a"]
    # Если символ не поддерживается, возвращаем 404 с объяснением
    raise HTTPException(
        status_code=404,
        detail={"message": f"Order book for symbol '{symbol}' not found on Exchange A"}
    )

@router.get('/exchange-b/book')
async def book_b(symbol: str):
    """Возвращает заглушечные ордера для биржи B"""
    if symbol in SUPPORTED_SYMBOLS:
        return SUPPORTED_SYMBOLS[symbol]["exchange_b"]
    raise HTTPException(
        status_code=404,
        detail={"message": f"Order book for symbol '{symbol}' not found on Exchange B"}
    )
