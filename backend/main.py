from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.auth_controller import router as auth_router
from backend.controllers.favorites_controller import router as favorites_router
from backend.controllers.movies_controller import router as movies_router
from backend.controllers.recommendations_controller import router as recommendations_router



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies_router, prefix="/api/movies", tags=["Movies"])
app.include_router(favorites_router, prefix="/api/favorites", tags=["Favorites"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(recommendations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
