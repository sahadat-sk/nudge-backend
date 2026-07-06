from fastapi import FastAPI
from nudge_backend.api.v1.contacts import router as contacts_router
from nudge_backend.api.v1.contact_activity import router as contact_activity_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router=contacts_router, prefix="/api/v1")
app.include_router(router=contact_activity_router, prefix="/api/v1")
