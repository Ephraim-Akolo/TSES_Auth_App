# TSES Authentication Service
A modular Django-based authentication service providing email-based One-Time Passwords (OTP). This service features Redis-backed rate limiting, asynchronous task processing via Celery, and comprehensive API documentation.

## Quick Start
The project is fully containerized. You can launch the entire stack—including the Django API, PostgreSQL database, Redis cache, and Celery worker—with a single command

```bash
docker compose up --build
```

The API will be available at http://localhost:10000

## Environment Variables
Create a .env file in the root directory. Refer to `.env.example` for required keys.

## Tech Stack
* Framework: Django & Django REST Framework (DRF) 
* Database: PostgreSQL 
* Task Queue: Celery & Redis 
* Authentication: djangorestframework-simplejwt 
* Documentation: drf-spectacular

## Features
* Passwordless Auth: OTP generation with 5-minute TTL stored in Redis.
* Smart Rate Limiting: Atomic Redis counters to prevent brute force (3 requests/10m per email; 10 requests/1h per IP).
* Security Lockout: Automatic 15-minute lockout after 5 failed verification attempts.
* Async Processing: Background tasks for email delivery and audit logging via Celery.
* Audit Trail: Detailed logs for all auth events with filtering and pagination.

## API Documentation
Once the system is running, access the interactive Swagger UI to explore endpoints, schemas, and example requests: [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/) 

## API Endpoints
### Authentication
* **POST** /api/v1/auth/otp/request: *Initiates an OTP request for an email.*
* **POST** /api/v1/auth/otp/verify: *Validates OTP and returns JWT tokens.*
### Audit
* **GET** /api/v1/audit/logs: *Paginated, filterable list of audit entries (Requires JWT).*
