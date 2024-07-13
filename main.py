import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select


PGPASSWORD = os.environ["POSTGRES_PASSWORD"]
PGPORT = os.environ["PGPORT"]

DATABASE_URL = f"postgresql+asyncpg://postgres:{PGPASSWORD}@viaduct.proxy.rlwy.net:{PGPORT}/railway"

app = FastAPI()

origins = ["*"]  # Update this to the domain of your frontend app

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create a SQLAlchemy engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Create a Base class for our models
Base = declarative_base()

# Define an example model
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)


# Create the database tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

class ItemCreate(BaseModel):
    name: str
    description: str

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = select(Item).where(Item.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        if item:
            return item
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/items/")
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_item = Item(name=item.name, description=item.description)
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
