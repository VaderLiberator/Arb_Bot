import asyncio
import uuid
import pytest
from httpx import AsyncClient
from core import pub_queue, tasks_store
from worker.worker import process_task

@pytest.mark.asyncio
async def test_worker_process(monkeypatch):
    # Мокаем ответы AsyncClient.get
    async def fake_get(self, url, params=None):
        # Одинаковые книги для простоты: bid=10@1, ask=9@1
        class R:
            def json(self_inner):
                return {'bids': [[10, 1]], 'asks': [[9, 1]]}
        return R()

    monkeypatch.setattr(AsyncClient, 'get', fake_get)

    # 1) Сценарий: объём = 1 , есть арбитраж (покупаем за 9, продаём за 10)
    tid1 = uuid.uuid4()
    tasks_store[tid1] = {
        'params': {'symbol': 'X', 'threshold': 5, 'volume': 1},
        'status': 'running',
        'last_check': None,
        'opportunity': None
    }
    await process_task(tid1)
    opp1 = tasks_store[tid1]['opportunity']
    # Проверяем, что появилась возможность и profit_pct рассчитан правильно
    assert opp1 is not None
    assert opp1['a_price'] == 9    # цена ask на бирже A
    assert opp1['b_price'] == 10   # цена bid на бирже B
    # Прибыль: (10−9)/9*100 ≈ 11.11  округлено до сотых
    assert opp1['profit_pct'] == 11.11

    # 2) Сценарий: объём = 2, нет подходящих уровней, возможности нет
    tid2 = uuid.uuid4()
    tasks_store[tid2] = {
        'params': {'symbol': 'X', 'threshold': 5, 'volume': 2},
        'status': 'running',
        'last_check': None,
        'opportunity': None
    }
    await process_task(tid2)
    opp2 = tasks_store[tid2]['opportunity']
    # При объёме 2 ни один тикер не имеет необходимого объёма, opportunity остаётся None
    assert opp2 is None
