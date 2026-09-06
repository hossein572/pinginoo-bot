"""Run the bot and Mini App together; one worker/machine per Telegram token."""

import asyncio
import logging
import os

import uvicorn

from bot import build_application
from settings import load_settings
from webapp import app


async def main():
    config = load_settings()
    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")), log_level="info")
    )
    if os.getenv("PINGINOO_DEMO") == "1" or not config["bot_token"]:
        if not config["bot_token"] and os.getenv("PINGINOO_DEMO") != "1":
            logging.warning(
                "No BOT_TOKEN: the web frontend is running but production APIs require Telegram authentication"
            )
        await server.serve()
        return
    application = build_application(config)
    async with application:
        await application.post_init(application)
        await application.start()
        await application.updater.start_polling(allowed_updates=["message", "callback_query"])
        try:
            await server.serve()
        finally:
            await application.updater.stop()
            await application.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    asyncio.run(main())
