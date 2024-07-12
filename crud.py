from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Item  # Ensure this import is correct

async def get_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()

async def create_item(db: AsyncSession, name: str, description: str):
    item = Item(name=name, description=description)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item