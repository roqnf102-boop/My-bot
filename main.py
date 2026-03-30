import os, requests, anthropic, json

# 1. 깃허브 금고에서 데이터 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOGGER_ID') # 이제 이 금고를 새로 만드셔야 합니다!

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (사장님 화면에 뜬 모델명 그대로)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a helpful blog post about Busan travel tips in English. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드
    # API 키를 주소 뒤에 직접 붙여서 구글이 못 본 척 못 하게 합니다.
    blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOGGER_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    post_data = {
        "kind": "blogger#post",
        "title": "Local's Guide: Best Travel Tips for Busan",
        "content": content
    }
    
    res = requests.post(blog_url, data=json.dumps(post_data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [대성공] 사장님! 드디어 블로그에 글이 올라갔습니다!")
    else:
        send_telegram(f"❌ 마지막 고개 (코드: {res.status_code})\n이유: {res.text[:150]}")

except Exception as e:
    send_telegram(f"❌ 에러 발생: {str(e)}")
