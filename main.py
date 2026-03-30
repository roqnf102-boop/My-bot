import os, requests, json

# 1. 깃허브 금고 데이터
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip()
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip()
TELE_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELE_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

def send(msg):
    requests.get(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", params={'chat_id': TELE_ID, 'text': msg})

try:
    # 2. 구글이 요구하는 정석 주소 (키를 주소에 포함)
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    
    # 3. 테스트 데이터
    data = {
        "kind": "blogger#post",
        "title": "Final Success Test",
        "content": "이 글이 보이면 9시간의 사투는 끝입니다!"
    }
    
    res = requests.post(url, json=data)
    
    if res.status_code == 200:
        send("✅ [기적] 드디어 블로그에 글이 올라갔습니다! 사장님 축하드려요!")
    else:
        # 실패 시 이유를 아주 상세하게 봅니다.
        err_msg = res.json().get('error', {}).get('message', res.text)
        send(f"❌ 여전한 권한 에러: {err_msg}\n(계정 일치 여부를 꼭 확인하세요!)")

except Exception as e:
    send(f"❌ 시스템 오류: {str(e)}")
