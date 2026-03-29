import os, requests, anthropic

# 1. 깃허브 Secrets에서 열쇠 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOGGER_ID')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})
    except:
        pass

# 2. 블로그 글쓰기 실행 (워크벤치에 떠 있는 이름 'claude-sonnet-4-6'으로 강제 지정)
try:
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", # 사장님 화면에 있던 그 이름 그대로!
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a helpful English blog post about Korean culture. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드
    blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/?key={BLOGGER_API_KEY}"
    post_data = {
        "kind": "blogger#post",
        "title": "Amazing Korean Culture Trends",
        "content": content
    }
    res = requests.post(blog_url, json=post_data)
    
    if res.status_code == 200:
        send_telegram("✅ 드디어 성공! 블로그 확인해 보세요!")
    else:
        send_telegram(f"❌ 클로드는 성공했으나 블로그 업로드 실패 (코드: {res.status_code})")

except Exception as e:
    send_telegram(f"❌ 이번에도 404면 앤스로픽 서버 오류입니다: {str(e)}")
