import os, requests, anthropic, json

# 1. 깃허브 Secrets에서 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY', '').strip()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
BLOGGER_KEY = os.environ.get('BLOGGER_API_KEY', '').strip()
BLOGGER_ID = os.environ.get('BLOGGER_ID', '').strip()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (모델명: 사장님 계정용 최신 모델)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620", 
        max_tokens=1500,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan's lifestyle in English. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 전송 (구글 공식 문서 권장 방식)
    # 주소창에 직접 키를 박아 신분 증명을 확실히 합니다.
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_ID}/posts?key={BLOGGER_KEY}"
    
    # 구글이 가장 좋아하는 표준 JSON 형식
    payload = json.dumps({
        "kind": "blogger#post",
        "title": "Living the Busan Life: A Salaryman's Perspective",
        "content": content
    })
    
    headers = {'Content-Type': 'application/json'}
    
    # 전송!
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        send_telegram("✅ [성공] 사장님!!! 드디어 뚫렸습니다! 9시간 고생 끝!")
    else:
        # 실패 시 구글의 '진짜 속마음'을 텔레그램으로 보냅니다.
        # 여기서 나오는 메시지가 범인을 잡는 마지막 단서입니다.
        error_info = response.json().get('error', {}).get('message', response.text)
        send_telegram(f"❌ 구글 응답 ({response.status_code}): {error_info}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
