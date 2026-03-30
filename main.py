import os, requests, anthropic, json

# 1. 깃허브 보관함에서 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip() 
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip() 

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (여긴 이미 뚫렸습니다!)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a helpful blog post about Busan travel in English. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (사진 속 'key=API_KEY' 방식 적용)
    # 주소 맨 뒤에 ?key=... 를 붙여서 사장님의 신분을 강제로 증명합니다.
    target_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    post_data = {
        "kind": "blogger#post",
        "title": "Exploring the Magic of Busan",
        "content": content
    }
    
    # 전송!
    res = requests.post(target_url, data=json.dumps(post_data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [대성공] 사장님! 9시간의 사투 끝에 블로그가 뚫렸습니다! 🥂")
    else:
        # 실패하면 구글이 뱉는 진짜 이유를 그대로 보여줍니다.
        send_telegram(f"❌ 구글 응답 ({res.status_code}): {res.text[:200]}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
