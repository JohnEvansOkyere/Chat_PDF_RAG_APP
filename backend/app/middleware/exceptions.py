# app/middleware/exceptions.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log exc if you have logger, then return generic response
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
