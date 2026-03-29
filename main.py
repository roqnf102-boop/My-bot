import os, requests, anthropic, json

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

# 2. 블로그 글쓰기 실행 (성공했던 모델명 유지)
try:
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a helpful English blog post about Korean culture. Use HTML tags like <h1>, <p>, <ul>, <li>."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (헤더 및 데이터 형식 보강)
    blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/?key={BLOGGER_API_KEY}"
    
    # 구글이 좋아하는 정석 데이터 형식
    post_data = {
        "kind": "blogger#post",
        "title": "Exploring the Charm of Korean Culture",
        "content": content
    }
    
    # 중요: json.dumps로 데이터를 묶고, Content-Type을 명시합니다.
    headers = {'Content-Type': 'application/json'}
    res = requests.post(blog_url, data=json.dumps(post_data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [성공] 드디어 블로그에 첫 글이 올라갔습니다! 확인해보세요!")
    else:
        # 에러 메시지 상세 확인용
        error_detail = res.text[:100]
        send_telegram(f"❌ 블로그 업로드 실패 (코드: {res.status_code})\n이유: {error_detail}")

except Exception as e:
    send_telegram(f"❌ 클로드 통신 에러: {str(e)}")
