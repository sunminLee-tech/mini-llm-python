import uvicorn
import json
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
from notion_client import Client

load_dotenv()
app = FastAPI(title="LLM Toy API")
client = OpenAI()
notion = Client(auth=os.environ["NOTION_TOKEN"])

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_schedule",
            "description": "노션에 일정을 추가한다",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "일정 제목"},
                    "date": {"type": "string", "description": "날짜 (YYYY-MM-DD 형식)"},
                    "status": {"type": "string", "description": "상태 (예: 시작 전, 진행 중, 완료)"}
                },
                "required": ["title", "date"]
            }
        }
    },
     {
        "type": "function",
        "function": {
            "name": "remove_schedule",
            "description": "노션에 일정을 삭제한다",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "일정 제목"},
                    "date": {"type": "string", "description": "날짜 (YYYY-MM-DD 형식)"},
                    "status": {"type": "string", "description": "상태 (예: 시작 전, 진행 중, 완료)"}
                },
                "required": ["title", "date"]
            }
        }
    },
      {
        "type": "function",
        "function": {
            "name": "modify_schedule",
            "description": "노션에 기존 일정을 수정한다. title로 검색 후 new_ 값으로 변경한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "검색할 기존 일정 제목"},
                    "new_title": {"type": "string", "description": "변경할 새 제목"},
                    "new_date": {"type": "string", "description": "변경할 새 날짜 (YYYY-MM-DD 형식)"},
                    "new_status": {"type": "string", "description": "변경할 새 상태 (예: 시작 전, 진행 중, 완료)"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "노션에서 일정을 조회한다. 제목으로 검색하거나 전체 일정을 가져온다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "검색할 일정 제목 (없으면 전체 조회)"}
                },
                "required": []
            }
        }
    }
]


def create_schedule(title: str, date: str, status: str = "시작 전"):
    db_id = os.environ["NOTION_SCHEDULE_DB_ID"]
    page = notion.pages.create(
        parent={"database_id": db_id},
        properties={
            "title": {"title": [{"text": {"content": title}}]},
            "date": {"date": {"start": date}},
            "status": {"status": {"name": status}},
        }
    )
    return {"id": page["id"], "title": title, "date": date, "status": status}


def remove_schedule(title: str, date: str, status: str = ""):
    # 1. 제목으로 검색
    results = notion.search(query=title, filter={"property": "object", "value": "page"})
    # 2. 찾은 페이지 삭제(archive)
    for page in results["results"]:
        page_title = page["properties"]["title"]["title"]
        if page_title and page_title[0]["plain_text"] == title:
            notion.pages.update(page_id=page["id"], archived=True)
            return {"deleted": True, "title": title, "date": date}
    return {"deleted": False, "message": f"'{title}' 일정을 찾을 수 없습니다"}


def modify_schedule(title: str, new_title: str = "", new_date: str = "", new_status: str = ""):
    # 1. 제목으로 검색
    results = notion.search(query=title, filter={"property": "object", "value": "page"})
    for page in results["results"]:
        page_title = page["properties"]["title"]["title"]
        if page_title and page_title[0]["plain_text"] == title:
            # 2. 변경할 속성만 업데이트
            properties = {}
            if new_title:
                properties["title"] = {"title": [{"text": {"content": new_title}}]}
            if new_date:
                properties["date"] = {"date": {"start": new_date}}
            if new_status:
                properties["status"] = {"status": {"name": new_status}}
            notion.pages.update(page_id=page["id"], properties=properties)
            return {"modified": True, "title": title, "new_title": new_title, "new_date": new_date, "new_status": new_status}
    return {"modified": False, "message": f"'{title}' 일정을 찾을 수 없습니다"}


def get_schedule(title: str = ""):
    results = notion.search(query=title, filter={"property": "object", "value": "page"})
    schedules = []
    for page in results["results"]:
        props = page["properties"]
        page_title = props.get("title", {}).get("title", [])
        page_date = props.get("date", {}).get("date")
        page_status = props.get("status", {}).get("status")
        schedules.append({
            "title": page_title[0]["plain_text"] if page_title else "",
            "date": page_date["start"] if page_date else "",
            "status": page_status["name"] if page_status else "",
        })
    if not schedules:
        return {"found": False, "message": "일정이 없습니다"}
    return {"found": True, "schedules": schedules}


class ChatRequest(BaseModel):
    clientId: str
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    messages = [
        {"role": "system", "content": "너는 도움이 되는 한국어 어시스턴트야. 사용자가 일정 추가를 요청하면 create_schedule 함수를 사용해."
        " 사용자가 일정 삭제를 요청하면 remove_schedule 함수를 사용해. 사용자가 일정 수정을 요청하면 modify_schedule 함수를 사용해. 사용자가 일정 조회를 요청하면 get_schedule 함수를 사용해."},
        {"role": "user", "content": request.message}
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools,
        temperature=0.7
    )

    choice = response.choices[0].message
    print(f"[choice] {choice}")

    # LLM이 함수 호출을 결정한 경우
    if choice.tool_calls:
        tool_call = choice.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "create_schedule":
            print(f"[Tool 호출] create_schedule: {args}")
            result = create_schedule(**args)
        elif tool_call.function.name == "remove_schedule":
            print(f"[Tool 호출] remove_schedule: {args}")
            result = remove_schedule(**args)
        elif tool_call.function.name == "modify_schedule":
            print(f"[Tool 호출] modify_schedule: {args}")
            result = modify_schedule(**args)
        elif tool_call.function.name == "get_schedule":
            print(f"[Tool 호출] get_schedule: {args}")
            result = get_schedule(**args)


        # 함수 결과를 LLM에게 다시 전달해서 자연어 응답 받기
        messages.append(choice.model_dump())
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })

        follow_up = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7
        )
        reply = follow_up.choices[0].message.content
    else:
        reply = choice.content

    print(f"[응답] {reply}")
    return {"message": reply}


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
