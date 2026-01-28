from fastapi import FastAPI

app = FastAPI(
  title="CI/CD Demo API",
  description="Complete CI/CD pipeline demonstration",
  version="1.0.0"
)

@app.get("/")
def read_root():
  return {
    "message": "Hello from CI/CD Pipeline!",
    "status": "running"
  }

@app.get("/health")
def health_check():
  return {"status": "healthy"}