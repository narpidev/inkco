import asyncio
import asyncpg


async def main():
    for ssl in ("disable", "prefer"):
        try:
            conn = await asyncpg.connect(
                host="127.0.0.1",
                port=5432,
                user="postgres",
                password="TU_PASSWORD",
                database="ink_lab",
                ssl=ssl,
            )
            print(ssl, "-> OK", await conn.fetchval("select version()"))
            await conn.close()
        except Exception as e:
            print(ssl, "-> FALLO:", type(e).__name__, e)


asyncio.run(main())