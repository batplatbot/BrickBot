import aiohttp


async def send_discord_webhook(webhook_url: str, title: str, description: str, color: int = 0x5865F2):
    """Send a message to Discord webhook."""
    if not webhook_url:
        return

    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "timestamp": "2026-01-01T00:00:00.000Z"
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as resp:
                return resp.status in (200, 204)
    except Exception:
        return False
