# 🧱 BrickBot – Telegram Community Management Bot

A professional, modular Telegram bot built with **Python 3.12+** and **python-telegram-bot v22.8**.

## Features

### BrickBot Basic
- `/start`, `/help`, `/ping`, `/id`, `/userinfo`, `/about`
- Welcome/goodbye messages
- Admin commands
- Group statistics

### BrickBot Premium
- Moderation (`/warn`, `/mute`, `/ban`, `/unban`, `/clear`)
- Auto-moderation (anti-spam, anti-link, anti-invite, word filter, scam detection)
- Logging (message edits/deletions, member joins/leaves, admin actions)
- Support system (FAQ, conversation flow)
- Utility (`/poll`, `/remind`, `/announce`, `/qr`, `/random`, `/dice`, `/coinflip`, `/timestamp`)
- Statistics (user, group, command usage)

## Installation

```bash
git clone https://github.com/batplatbot/brickbot-telegram
cd brickbot-telegram
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your token
python bot.py
