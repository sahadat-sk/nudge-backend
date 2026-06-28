from fastapi import FastAPI
from nudge_backend.api.v1.contacts import router

app = FastAPI()
app.include_router(router=router, prefix="/api/v1")
