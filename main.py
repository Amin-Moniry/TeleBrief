import asyncio

from digest_core import run_digest, MY_CHAT_ID, HOURS_WINDOW


async def main():
    count = await run_digest(MY_CHAT_ID, hours=HOURS_WINDOW, include_date_header=False)
    print(f"Done. Sent {count} messages.")


if __name__ == "__main__":
    asyncio.run(main())