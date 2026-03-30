import os, requests, anthropic, json

# 1. 깃허브 Secrets에서 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY', '').strip()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
BLOGGER_KEY = os.environ.get('BLOGGER_API_KEY', '').strip()
BLOGGER_ID = os.environ.get('BLOGGER_ID', '').strip()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})
    except:
        pass

try:
    # 2. 클로드 글쓰기 (모델명을 가장 확실한 최신형으로 변경)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-7-sonnet-latest",  # 404 에러 방지용 최신 모델명
        max_tokens=1500,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan travel in English. Use HTML tags like <h2> and <p>."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 전송 (URL 파라미터 방식)
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_ID}/posts?key={BLOGGER_KEY}"
    
    payload = {
        "kind": "blogger#post",
        "title": "A Perfect Day in Busan",
        "content": content
    }
    
    # 전송!
    response = requests.post(post_url, json=payload)
    
    if response.status_code == 200:
        send_telegram("✅ [기적] 사장님!!! 드디어 블로그 글쓰기 성공했습니다! 9시간 고생 끝!")
    else:
        # 실패 시 구글의 진짜 이유를 봅니다.
        error_msg = response.json().get('error', {}).get('message', response.text)
        send_telegram(f"❌ 구글 응답 ({response.status_code}): {error_msg}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
