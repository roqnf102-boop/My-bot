import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# 1. 깃허브 Secrets에서 사장님이 넣은 '열쇠 3종 세트' 가져오기
CLIENT_ID = os.environ.get('BLOGGER_CLIENT_ID')
CLIENT_SECRET = os.environ.get('BLOGGER_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('BLOGGER_REFRESH_TOKEN')
BLOG_ID = os.environ.get('BLOG_ID')

def post_to_blogger(title, content):
    # 2. 사장님이 따온 리프레시 토큰으로 구글 문 열기
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    # 토큰이 만료됐으면 자동으로 갱신
    if not creds.valid:
        creds.refresh(Request())

    # 3. 블로거 서비스 연결
    service = build('blogger', 'v3', credentials=creds)

    # 4. 실제 글쓰기 실행
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }

    posts = service.posts()
    result = posts.insert(blogId=BLOG_ID, body=body).execute()
    print(f"✅ 포스팅 성공! 주소: {result.get('url')}")

# 테스트 실행 (나중에 AI 글쓰기 부분이랑 합치시면 됩니다)
if __name__ == "__main__":
    post_to_blogger("테스트 포스팅입니다", "<p>9시간 사투 끝에 성공한 자동 포스팅!</p>")
