import uuid
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
from models import StartRequest, StartResponse, StatusResponse
from utils import best_price, profit_pct
from mock.exchange import router as mock_router
from core import pub_queue, tasks_store
from worker.worker import worker_loop
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Эндпоинты реализованы ниже:
# POST /start — в функции start(), возвращает task_id
# GET /status/{task_id} — в функции status(), возвращает состояние задачи

# Фоновый воркер запускается через lifespan (FastAPI v0.100+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(worker_loop())
    logger.info("Worker loop started")
    yield

app = FastAPI(title="Arbitrage Bot", lifespan=lifespan)
app.include_router(mock_router)

async def lifespan(app: FastAPI):
    # запускаем воркер при старте
    asyncio.create_task(worker_loop())
    logger.info("Worker loop started")
    yield

# Запуск задачи
@app.post('/start', response_model=StartResponse)
async def start(req: StartRequest):
    task_id = uuid.uuid4()
    tasks_store[task_id] = {
        'params': req.model_dump(),
        'status': 'running',
        'last_check': None,
        'opportunity': None
    }
    await pub_queue.put(task_id)
    logger.info(f"Started task {task_id} with params {req.model_dump()}")
    return StartResponse(task_id=task_id)

# Получение статуса задачи
@app.get('/status/{task_id}', response_model=StatusResponse)
async def status(task_id: uuid.UUID):
    """Получить статус задачи"""
    record = tasks_store.get(task_id)
    if not record:
        logger.warning(f"Status requested for unknown task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Status for task {task_id}: {record['status']}")
    return StatusResponse(**record)

# Остановка задачи
@app.post('/stop/{task_id}')
async def stop(task_id: uuid.UUID):
    """Остановить задачу по запросу пользователя"""
    record = tasks_store.get(task_id)
    if not record:
        logger.warning(f"Stop requested for unknown task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    record['status'] = 'stopped'
    logger.info(f"Task {task_id} stopped by user")
    return {'task_id': task_id, 'status': 'stopped'}
