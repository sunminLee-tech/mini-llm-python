import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])
SCHEDULE_DB_ID = os.environ["NOTION_SCHEDULE_DB_ID"]

def find_schedule_by_title(title: str):
    ...

def update_schedule_time(page_id: str, new_date: str):
    ...