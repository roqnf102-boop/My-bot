import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def post_to_blogger():
    # 깃허브 Secrets에서 사장님이 넣은 '열쇠 3종'과 '블로그ID' 가져오기
    CLIENT_ID = os.environ.get('BLOGGER_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('BLOGGER_CLIENT_SECRET')
    REFRESH_TOKEN = os.environ.get('BLOGGER_REFRESH_TOKEN')
    BLOG_ID = os.environ.get('BLOG_ID')

    # 사장님이 따온 리프레시 토큰으로 구글 문 열기
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    # 토큰이 만료됐으면 자동으로 갱신
    try:
        if not creds.valid:
            creds.refresh(Request())
            
        service = build('blogger', 'v3', credentials=creds)

        # 실제 블로그에 올릴 내용 (테스트용)
        body = {
            "kind": "blogger#post",
            "title": "9시간 사투 끝에 성공한 자동 포스팅!",
            "content": "사장님, 드디어 성공했습니다! 이제 AI가 자동으로 글을 씁니다."
        }

        posts = service.posts()
        result = posts.insert(blogId=BLOG_ID, body=body).execute()
        print(f"✅ 포스팅 성공! 주소: {result.get('url')}")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    post_to_blogger()
