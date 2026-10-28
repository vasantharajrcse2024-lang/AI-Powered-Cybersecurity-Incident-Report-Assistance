"""Optional localhost FastAPI surface; Streamlit is the primary interface."""
from fastapi import FastAPI
from incident_assistant.database import init_db, list_incidents
app = FastAPI(title="Incident Report Assistant API", version="1.0.0", description="Local educational prototype; bind to localhost only.")
@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"status":"ok","storage":"SQLite","external_ai":False}
@app.get("/incidents")
def incidents(): return list_incidents()
