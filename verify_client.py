import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    try:
        print("Expected properties:")
        print("api_key:", hasattr(db, 'api_key'))
        print("webhook_endpoint:", hasattr(db, 'webhook_endpoint'))
        
        # Also list all properties to debug
        print("\nAll Prisma properties:")
        props = [p for p in dir(db) if not p.startswith('_')]
        print(props)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
