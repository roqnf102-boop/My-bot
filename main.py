import os, requests, anthropic

# 1. 깃허브 금고에서 열쇠 꺼내기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOGGER_ID')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

# 2. 블로그 글쓰기 실행 (모델명을 워크벤치에 뜬 이름으로 변경)
try:
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620", # 사장님 계정에서 인식 가능한 이름으로 재시도
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a short blog post about Korean food in English with HTML tags."}]
    )
    content = message.content[0].text
    
    # 블로그 업로드
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/?key={BLOGGER_API_KEY}"
    data = {"kind": "blogger#post", "title": "K-Food Trend", "content": content}
    res = requests.post(url, json=data)
    
    if res.status_code == 200:
        send_telegram("✅ 성공! 드디어 블로그에 글이 올라갔습니다.")
    else:
        send_telegram(f"❌ 블로그 업로드 실패: {res.status_code}")

except Exception as e:
    # 만약 여기서 또 404가 나면 워크벤치에 적힌 'claude-sonnet-4-6'으로 이름을 한 번 더 바꿔야 합니다.
    send_telegram(f"❌ 여전한 에러: {str(e)}")
