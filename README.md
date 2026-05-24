# Spend Control Control-Service

Standalone public API and orchestration service for Spend Control Console.

## Run

```powershell
cd c:\Users\lijaz\Desktop\PROJECT2\spend-control-control-service
py -3.13 -m pip install -e .
$env:DATABASE_URL='postgresql+psycopg://spendcontrol:spendcontrol@localhost:5432/spend_control'
$env:JWT_SECRET_KEY='dev-secret-change-me'
$env:EXPENSE_SERVICE_URL='http://localhost:8001'
$env:AI_SERVICE_URL='http://localhost:8002'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Test

```powershell
$env:DATABASE_URL='sqlite:///./control-test.db'
$env:JWT_SECRET_KEY='test-secret'
py -3.13 -m pytest tests
```

