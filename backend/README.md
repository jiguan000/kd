# Backend (FastAPI + MySQL)

## Quick start

```bash
conda create -n kb python=3.11 -y
conda activate kb
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database

```sql
CREATE DATABASE knowledge_base DEFAULT CHARACTER SET utf8mb4;
```

Set `DATABASE_URL` in `.env` (see `.env.example`).
