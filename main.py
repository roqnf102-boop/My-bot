import os, requests, anthropic, json

# 1. 환경 변수 (깃허브 Secrets 이름과 똑같아야 합니다)
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY', '').strip() # 공백 제거 추가
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip() # 공백 제거 추가

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (검증된 모델명)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan travel in English. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (가장 확실한 POST 방식)
    # 주소 형식을 구글 공식 가이드대로 완전히 맞췄습니다.
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
    
    headers = {'Content-Type': 'application/json'}
    params = {'key': BLOGGER_API_KEY}
    
    data = {
        "kind": "blogger#post",
        "title": "Exploring the Magic of Busan",
        "content": content
    }
    
    # 구글로 전송
    res = requests.post(post_url, params=params, data=json.dumps(data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [성공] 사장님! 드디어 블로그에 글이 꽂혔습니다! 확인해보세요!")
    else:
        # 구글이 뱉는 에러 메시지 전체를 텔레그램으로 보냅니다.
        error_msg = res.json().get('error', {}).get('message', 'Unknown Error')
        send_telegram(f"❌ 구글 에러 ({res.status_code}): {error_msg}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류 발생: {str(e)}")
