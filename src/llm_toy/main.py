import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="LLM Toy API")


@app.post("/debug")
async def debug(request: Request):
    body = await request.body()
    print(f"[DEBUG] raw body: {body}")
    print(f"[DEBUG] headers: {request.headers}")
    return {"raw": body.decode() if body else "empty"}


class ChatRequest(BaseModel):
    clientId: str
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
  
    
    print(f"[요청] clientId: {request.clientId}, message: {request.message}")
    # TODO: LLM 호출 로직
    return {
        "clientId": request.clientId,
        "response": f"받은 메시지: {request.message}"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
