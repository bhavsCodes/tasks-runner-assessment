from fastapi import FastAPI
app = FastAPI(title="Task Runner Service")
@app.get("/")
def root():
    return{"message":"Task Runner Service is running"}
