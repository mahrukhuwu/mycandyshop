from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine, Session, Field
import events_pb2
import settings
import asyncio

class Product(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    price: float
    quantity: int
    description: str
    availability: bool
    user_id: int

connection_string = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={}, pool_recycle=300)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    create_db_and_tables()
    print("Tables created.")
    
    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(consume())
    print("Consumer task started.")
    
    yield
    
    consumer_task.cancel()
    await consumer_task
    print("Consumer task cancelled.")

app = FastAPI(lifespan=lifespan, title="Product Service Consumer", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8004",
            "description": "Development Server"
        }
    ])

@app.get("/")
async def root():
    return {"message": "Product Consumer"}

def save_product(session, product_data):
    print("Saving product...")
    product = Product(
        id=product_data.id,
        name=product_data.name,
        price=product_data.price,
        quantity=product_data.quantity,
        description=product_data.description,
        availability=product_data.availability,
        user_id=product_data.user_id
    )
    session.add(product)
    session.commit()

async def consume():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_ORDER_TOPIC,
        bootstrap_servers=settings.BOOTSTRAP_SERVER,
        group_id="product_consumer_group"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            product_proto = events_pb2.Product()
            product_proto.ParseFromString(msg.value)
            with Session(engine) as session:
                save_product(session, product_proto)
    finally:
        await consumer.stop()












































# from contextlib import asynccontextmanager
# from aiokafka import AIOKafkaConsumer
# from fastapi import FastAPI
# from sqlmodel import SQLModel, create_engine, Session, Field
# import events_pb2
# import settings
# import asyncio

# class Product(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True)
#     name: str
#     price: float
#     quantity: int
#     description: str
#     availability: bool

# connection_string = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
# engine = create_engine(connection_string, connect_args={}, pool_recycle=300)

# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Creating tables...")
#     create_db_and_tables()
#     print("Tables created.")
    
#     loop = asyncio.get_event_loop()
#     consumer_task = loop.create_task(consume())
#     print("Consumer task started.")
    
#     yield
    
#     consumer_task.cancel()
#     await consumer_task
#     print("Consumer task cancelled.")

# app = FastAPI(lifespan=lifespan, title="Product Service Consumer", 
#     version="0.0.1",
#     servers=[
#         {
#             "url": "http://127.0.0.1:8001",
#             "description": "Development Server"
#         }
#     ])

# @app.get("/")
# async def root():
#     return {"message": "Product Consumer"}

# def save_product(session, product_data):
#     print("Saving product...")
#     product = Product(
#         id=product_data.id,
#         name=product_data.name,
#         price=product_data.price,
#         quantity=product_data.quantity,
#         description=product_data.description,
#         availability=product_data.availability
#     )
#     session.add(product)
#     session.commit()
#     print("Product saved.")

# async def consume():
#     consumer = AIOKafkaConsumer(
#         settings.KAFKA_ORDER_TOPIC,
#         bootstrap_servers=settings.BOOTSTRAP_SERVER,
#         group_id='product_group',
#         auto_offset_reset='earliest'  # Ensure this is set to read from the beginning
#     )
#     await consumer.start()
#     print("Consumer started.")
#     try:
#         while True:
#             async for msg in consumer:
#                 print("Received message from Kafka.")
#                 try:
#                     product_data = events_pb2.Product()
#                     product_data.ParseFromString(msg.value)
#                     print(f"Parsed product data: {product_data}")
                    
#                     # Using sync session in an async function
#                     with Session(engine) as session:
#                         save_product(session, product_data)
#                         print(f"Saved product with ID: {product_data.id}")
#                 except Exception as e:
#                     print(f"Error processing message: {e}")
#     except Exception as e:
#         print(f"Error consuming messages: {e}")
#     finally:
#         await consumer.stop()
#         print("Consumer stopped.")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
