from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.routing import Mount
from app.ws_router import router

app = FastAPI()
app.include_router(router)

# Mount static files at "/static" to avoid conflict

app.mount("/static", StaticFiles(directory="static"), name="static")
# Serve index.html manually at "/" (without overriding /ws)
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
