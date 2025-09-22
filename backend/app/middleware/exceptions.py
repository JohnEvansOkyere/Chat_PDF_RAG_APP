from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.applications import FastAPI

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
