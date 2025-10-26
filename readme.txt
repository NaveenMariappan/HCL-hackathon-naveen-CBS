# CBS (Core Banking System) - HCL Hackathon

User Creation & KYC
mandatory details: Name, DOB, Address, PAN, Email, Ph no
KYC Documents, 

FAST API for backend
MySQL for Database
JWT for auth

username : Email address
password : 8 char
role: customer, admin, auditor

For Customer Access till Acc creation, tran logs, loan application, money transfer

For Admin Access till Loan approval, manage acc, trans log

For Auditor Access till Audit log 

unit test with 10 cases each role

Small core-banking prototype implementing:
- User creation + KYC
- Account creation and transaction logs
- Loan application workflow
- JWT authentication and role-based access (customer, admin, auditor)
- FastAPI backend, MySQL database

Status
- Concept and requirements captured. Next steps: implement endpoints, DB migrations, CI, tests.

Tech stack
- Backend: FastAPI (Python)
- DB: MySQL 
- Auth: JWT 
- Testing: pytest,postman

Core data & roles
- Required user fields: name, dob, address, PAN, email, phone
- KYC documents: file references stored in DB or object store

- Roles:
  - customer: create accounts, view transaction logs, apply for loans, transfer money
  - admin: approve loans, manage accounts, view/manage transaction logs
  - auditor: access audit logs and read-only views for compliance

Authentication and passwords
- Username = email
- Password: minimum 8 characters (enforce complexity as needed)
- JWT for authentication; role claim inside token
- Secure password hashing (bcrypt/argon2)

Suggested database tables (high level)
- users (id, name, email, password_hash, dob, phone, address, pan, role, created_at, updated_at)
- kyc_documents (id, user_id, doc_type, file_path, status, uploaded_at)
- accounts (id, user_id, account_number, type, balance, status, created_at)
- transactions (id, account_id, type, amount, balance_after, description, created_at)
- loans (id, user_id, amount, status, applied_at, approved_by, approved_at)
- audit_logs (id, actor_id, action, resource_type, resource_id, details, timestamp)

API surface (examples)
- Auth
  - POST /auth/register — register user + start KYC
  - POST /auth/login — returns access + refresh tokens
  - POST /auth/refresh — refresh token
- Customer
  - POST /accounts — create account
  - GET /accounts — list user accounts
  - GET /accounts/{id}/transactions — transaction log
  - POST /transactions/transfer — transfer money between accounts (checks balance)
  - POST /loans — apply for loan
- Admin
  - GET /loans — list pending loans
  - POST /loans/{id}/approve — approve loan
  - PATCH /accounts/{id} — manage account (freeze/close)
- Auditor
  - GET /audit/logs — read-only access to audit logs

Security considerations
- Validate and sanitize all inputs (PAN format, phone, email)
- Rate-limit critical endpoints (login, transfers)
- Use parameterized queries / ORM to avoid SQL injection
- Store KYC docs securely (S3 or similar) and keep access logs
- Rotate JWT secrets and set reasonable token lifetimes

Dev / Run instructions (local)
1. Create virtual env: python -m venv .venv && source .venv/bin/activate
2. Install: pip install -r requirements.txt (include fastapi, uvicorn, sqlalchemy, alembic, pydantic, PyJWT, bcrypt)
3. Configure environment variables (see .env example below)
4. Run DB migrations (alembic upgrade head)
5. Start server: uvicorn app.main:app --reload

Recommended env variables
- DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/cbs
- JWT_SECRET=your-secret
- JWT_ALGORITHM=HS256
- ACCESS_TOKEN_EXPIRE_MINUTES=15
- REFRESH_TOKEN_EXPIRE_DAYS=7
- S3_BUCKET_NAME (if using object store)

Password and validation rules (recommendation)
- Minimum 8 characters, include at least one uppercase, one lowercase, one number
- Rate-limit failed logins and lock account after N attempts

Testing and quality
- Target: unit + integration tests with coverage >= 80%
- You requested 50 cases per role — create tests covering auth, happy paths and failures, role-based access, edge cases and security checks.
- Use pytest, pytest-asyncio, and httpx AsyncClient for endpoint testing. Use factories/fixtures for test data.

Next steps (recommended)
- Create initial data models and migrations
- Implement auth endpoints and JWT middleware
- Implement one role flow end-to-end (customer) and write tests
- Add CI (GitHub Actions) to run tests and linters on PRs

If you want, I can:
- scaffold the FastAPI project structure,
- add models and Alembic migrations,
- or generate the initial set of pytest tests (50 per role) and a Postman collection.
