from fastapi import FastAPI
from app.routers.extract import router as extract_router
from app.routers.predict import router as predict_router
from app.routers.analyze import router as analyze_router
from app.routers.agent import router as agent_router


app = FastAPI()

app.include_router(extract_router)
app.include_router(predict_router)
app.include_router(analyze_router)
app.include_router(agent_router)


@app.get("/")
def home():
    return {"message": "API is running"}