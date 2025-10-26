from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.routers import auth, kyc, accounts, transfers, transactions, dashboard
from app.database import engine
from app import models

# ✅ Create app FIRST before using it
app = FastAPI(title="Core Banking System API")

# ✅ Swagger Authorization Fix
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Core Banking System API",
        version="1.0.0",
        description="Core Banking System Backend - Auth, KYC, Accounts, Transfers, Dashboard",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

# ✅ Include Routers
app.include_router(auth.router)
app.include_router(kyc.router)
app.include_router(accounts.router)
app.include_router(transfers.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)

# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to Core Banking System API"}

# ✅ Create database tables
models.Base.metadata.create_all(bind=engine)
