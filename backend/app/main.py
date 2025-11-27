from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import ws, models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(ws.router, prefix="/ws", tags=["websockets"])
app.include_router(models.router, prefix="/api", tags=["models"])

@app.get("/")
async def root():
    return {"message": "NeuralCanvas Brain is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
