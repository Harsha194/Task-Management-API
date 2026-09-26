# Task Management REST API

## Overview

This project is a secure Task Management REST API built with Python, FastAPI, MongoDB Atlas, and JWT authentication. It allows users to register, log in, manage their own tasks, filter and search tasks, paginate results, and view user-scoped analytics.

## Features

- User registration
- Secure password hashing with bcrypt
- JWT-based login and bearer authentication
- Current-user endpoint
- Authenticated task CRUD
- User-level task ownership enforcement
- Task status filtering
- Task priority filtering
- Case-insensitive text search
- Pagination metadata
- MongoDB aggregation analytics
- Automated test coverage
- Swagger/OpenAPI documentation

## Technology Stack

- Python
- FastAPI
- Uvicorn
- MongoDB Atlas
- PyMongo
- Pydantic
- JWT authentication
- Passlib + bcrypt
- Pytest

## Architecture

The project is organized into a simple modular layout:

- app/main.py
- app/config.py
- app/database.py
- app/models/
- app/schemas/
- app/routes/
- app/services/
- app/dependencies/
- app/utils/
- tests/

## Authentication

Most protected routes require a bearer token:

```http
Authorization: Bearer <jwt-token>
```

The current-user dependency validates the token and loads the authenticated user from MongoDB.

## API Endpoints

| Method | Endpoint | Purpose | Auth |
| --- | --- | --- | --- |
| GET | /health | API health check | No |
| GET | /health/db | MongoDB connectivity check | No |
| POST | /auth/register | Register a new user | No |
| POST | /auth/login | Log in and receive a JWT | No |
| GET | /auth/me | Get authenticated user profile | Yes |
| POST | /tasks | Create a task | Yes |
| GET | /tasks | List tasks with filters, search, and pagination | Yes |
| GET | /tasks/analytics | Get user-specific task analytics | Yes |
| GET | /tasks/{task_id} | Get one task by ID | Yes |
| PUT | /tasks/{task_id} | Update one task by ID | Yes |
| DELETE | /tasks/{task_id} | Delete one task by ID | Yes |

## Task Management

Each task belongs to the authenticated user. Users can create, read, update, and delete only their own tasks.

### Supported task fields

- title
- description
- status: pending, in_progress, completed
- priority: low, medium, high
- due_date

## Filtering, Search, and Pagination

The GET /tasks endpoint supports:

- `status`
- `priority`
- `search`
- `page`
- `limit`

Example requests:

```http
GET /tasks
GET /tasks?status=pending
GET /tasks?priority=high
GET /tasks?search=fastapi
GET /tasks?page=2&limit=5
GET /tasks?status=pending&priority=high&search=api&page=1&limit=10
```

Results include pagination metadata:

- page
- limit
- total
- pages

## Analytics

GET /tasks/analytics returns statistics for the authenticated user only.

Example response:

```json
{
  "total_tasks": 20,
  "completed_tasks": 8,
  "pending_tasks": 7,
  "in_progress_tasks": 5,
  "low_priority_tasks": 4,
  "medium_priority_tasks": 10,
  "high_priority_tasks": 6,
  "completion_rate": 40.0
}
```

If a user has no tasks, the endpoint returns zeros and `completion_rate` as `0.0`.

## Project Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Task_management_API
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and update it with your own values:

```bash
copy .env.example .env
```

Then set your MongoDB and JWT values in the `.env` file.

Example structure:

```env
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster-url>/<database>?retryWrites=true&w=majority
DATABASE_NAME=task_management
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Start the application

```bash
python -m uvicorn app.main:app --reload --port 8081
```

### 6. Open Swagger

```text
http://127.0.0.1:8081/docs
```

## Testing

Run the full suite:

```bash
python -m pytest -q
```

Verified baseline:

- 36 passed
- 1 warning
- exit code 0

The warning is a non-blocking Starlette/anyio deprecation warning from the test client. It does not affect application behavior.

## Security

- Passwords are hashed before storage.
- Passwords are never returned in API responses.
- JWT tokens are required for protected routes.
- Task and analytics queries are scoped to the authenticated user only.
- Another user's tasks are not exposed through CRUD, filtering, search, pagination, or analytics.

## Notes

This project is a clean, interview-friendly FastAPI backend for task management with MongoDB and JWT-based security. It is designed for learning and presentation rather than large-scale production infrastructure.
