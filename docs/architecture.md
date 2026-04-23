# Архітектура системи

## 🛠 Технологічний стек

- **Мова:** Python 3.12+
- **Фреймворк:** FastAPI (для високої швидкості та асинхронності).
- **База даних:** PostgreSQL (основне сховище).
- **ORM:** SQLAlchemy 2.0.
- **Контейнеризація:** Docker & Docker Compose.
- **Типізація:** Pydentic.
- **Міграції:** alembic.

## 🏗 Структура системи

- **API Layer:** Обробка HTTP-запитів, валідація даних (Pydantic).
- **Service Layer:** Основна бізнес-логіка (розрахунки, правила).
- **Data Access Layer:** Взаємодія з базою даних через репозиторії.
- **Models** Моделі бази даних
- **Schemas** схеми даних

## 📊 Схема бази даних (Entities)

Короткий опис основних таблиць та зв'язків:

- **Products:** id, name, description, img_url, product_url, supplier_category_name, supplier_name, sku, external_id, price, price_old, stock_quantity, currency, stock_status, category_id(зв'язок з категоріями), supplier_deleted_at, created_at, updated_at (можливе оновлення)

- **Categories:** id, name

- **ProductStockHistory:** id, product_id(зв'язок з товаром), quantity, created_at

## 🔌 Інтеграції зі сторонніми сервісами

1. **AI:** інтеграція з копайлот для отримання категорій за назвою товару

## 🔄 Потік даних (Data Flow)

1. Система парсить товари у постачальників
2. Товари додаються в бд
3. Якшо в товарів нема категорії то вона визначається за допомогою ai
4. Товари віддаються по ендпоінту
