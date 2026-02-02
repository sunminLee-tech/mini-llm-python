import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = FastAPI(title="LLM Toy API")

class ChatRequest(BaseModel):
    clientId: str
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 도움이 되는 한국어 어시스턴트야"},
            {"role": "user", "content": request.message}
        ],
        temperature=0.7
    )
    print(f"[요청]", response.choices[0].message.content)
    return  {"message": response.choices[0].message.content}
    
   


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
