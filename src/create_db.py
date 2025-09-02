import asyncio
from src.database import engine, Base

async def init_models():
    """

    :return:
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Базу даних ініціалізовано")

if __name__ == "__main__":
    asyncio.run(init_models())
