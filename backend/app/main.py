from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.agent import router as agent_router
from app.routes.rag import router as rag_router
from app.routes import sql as sql_routes 
from app.routes import eval as eval_route


def create_app() -> FastAPI:
    app = FastAPI(title="Project 7 - Multi-Tool Agent", version="0.2.0")

    app.include_router(health_router, tags=["health"])
    app.include_router(agent_router, tags=["agent"])
    app.include_router(rag_router, tags=["rag"])
    app.include_router(sql_routes.router)  
    app.include_router(eval_route.router)
 

    return app

app = create_app()
