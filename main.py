from fastapi import FastAPI

app = FastAPI(title="WM_Imports API")

@app.get("/")
def home():
    return {"status": "API WM_Imports rodando com sucesso!"}
