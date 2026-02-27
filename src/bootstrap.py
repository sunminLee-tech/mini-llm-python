import os
import numpy as np
import faiss
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI

load_dotenv()

# -----------------------------
# 1. Notion 연결
# -----------------------------
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_SCHEDULE_DB_ID"]

# -----------------------------
# 2. OpenAI 임베딩 클라이언트
# -----------------------------
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBED_MODEL = "text-embedding-3-small"
DIMENSION = 1536  # 모델 차원

# -----------------------------
# 3. Notion 데이터 조회
# -----------------------------
def fetch_notion_pages():
    results = []
    cursor = None

    while True:
        resp = notion.databases.query(
            database_id=database_id,
            start_cursor=cursor
        )
        results.extend(resp["results"])
        print(f"[results] {results}")

        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return results


# -----------------------------
# 4. 텍스트 추출 (간단 버전)
# -----------------------------
def extract_text(page):
    props = page.get("properties", {})
    texts = []

    for v in props.values():
        if v.get("type") == "title":
            texts.extend([t["plain_text"] for t in v["title"]])
        elif v.get("type") == "rich_text":
            texts.extend([t["plain_text"] for t in v["rich_text"]])

    return " ".join(texts).strip()


# -----------------------------
# 5. 임베딩 생성
# -----------------------------
def embed_text(text):
    if not text:
        return None

    res = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return np.array(res.data[0].embedding, dtype="float32")


# -----------------------------
# 6. FAISS 인덱스 생성
# -----------------------------
def build_faiss(vectors):
    index = faiss.IndexFlatL2(DIMENSION)
    index.add(np.vstack(vectors))
    return index


# -----------------------------
# 7. 메인 bootstrap
# -----------------------------
def main():
    pages = fetch_notion_pages()
    print(f"페이지 수: {len(pages)}")

    vectors = []
    ids = []

    for page in pages:
        text = extract_text(page)
        if not text:
            continue

        vec = embed_text(text)
        if vec is None:
            continue

        vectors.append(vec)
        ids.append(page["id"])

    if not vectors:
        print("임베딩할 데이터 없음")
        return

    index = build_faiss(vectors)

    # 저장
    faiss.write_index(index, "notion_index.faiss")
    np.save("notion_ids.npy", np.array(ids))

    print(" FAISS 저장 완료:", index.ntotal)


if __name__ == "__main__":
    main()