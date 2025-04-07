# import asyncio
# import logging
# import uuid

# from datetime import datetime
# from faker import Faker

# from motor.motor_asyncio import AsyncIOMotorClient
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.sql import text

# fake = Faker()

# # Подключение к PostgreSQL
# POSTGRES_DSN = "postgresql+asyncpg://app:123qwe@db:5432/movies_database"
# MONGO_DSN = "mongodb://mongodb:27017"
# MONGO_DB = "cinema"

# # Настройка логирования
# logging.basicConfig(level=logging.INFO)

# # Подключение к PostgreSQL
# engine = create_async_engine(POSTGRES_DSN, echo=True, pool_size=10, max_overflow=5, pool_recycle=300)
# AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# # Подключение к MongoDB
# mongo_client = AsyncIOMotorClient(MONGO_DSN)
# mongo_db = mongo_client[MONGO_DB]
# users_collection = mongo_db["users"]

# # Функция для генерации случайных пользователей (с UUID)
# def generate_user():
#     return {
#         'id': str(uuid.uuid4()),
#         'login': fake.user_name(),
#         'email': fake.email(),
#         'password': fake.password(),
#         'first_name': fake.first_name(),
#         'last_name': fake.last_name(),
#         'created_at': datetime.now(),
#         'last_login': datetime.now(),
#         'is_admin': False,
#         'is_staff': False,
#         'is_active': True,
#     }

# # Генерация и вставка пользователей в PostgreSQL и MongoDB
# async def save_user_to_db(session, user):
#     try:
#         # Вставка данных в PostgreSQL
#         insert_query = text("""
#             INSERT INTO users (id, login, email, password, first_name, last_name, created_at, last_login, is_admin, is_staff, is_active)
#             VALUES (:id, :login, :email, :password, :first_name, :last_name, :created_at, :last_login, :is_admin, :is_staff, :is_active)
#             RETURNING id;
#         """)

#         result = await session.execute(insert_query, user)
#         user_id = result.scalar()

#         # Преобразуем UUID в строку перед вставкой в MongoDB
#         user_id_str = str(user_id)

#         # Вставка данных в MongoDB
#         users_collection.insert_one({
#             "user_id": user_id_str,
#             "username": user['login'],
#             "email": user['email'],
#             "password": user['password']
#         })

#         logging.info(f"User {user['login']} saved with ID {user_id}")
#         await session.commit()
#     except SQLAlchemyError as e:
#         logging.error(f"Error saving user: {e}")
#         await session.rollback()
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}")

# # Главная асинхронная функция
# async def main():
#     async with AsyncSessionLocal() as session:
#         for _ in range(10):
#             user_data = generate_user()
#             await save_user_to_db(session, user_data)
#         logging.info("Users saved successfully.")

# if __name__ == "__main__":
#     asyncio.run(main())
