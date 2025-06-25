import pytest
from httpx import AsyncClient
from api.main import app
from core import pub_queue, tasks_store

@pytest.mark.asyncio
async def test_start_and_status(tmp_path):
    # стартуем клиент
    async with AsyncClient(app=app, base_url='http://test') as client:
        # POST /start
        resp = await client.post('/start', json={
            'symbol': 'BTC_USDT', 'threshold': 0.5, 'volume': 0.01
        })
        assert resp.status_code == 200
        task_id = resp.json()['task_id']
        # очередь должна содержать задачу
        assert not pub_queue.empty()

        # GET /status до обработки воркером
        status = await client.get(f'/status/{task_id}')
        assert status.status_code == 200
        assert status.json()['status'] == 'running'
