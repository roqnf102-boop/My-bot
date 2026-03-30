import os, requests, anthropic, json

# 1. 보관함에서 정보 꺼내오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip() # 사진에 있는 그 키
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip() # 사장님이 찾으신 그 숫자

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (여긴 이미 성공!)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a short blog post about Busan travel using HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (사진 속 지침 100% 반영)
    # 주소 끝에 ?key=... 를 붙여서 사장님의 신분을 확실히 증명합니다.
    target_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    post_data = {
        "kind": "blogger#post",
        "title": "Unforgettable Trip to Busan",
        "content": content
    }
    
    # 실제 전송
    res = requests.post(target_url, data=json.dumps(post_data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [대성공] 사장님! 9시간 사투 끝에 블로그가 뚫렸습니다!")
    else:
        # 실패하면 구글이 뱉는 진짜 이유를 봅니다.
        send_telegram(f"❌ 구글 응답: {res.status_code}\n내용: {res.text}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
