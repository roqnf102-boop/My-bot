import os, requests, anthropic, json

# 1. 깃허브 보관함에서 정보 가져오기 (공백 제거 .strip() 추가)
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY', '').strip()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
# 깃허브 Secrets 이름이 'BLOGGER_API_KEY' 인지 꼭 확인하세요!
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip() 
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip() 

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (이건 이미 성공했으니 그대로 둡니다)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a 3-paragraph English blog post about Busan travel using HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (403 에러를 해결하는 정석 방식)
    # 구글이 사진에서 요구한 대로 ?key=... 를 주소에 직접 박았습니다.
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "kind": "blogger#post",
        "title": "Essential Guide to Busan Travel",
        "content": content
    }
    
    # 구글로 전송!
    res = requests.post(post_url, data=json.dumps(data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [기적] 드디어 뚫렸습니다 사장님! 블로그에 글 꽂혔어요!")
    else:
        # 실패하면 구글이 뱉는 구체적인 이유를 보여줍니다.
        send_telegram(f"❌ 구글 응답 ({res.status_code}): {res.text[:200]}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
