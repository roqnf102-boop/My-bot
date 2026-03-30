import os, requests, json

# 1. 깃허브 Secrets에서 정보 가져오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip()
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 없이 바로 테스트 글 작성
    content = "<h1>API Test Success</h1><p>이 메시지가 보이면 구글 블로그 연결은 성공한 겁니다!</p>"
    
    # 3. 구글 블로그 업로드
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    payload = {"kind": "blogger#post", "title": "Connection Test", "content": content}
    
    response = requests.post(post_url, json=payload)
    
    if response.status_code == 200:
        send_telegram("✅ [성공] 사장님! 구글 연결은 완벽합니다! 이제 클로드 키만 새로 바꾸시면 됩니다.")
    else:
        err = response.json().get('error', {}).get('message', response.text)
        send_telegram(f"❌ 구글 연결 실패 ({response.status_code}): {err}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
