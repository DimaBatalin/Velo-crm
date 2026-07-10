from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import create_tables
from app.core.config import settings
from app.core.deps import get_current_user

from app.api.auth import router as auth_router
from app.api.people import router as people_router
from app.api.bikes import router as bikes_router
from app.api.passport import router as passport_router
from app.api.parts import router as parts_router
from app.api.services import router as services_router
from app.api.repairs import router as repairs_router
from app.api.rentals import router as rentals_router
from app.api.enums import router as enums_router
from app.api.tags import router as tags_router
from app.api.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="VELO API",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth required)
app.include_router(auth_router)

# Protected routes (JWT required)
protected = {"dependencies": [Depends(get_current_user)]}

app.include_router(people_router,  **protected)
app.include_router(bikes_router,   **protected)
app.include_router(passport_router,**protected)
app.include_router(parts_router,   **protected)
app.include_router(services_router,**protected)
app.include_router(repairs_router, **protected)
app.include_router(rentals_router, **protected)
app.include_router(enums_router,   **protected)
app.include_router(tags_router,    **protected)
app.include_router(analytics_router, **protected)


@app.get("/")
async def root():
    return {"message": "VELO API"}
