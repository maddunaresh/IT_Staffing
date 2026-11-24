from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import engine
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.recruiting.router import router as recruiting_router
from app.modules.lookups.router import router as lookups_router

app = FastAPI(title="IT Staffing API")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(recruiting_router)
app.include_router(lookups_router)



class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/database")
def database_health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1")).scalar_one()

    return {"database": "connected"}