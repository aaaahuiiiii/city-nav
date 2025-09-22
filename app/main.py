from fastapi import FastAPI
from pydantic import BaseModel
import json, os

app = FastAPI()
DATA_PATH = os.path.join(os.path.dirname(__file__), "qa.json")

class QA(BaseModel):
    question: str
    answer: str

@app.get("/api/qa")
def list_qa():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/qa")
def add_qa(item: QA):
    data = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(item.model_dump())
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "size": len(data)}
