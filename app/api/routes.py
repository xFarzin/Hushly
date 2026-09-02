from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.services.links import get_link_by_token_or_slug
from app.localization import get_text

router = APIRouter()

# Get absolute path to templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/{slug}", response_class=HTMLResponse)
async def visit_link(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_token_or_slug(db, slug)

    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Link not found or inactive")

    # Get user to get display name
    await db.refresh(link, ['user'])
    name = link.user.display_name or f"User {link.user.id}"

    lang = link.default_language
    if lang == "auto":
        # Simplified auto-detection, fallback to english
        lang = "en"

    title = get_text(lang, "web_entry_title", name=name)
    button_text = get_text(lang, "web_entry_button")

    # Generate bot deep link
    bot_username = "HushlyChatBot" # Hardcoded for now
    telegram_link = f"https://t.me/{bot_username}?start={link.token}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "lang": lang,
        "title": title,
        "button_text": button_text,
        "telegram_link": telegram_link
    })
