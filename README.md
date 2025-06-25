# Arb_Bot
Асинхронный арбитражный мини‑бот

# Структура проекта:

arb_bot/

├── api/

│   └── main.py            # FastAPI-приложение с эндпоинтами

├── core.py	               #  Общая очередь задач для воркера и хранилище их состояний

├── worker/

│   └── worker.py          # Асинхронный воркер для обработки задач

├── mock/

│   └── exchange.py        # Заглушки order book для Exchange A и B

├── models.py              # Pydantic-модели запросов и ответов

├── pytest.ini	           # Задание корня модулей для pytest

├── utils.py               # Утилитарные функции для расчёта цен и спреда

├── requirements.txt       # Список зависимостей

├── pyproject.toml         # Конфигурация проекта (PEP 621)

├── README.md              # Инструкция по запуску

├── Dockerfile             # Запуск в Docker

└── tests/

    ├── test_utils.py      # тесты для utils.py
    
    ├── test_api.py        # тесты для эндпоинтов через httpx
    
    └── test_worker.py     # тест воркера с моками и арбитражной возможностью с заданным объемом

# Установка
(powershell windows)
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt

(Linux)
cd /путь/к/arb_bot
source .venv/bin/activate

# Запуск сервера и воркера

в одном терминале с правами администратора и активным venv
c/без Redis:
$Env:WORKER_USE_REDIS = 'false' или 'true'
export WORKER_USE_REDIS=false или true #(linux)

если 'true':
$Env:REDIS_URL  = 'redis://localhost:6379' #(пример windows) 
export REDIS_URL='redis://localhost:6379' #(linux)
uvicorn api.main:app --reload --host 127.0.0.1 --port 8001

# Запуск в Docker
Сборка образа (в корне проекта, где лежит Dockerfile):
docker build -t arb_bot:latest .

Запуск контейнера:
docker run -d --name arb_bot \
  -p 8001:8001 \
  -e CHECK_DELAY=3 \
  -e WORKER_USE_REDIS = 'true' \
  -e REDIS_URL=redis://host:6379 \ #пример
  arb_bot:latest

# Примеры запросов

Запустить задачу в другом терминале PowerShell и томже venv:
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8001/start `
    -ContentType "application/json" `
    -Body '{ 
        "symbol":     "BTC_USDT",
        "threshold":  0.5,
        "volume":     0.01
    }'
    
(Linux)
curl -X POST http://127.0.0.1:8001/start \
     -H "Content-Type: application/json" \
     -d '{
           "symbol":    "BTC_USDT",
           "threshold": 0.5,
           "volume":    0.01
         }'

получим номер запущенной задачи (пример):
task_id
-------
610a5ab8-22ad-48ae-9dee-c12719ec8712

проверить статус:
Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8001/status/610a5ab8-22ad-48ae-9dee-c12719ec8712
(linux)
curl http://127.0.0.1:8001/status/610a5ab8-22ad-48ae-9dee-c12719ec8712

получаем :
status  last_check                  opportunity
------  ----------                  -----------
running 2025-06-23T18:42:22 @{a_price=30150,0; b_price=30555,0; profit_pct=1,34; direction=A>B}

Остановка задачи вручную:
Invoke-RestMethod -Method POST `
  -Uri http://127.0.0.1:8001/stop/{task_id}
(linux )
curl -X POST http://127.0.0.1:8001/stop/610a5ab8-22ad-48ae-9dee-c12719ec8712

Остановка бота:
CTRL+C

# Настройка 
Задержка CHECK_DELAY, По умолчанию интервал проверки равен 2 секундам.
Чтобы его изменить, нужно экспортировать переменную окружения CHECK_DELAY в секундах перед запуском:
$Env:CHECK_DELAY=3 (PowerShell)
export CHECK_DELAY=3 (linux)
После этого воркер будет спать указанное число секунд между итерациями.

# Запуск тэстов

pytest -q -k "test"

В tests/ есть:
test_utils.py — проверяет расчёт лучшей цены и спреда.
test_api.py — с помощью pytest-asyncio + httpx.AsyncClient дергает /start и /status.
test_worker.py — эмитит задачи в очередь и подменяет HTTP-запросы к mock-API через respx или aioresponses, проверяет арбитражную возможнось с заданным объемом
