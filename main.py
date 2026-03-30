import os, requests, anthropic, json

# 1. 환경변수 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY', '').strip()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip()
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (무조건 돌아가는 Haiku 모델)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-haiku-20240307", 
        max_tokens=1000,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan travel in English with HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    payload = {"kind": "blogger#post", "title": "Trip to Busan", "content": content}
    
    response = requests.post(post_url, json=payload)
    
    if response.status_code == 200:
        send_telegram("✅ [성공] 사장님! 9시간 만에 드디어 뚫렸습니다!")
    else:
        # 만약 여기서 에러가 나면 구글 권한 문제입니다.
        err = response.json().get('error', {}).get('message', response.text)
        send_telegram(f"❌ 구글 응답 ({response.status_code}): {err}")

except Exception as e:
    send_telegram(f"❌ 오류: {str(e)}")
