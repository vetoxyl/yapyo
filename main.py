import asyncio
from presale_bot import ArbitrumPresaleBot

if __name__ == "__main__":
    bot = ArbitrumPresaleBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        bot.stop() 