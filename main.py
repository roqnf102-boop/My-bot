import os, requests, json
from requests.auth import HTTPBasicAuth

# 1. 깃허브 Secrets에서 정보 가져오기
EMAIL = "roqnf102@gmail.com" # 사장님 확인된 계정
APP_PASS = os.environ.get('BLOGGER_API_KEY', '').strip() # pdhbpzjyewvrctes (띄어쓰기 없이!)
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip()
TELE_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELE_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

def send(msg):
    requests.get(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", params={'chat_id': TELE_ID, 'text': msg})

try:
    # 2. 구글 블로그 전송 (앱 비밀번호 로그인 방식)
    # 이제 주소에 ?key= 는 뺍니다.
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
    
    payload = {
        "kind": "blogger#post",
        "title": "9시간 사투의 끝: 마스터키로 강제 진입",
        "content": "<h2>연결 성공!</h2><p>앱 비밀번호 인증으로 구글 보안망을 뚫었습니다.</p>"
    }
    
    # 이 부분이 핵심: 이메일과 앱 비밀번호로 '나'임을 증명합니다.
    res = requests.post(
        url, 
        json=payload,
        auth=HTTPBasicAuth(EMAIL, APP_PASS)
    )
    
    if res.status_code == 200:
        send("✅ [기적] 사장님!!! 드디어 블로그 글쓰기 성공했습니다! 이제 소고기 드시러 가세요!")
    else:
        # 또 실패하면 구글이 뱉는 이유를 샅샅이 봅니다.
        err_msg = res.json().get('error', {}).get('message', res.text)
        send(f"❌ 마지막 시도 실패: {err_msg}")

except Exception as e:
    send(f"❌ 시스템 오류: {str(e)}")
