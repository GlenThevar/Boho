from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import api_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Boho - Firewall Policy Simulation Platform",
    description="Deterministic offline firewall policy simulator and testing platform (Stage 1).",
    version="1.0.0",
)

# CORS configuration restricted to local frontend development origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Boho Firewall Simulation Engine",
        "stage": 1,
        "mode": "offline-simulation"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
