"""Telegram bot subclass that localizes finalized UI text and keyboards."""
import json
import os
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ExtBot
from ui_en import translate as translate_en


def language_for(chat_id) -> str:
    try:
        path = Path(os.getenv("DATA_DIR", ".")) / "bot_state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("users", {}).get(str(chat_id), {}).get("language", "fa")
    except Exception:
        return "fa"


def localize(text: str, lang: str) -> str:
    return translate_en(text) if lang == "en" else text


def localize_markup(markup, lang: str):
    if lang != "en" or not isinstance(markup, InlineKeyboardMarkup):
        return markup
    rows = []
    for row in markup.inline_keyboard:
        rows.append([InlineKeyboardButton(
            text=translate_en(button.text), url=button.url,
            callback_data=button.callback_data, switch_inline_query=button.switch_inline_query,
            switch_inline_query_current_chat=button.switch_inline_query_current_chat,
            login_url=button.login_url, web_app=button.web_app,
            callback_game=button.callback_game, pay=button.pay,
        ) for button in row])
    return InlineKeyboardMarkup(rows)


class LocalizedBot(ExtBot):
    async def send_message(self, chat_id, text, *args, **kwargs):
        lang = language_for(chat_id)
        kwargs["reply_markup"] = localize_markup(kwargs.get("reply_markup"), lang)
        return await super().send_message(chat_id, localize(text, lang), *args, **kwargs)

    async def edit_message_text(self, text, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        lang = language_for(chat_id) if chat_id is not None else "fa"
        kwargs["reply_markup"] = localize_markup(kwargs.get("reply_markup"), lang)
        return await super().edit_message_text(localize(text, lang), *args, **kwargs)
