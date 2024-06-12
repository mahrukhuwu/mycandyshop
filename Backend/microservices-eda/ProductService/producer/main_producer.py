from contextlib import asynccontextmanager
from typing import Annotated
from aiokafka import AIOKafkaProducer
import events_pb2
import settings
from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import SQLModel, Field, Session
import httpx

class ProductModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    price: float
    quantity: int
    description: str
    availability: bool
    user_id: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan, title="Product Service Producer", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8000",
            "description": "Development Server"
        }
    ])

@app.get("/")
def read_root():
    return {"App": "Product Service Producer"}

async def get_producer():
    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()

async def get_current_user(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get("http://kong:8001/users/me", headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not validate credentials")
        return response.json()

@app.post("/products/", response_model=ProductModel)
async def create_product(
    product: ProductModel,
    producer: Annotated[AIOKafkaProducer, Depends(get_producer)],
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token)
    product.user_id = current_user["id"]
    product_proto = events_pb2.Product(
        id=product.id,
        name=product.name,
        price=product.price,
        quantity=product.quantity,
        description=product.description,
        availability=product.availability,
        user_id=product.user_id
    )
    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(settings.KAFKA_ORDER_TOPIC, serialized_product)
    return {"message": "Product sent to Kafka", "id": product.id}


















# from contextlib import asynccontextmanager
# from typing import Annotated
# from aiokafka import AIOKafkaProducer
# import events_pb2
# import settings
# from fastapi import Depends, FastAPI
# from sqlmodel import SQLModel, Field

# class ProductModel(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True)
#     name: str
#     price: float
#     quantity: int
#     description: str
#     availability: bool

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield

# app = FastAPI(lifespan=lifespan, title="Product Service Producer", 
#     version="0.0.1",
#     servers=[
#         {
#             "url": "http://127.0.0.1:8000",
#             "description": "Development Server"
#         }
#     ])

# @app.get("/")
# def read_root():
#     return {"App": "Product Service Producer"}

# async def get_producer():
#     producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
#     await producer.start()
#     try:
#         yield producer
#     finally:
#         await producer.stop()

# @app.post("/products/", response_model=ProductModel)
# async def create_product(
#     product: ProductModel,
#     producer: Annotated[AIOKafkaProducer, Depends(get_producer)]
# ):
#     product_proto = events_pb2.Product(
#         id=product.id,
#         name=product.name,
#         price=product.price,
#         quantity=product.quantity,
#         description=product.description,
#         availability=product.availability
#     )
#     serialized_product = product_proto.SerializeToString()
#     await producer.send_and_wait(settings.KAFKA_ORDER_TOPIC, serialized_product)
#     return {"message": "Product sent to Kafka" , "id": product.id}