# TeleBrief Bilingual Upgrade

## What changed

- `/start` now opens a persistent Persian/English language picker.
- `/language` lets users switch language at any time.
- English users receive an English, left-to-right UI, keyboard labels, errors, loading states, pagination, channel management, admin analytics, and command menu.
- AI and cybersecurity prompts require English-only prose for English users.
- Crypto/geopolitical prompts, market overviews, highlights, currency reports, relative times, metadata, and source labels have native English formatters.
- Persian behavior remains the default and existing user data is backward-compatible.

## New files

- `ui_en.py`: English UI copy and dynamic-message localization.
- `ui_fa.py`: Persian UI adapter and language labels.
- `localized_bot.py`: per-user UI/keyboard localization at Telegram delivery time.

## Deployment

No new dependency or environment variable is required. Deploy normally with `worker: python command_bot.py`. Existing `bot_state.json` entries gain a `language` field after a user chooses a language.
