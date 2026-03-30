import os, requests, json

# 1. 깃허브 Secrets에서 정보 가져오기
APP_PASS = os.environ.get('BLOGGER_API_KEY', '').strip() # pdhbpzjyewvrctes (띄어쓰기 없이!)
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip()
TELE_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELE_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

def send(msg):
    requests.get(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", params={'chat_id': TELE_ID, 'text': msg})

try:
    # 2. 클로드 없이 테스트 글 생성
    # AI 모델 에러를 피하기 위해 일단 직접 쓴 글을 보냅니다.
    title = "9시간 사투의 결과: 드디어 성공인가?"
    content = "<h2>드디어 뚫렸습니다!</h2><p>이 글이 블로그에 보인다면 사장님의 앱 비밀번호는 완벽하게 작동하는 겁니다.</p>"
    
    # 3. 구글 블로그 전송 (앱 비밀번호 마스터키 방식)
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={APP_PASS}"
    
    payload = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }
    
    # 전송!
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        send("✅ [기적] 사장님!!! 드디어 블로그 글쓰기 성공했습니다! 9시간 만에 뚫었습니다!")
    else:
        # 실패 시 이유를 아주 상세하게 봅니다.
        err_msg = res.json().get('error', {}).get('message', res.text)
        send(f"❌ 여전한 권한 에러: {err_msg}")

except Exception as e:
    send(f"❌ 시스템 오류: {str(e)}")
