import uuid
import asyncio

# Очередь задач для воркера
pub_queue: asyncio.Queue[uuid.UUID] = asyncio.Queue()
# In-memory хранилище состояния задач
tasks_store: dict[uuid.UUID, dict] = {}
