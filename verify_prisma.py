import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    # We don't necessarily need to connect to DB to check attribute existence on the class/instance structure 
    # but connecting ensures the client is initialized fully if needed.
    # However, to be safe and fast, let's just inspect the instance.
    print("Inspecting Prisma client...")
    if hasattr(db, 'organization'):
        print("SUCCESS: db.organization exists.")
    else:
        print("FAILURE: db.organization DOES NOT exist.")

if __name__ == "__main__":
    asyncio.run(main())
