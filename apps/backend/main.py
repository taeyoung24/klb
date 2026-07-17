from fastapi import FastAPI
import uvicorn

from settings import API_URL
from src.app_configuration import setup
from src.lifespan_definition import lifespan

klb_backend = FastAPI(
    title="KLB Backend API Documentation",
    lifespan=lifespan,
    docs_url="/docs",
    # swagger_ui_parameters={"persistAuthorization": True}
)

setup(klb_backend)

if __name__ == "__main__":
    host = API_URL.split('//')[1].split(':')[0]
    port = int(API_URL.split(':')[-1])
    uvicorn.run("main:klb_backend", host=host, port=port, reload=False)
