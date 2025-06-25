from uuid import UUID            # Тип для уникальных идентификаторов задач
from datetime import datetime    # Для хранения времени последней проверки
from pydantic import BaseModel, Field  # Для валидации и сериализации

class StartRequest(BaseModel):
    symbol: str = Field(..., min_length=1, json_schema_extra={"example": "BTC_USDT"})
    threshold: float = Field(..., ge=0, json_schema_extra={"example": 0.5})
    volume: float = Field(..., gt=0, json_schema_extra={"example": 0.01})

class StartResponse(BaseModel):
    # Ответ сервера с идентификатором задачи
    task_id: UUID

class Opportunity(BaseModel):
    # Модель данных об арбитражной возможности
    a_price: float    # Лучшая цена покупки/продажи  на бирже A
    b_price: float    # Лучшая цена покупки/продажи на бирже B
    profit_pct: float          # Процент потенциальной выгоды
    direction: str	#Направление сделки

class StatusResponse(BaseModel):
    # Ответ для проверки статуса задачи
    status: str               # "running" или "stopped"
    last_check: datetime | None     # Время последней проверки арбитража
    opportunity: Opportunity | None  # Последняя найденная возможность
