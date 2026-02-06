from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()  # .env 읽기

notion = Client(auth=os.environ["NOTION_TOKEN"])

db = notion.databases.retrieve(
    database_id=os.environ["NOTION_SCHEDULE_DB_ID"]
)

print("DB 연결 성공:", db["title"][0]["plain_text"])
