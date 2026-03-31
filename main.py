import os
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)

def post_to_blogger():
    CLIENT_ID = os.environ.get('BLOGGER_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('BLOGGER_CLIENT_SECRET')
    REFRESH_TOKEN = os.environ.get('BLOGGER_REFRESH_TOKEN')
    BLOG_ID = os.environ.get('BLOG_ID')

    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    try:
        if not creds.valid:
            creds.refresh(Request())
            
        service = build('blogger', 'v3', credentials=creds)

        body = {
            "kind": "blogger#post",
            "title": "드디어 성공! 자동 포스팅과 텔레그램 알림",
            "content": "9시간 사투 끝에 블로그 글쓰기와 텔레그램 알림이 모두 성공했습니다!"
        }

        posts = service.posts()
        result = posts.insert(blogId=BLOG_ID, body=body).execute()
        
        msg = f"✅ 블로그 포스팅 성공!\n주소: {result.get('url')}"
        print(msg)
        send_telegram(msg) # 텔레그램으로 전송!
        
    except Exception as e:
        error_msg = f"❌ 에러 발생: {e}"
        print(error_msg)
        send_telegram(error_msg) # 에러나도 텔레그램으로 알림!

if __name__ == "__main__":
    post_to_blogger()
