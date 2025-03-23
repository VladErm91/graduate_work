📌 Архитектура сервиса
Мы используем DDD (Domain-Driven Design) и чистую архитектуру, разделяя код на слои:

api/ — контроллеры (endpoints)

services/ — бизнес-логика

repositories/ — работа с базами данных

models/ — SQLAlchemy-модели

schemas/ — Pydantic-схемы

core/ — настройки, конфиги

main.py — точка входа