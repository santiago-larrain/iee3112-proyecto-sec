from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import casos

app = FastAPI(
    title="SEC Reclamos API",
    description="API para gestión de reclamos SEC",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(casos.router, prefix="/api", tags=["casos"])

@app.get("/")
def root():
    return {"message": "SEC Reclamos API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

