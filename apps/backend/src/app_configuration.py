from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from settings import API_KEY
from src.api import router
from src.utils.logger import logger


def setup(app: FastAPI):
    logger.info("Setting up application...")

    # OpenAPI 스키마 커스터마이징
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
            
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
        
        openapi_schema["security"] = [{"ApiKeyAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # API 키 검증 미들웨어
    async def verify_api_key(request: Request, call_next):
        if request.url.path.startswith("/api"):
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key != API_KEY:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid API key"}
                )
        response = await call_next(request)
        return response
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(router)

    logger.info("Application setup complete.")


