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
    # 2. 클로드 글쓰기 (모든 계정에서 공통 지원되는 표준 모델명)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-opus-20240229", # 404 에러를 방지하는 표준 모델명입니다.
        max_tokens=1500,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan travel in English. Use HTML tags like <h2> and <p>."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 전송
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_ID}/posts?key={BLOGGER_KEY}"
    
    payload = {
        "kind": "blogger#post",
        "title": "A Salaryman's Guide to Busan",
        "content": content
    }
    
    response = requests.post(post_url, json=payload)
    
    if response.status_code == 200:
        send_telegram("✅ [성공] 사장님, 드디어 블로그 글쓰기 성공했습니다. 고생 많으셨습니다.")
    else:
        # 실패 시 구글의 응답을 최대한 자세히 봅니다.
        error_msg = response.json().get('error', {}).get('message', response.text)
        send_telegram(f"❌ 구글 응답 ({response.status_code}): {error_msg}")

except Exception as e:
    # 텔레그램으로 구체적인 에러 내용을 다시 보냅니다.
    send_telegram(f"❌ 오류 발생: {str(e)}")
