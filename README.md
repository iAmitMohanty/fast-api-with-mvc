# Customer Management API

A production-ready RESTful API built with **FastAPI**, **SQLAlchemy 2.0**, and **MySQL**. It provides full CRUD operations for customer records, protected by JWT-based authentication with access/refresh token support.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Authentication Flow](#authentication-flow)
- [Request & Response Format](#request--response-format)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Logging](#logging)

---

## Features

- JWT authentication with short-lived access tokens and long-lived refresh tokens
- Secure password hashing with bcrypt
- Full CRUD for customer records
- Standardised JSON response envelope (`status`, `message`, `data`, `error`)
- Global validation error handler with field-level error details
- Daily rotating log files (retained for 30 days)
- SQLAlchemy connection pool with `pool_pre_ping` for reliable database connections
- Auto table creation on startup

---

## Tech Stack

| Layer | Library / Tool |
|---|---|
| Web framework | FastAPI 0.115.0 |
| ASGI server | Uvicorn 0.30.6 (standard) |
| ORM | SQLAlchemy 2.0.36 |
| Database | MySQL (via PyMySQL 1.1.1) |
| Data validation | Pydantic 2.9.2 + pydantic-settings 2.5.2 |
| Authentication | python-jose 3.3.0 (JWT) |
| Password hashing | passlib 1.7.4 + bcrypt 3.2.2 |
| Cryptography | cryptography 49.0.0 |
| Email validation | email-validator 2.3.0 |

---

## Project Structure

```
fast-api-with-mvc/
├── app/
│   ├── main.py                  # FastAPI app, route definitions, startup
│   ├── controllers/
│   │   ├── auth_controller.py   # Register, login, refresh, logout logic
│   │   └── customer_controller.py
│   ├── repositories/
│   │   ├── user_repository.py   # DB queries for User model
│   │   └── customer_repository.py
│   ├── models/
│   │   ├── user.py              # SQLAlchemy User model
│   │   └── customer.py          # SQLAlchemy Customer model
│   ├── schemas/
│   │   ├── auth_schema.py       # Pydantic schemas for auth
│   │   └── customer_schema.py   # Pydantic schemas for customers
│   ├── core/
│   │   ├── config.py            # App settings via pydantic-settings
│   │   ├── security.py          # JWT & password utilities
│   │   ├── dependencies.py      # FastAPI dependency: get_current_user
│   │   └── logging_config.py    # Daily rotating file + console logging
│   ├── db/
│   │   └── database.py          # SQLAlchemy engine, session, Base
│   └── utils/
│       └── response_wrapper.py  # Standardised API response helpers
├── logs/                        # Daily log files (auto-created)
├── .env                         # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Database Models

### `users` table

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | UUID primary key |
| `username` | VARCHAR(100) | Unique, indexed |
| `email` | VARCHAR(150) | Unique, indexed |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `is_active` | BOOLEAN | Account status (default `true`) |
| `refresh_token` | VARCHAR(512) | Current refresh token (nullable) |
| `refresh_token_expiry_time` | DATETIME | Refresh token expiry (nullable) |
| `created_at` | DATETIME | Server default `NOW()` |
| `updated_at` | DATETIME | Auto-updated on change |

### `customers` table

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) | UUID primary key |
| `name` | VARCHAR(100) | Required |
| `email` | VARCHAR(150) | Unique, indexed |
| `phone` | VARCHAR(20) | Optional |
| `address` | VARCHAR(255) | Optional |
| `created_at` | DATETIME | Server default `NOW()` |
| `updated_at` | DATETIME | Auto-updated on change |

---

## API Endpoints

### Auth (public)

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive tokens |
| `POST` | `/auth/refresh` | Exchange refresh token for new token pair |
| `POST` | `/auth/logout` | Invalidate the current refresh token |

### Customers (protected — requires Bearer token)

| Method | Path | Description |
|---|---|---|
| `GET` | `/customers` | List all customers |
| `GET` | `/customers/{customer_id}` | Get a customer by ID |
| `POST` | `/customers` | Create a new customer |
| `PUT` | `/customers/{customer_id}` | Update a customer |
| `DELETE` | `/customers/{customer_id}` | Delete a customer |

---

## Authentication Flow

```
1. POST /auth/register  →  Create user account
2. POST /auth/login     →  Returns { access_token, refresh_token, token_type }
3. Use access_token in header: Authorization: Bearer <access_token>
4. When access_token expires, POST /auth/refresh with { refresh_token }
5. POST /auth/logout (authenticated) to revoke the refresh token
```

**Token lifetimes (defaults, overridable via `.env`):**

| Token | Lifetime |
|---|---|
| Access token | 30 minutes |
| Refresh token | 7 days |

---

## Request & Response Format

All endpoints return a consistent envelope:

```json
{
  "status": "success",
  "message": "Human-readable message",
  "data": { ... },
  "error": null
}
```

On validation failure (422):

```json
{
  "status": "error",
  "message": "Validation failed",
  "data": null,
  "error": [
    { "field": "body.email", "message": "value is not a valid email address" }
  ]
}
```

### Register — `POST /auth/register`

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secret123"
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": { "id": "uuid", "username": "johndoe", "email": "john@example.com" }
}
```

### Login — `POST /auth/login`

**Request:**
```json
{
  "username": "johndoe",
  "password": "secret123"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "<jwt>",
    "expiresAt": "<expire token time>",
    "userId": "<user id>",
    "userName": "<user name>",
    "displayName": "<dispaly name>",
    "refresh_token": "<token>"
  }
}
```

### Create Customer — `POST /customers`

**Request:**
```json
{
  "name": "Acme Corp",
  "email": "contact@acme.com",
  "phone": "+1-555-0100",
  "address": "123 Main St, Springfield"
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Customer created successfully",
  "data": {
    "id": "uuid",
    "name": "Acme Corp",
    "email": "contact@acme.com",
    "phone": "+1-555-0100",
    "address": "123 Main St, Springfield",
    "created_at": "2026-07-01T07:00:00",
    "updated_at": "2026-07-01T07:00:00"
  }
}
```

---

## Configuration

All configuration is loaded from a `.env` file in the project root via `pydantic-settings`.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://root:password@localhost:3306/customer_db` | MySQL connection string |
| `APP_TITLE` | `Customer Management API` | OpenAPI title |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `False` | Enables SQLAlchemy query logs and DEBUG-level logging |
| `JWT_SECRET_KEY` | *(must be set)* | Secret key for signing JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL in days |

**Example `.env`:**
```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/customer_db
APP_TITLE=Customer Management API
APP_VERSION=1.0.0
DEBUG=False
JWT_SECRET_KEY=replace-this-with-a-long-random-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL server running locally (or update `DATABASE_URL` accordingly)

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd fast-api-crud

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env     # Windows
# cp .env.example .env     # macOS / Linux
# Then edit .env with your database credentials and JWT secret

# 5. Create the MySQL database
# In MySQL:
# CREATE DATABASE customer_db;

# 6. Run the server (tables are created automatically on startup)
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

---

## Logging

Logs are written to both the console and a daily rotating file in the `logs/` directory.

```
logs/
├── app-2026-07-01.log
├── app-2026-07-02.log
└── ...
```

- A new file is created at midnight automatically.
- The last **30 days** of log files are retained.
- Log format: `YYYY-MM-DD HH:MM:SS | LEVEL    | module | message`
- When `DEBUG=True`, SQLAlchemy query logs are also emitted.
