import os
import sys

# Добавляем корневую директорию в путь поиска модулей, чтобы находились utils, models и др.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import uuid
from datetime import datetime, timezone
import httpx
import redis.asyncio as aioredis
from utils import best_price, profit_pct
from api.main import pub_queue, tasks_store
import logging
from core import pub_queue, tasks_store

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
worker_logger = logging.getLogger('worker')

# Настройки
DELAY = int(os.getenv('CHECK_DELAY', 2))  # задержка между проверками (по умолчанию 2 сек)
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8001')
USE_REDIS = os.getenv('WORKER_USE_REDIS', 'false').lower() == 'true'
REDIS_URL = os.getenv('REDIS_URL')       # например redis://localhost:6379
TASKS_CHANNEL = os.getenv('TASKS_CHANNEL', 'arb_tasks')
OPPS_CHANNEL = os.getenv('OPPORTUNITIES_CHANNEL', 'arb_opps')


async def process_task(task_id: uuid.UUID, redis_client: aioredis.Redis | None = None):
    """Запрашивает order book, считает спред и пушит в Redis, если есть возможность"""
    params = tasks_store[task_id]['params']
    symbol = params['symbol']
    threshold = params['threshold']

    # Параллельные запросы к mock-API или реальным эндпоинтам
    async with httpx.AsyncClient(base_url=API_URL) as client:
        try:
            resp_a, resp_b = await asyncio.gather(
                client.get('/mock/exchange-a/book', params={'symbol': symbol}),
                client.get('/mock/exchange-b/book', params={'symbol': symbol})
            )
        except Exception as e:
            worker_logger.error(f"Error fetching books: {e}", exc_info=True)
    
    try:
        book_a = resp_a.json()
    except TypeError:
        # поддержка заглушек с json=lambda:... в тестах
        book_a = resp_a.json.__func__()
    try:
        book_b = resp_b.json()
    except TypeError:
        book_b = resp_b.json.__func__()
        
    # Вычисляем лучшие цены с учетом объема
    required_volume = params.get('volume', 0)
    now = datetime.now(timezone.utc)
    try:
        bid_a, ask_a = best_price(book_a, required_volume)
        bid_b, ask_b = best_price(book_b, required_volume)
    except ValueError:
        # Нет уровней с требуемым объемом — сбрасываем opportunity и выходим
        tasks_store[task_id].update({
            'last_check': now,
            'opportunity': None
        })
        return
    
    # Вычисляем профит и направление сделки
    profit, direction = profit_pct(bid_a, ask_a, ask_b, bid_b)
    
    # Обновление in-memory store для /status
    now = datetime.now(timezone.utc)
    if profit >= threshold:
        # Сохраняем параметры арбитража
        tasks_store[task_id].update({
            'last_check': now,
            'opportunity': {
                'direction': direction,
                'profit_pct': profit,
                'a_price':   ask_a   if direction == "A>B" else bid_a,
                'b_price':   bid_b   if direction == "A>B" else ask_b,
            }
        })
    else:
        # Если profit ниже порога — сбрасываем opportunity
        tasks_store[task_id].update({
            'last_check': now,
            'opportunity': None
        })
    
    # Публикация возможности арбитража
    if profit >= threshold:
        base_ts = tasks_store[task_id]['last_check'].strftime("%Y-%m-%dT%H:%M:%SZ")
        msg = {
            'task_id':     str(task_id),
            'symbol':      symbol,
            'direction':   direction,
            'buy_price':   ask_a   if direction == "A>B" else ask_b,
            'sell_price':  bid_b   if direction == "A>B" else bid_a,
            'profit_pct':  profit,
            'timestamp':   base_ts
        }
        
        if USE_REDIS and REDIS_URL:
            redis_client = redis_client or await aioredis.from_url(REDIS_URL)
            await redis_client.publish_json(OPPS_CHANNEL, msg)
            worker_logger.info(f"Published opportunity to Redis: {msg}")
        else:
            worker_logger.info(f"Arbitrage opportunity: {msg}")

async def redis_listener(redis_client: aioredis.Redis):
    """Подписывается на канал задач и пушит в очередь pub_queue"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(TASKS_CHANNEL)
    worker_logger.info(f"Subscribed to Redis channel '{TASKS_CHANNEL}'")
    async for msg in pubsub.listen():
        if msg['type'] == 'message':
            try:
                tid = uuid.UUID(msg['data'].decode())
                # Инициализация записи в памяти
                tasks_store[tid] = {
                    'params': tasks_store.get(tid, {}).get('params', {}),
                    'status': 'running',
                    'last_check': None,
                    'opportunity': None
                }
                worker_logger.info(f"Received task_id {tid} from Redis channel")
                await pub_queue.put(tid)
            except Exception as e:
                worker_logger.error(f"Error parsing task_id: {e}")

async def worker_loop():
    """Запуск обработки задач с учётом USE_REDIS"""
    redis_client = None
    if USE_REDIS:
        if not REDIS_URL:
            worker_logger.error("WORKER_USE_REDIS=true, but REDIS_URL is not set")
        else:
            redis_client = await aioredis.from_url(REDIS_URL)
            asyncio.create_task(redis_listener(redis_client))

    while True:
        task_id = await pub_queue.get()
        worker_logger.info(f"Got task_id {task_id}, entering processing loop")
        # Обработка задачи пока статус 'running'
        while tasks_store.get(task_id, {}).get('status') == 'running':
            await process_task(task_id, redis_client)
            await asyncio.sleep(DELAY)
        # После выхода изменяем состояние очереди и метаданные
        worker_logger.info(f"Task {task_id} completed or stopped")
        tasks_store[task_id]['status'] = 'stopped'
        pub_queue.task_done()
