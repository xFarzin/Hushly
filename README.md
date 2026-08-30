# Hushly

An anonymous messaging platform centered around a Telegram bot.

## Architecture
- Python 3.12, FastAPI, Aiogram 3.x, SQLAlchemy 2.x, Alembic, SQLite
- Fully asynchronous
- Secure JWT-based callback data to prevent IDOR and tampering
- Pydantic Settings
- Pillow for RTL Persian text image generation
- No external dependencies like Redis (runs in a single Docker container)

## Setup
1. Clone the repository
2. Set up virtual environment
3. `pip install -r requirements.txt`
4. Set `.env` based on `app/config.py`
5. Run migrations: `alembic upgrade head`
6. Run: `python -m app.main`
