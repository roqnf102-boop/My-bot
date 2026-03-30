import os, requests, anthropic, json

# 1. 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOGGER_ID') # <--- 여기가 꼭 '숫자'여야 합니다!

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})

try:
    # 2. 클로드 글쓰기 (사장님 계정 전용 모델)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a funny blog post about Busan's 'salaryman uncle' lifestyle in English. Use HTML tags."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드
    # 구글 API가 가장 좋아하는 '주소에 키 박기' 방식
    target_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOGGER_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    post_data = {
        "kind": "blogger#post",
        "title": "A Day in the Life of a Busan Salaryman",
        "content": content
    }
    
    res = requests.post(target_url, data=json.dumps(post_data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [9시간 사투 끝!] 드디어 성공했습니다 사장님! 블로그 가보세요!")
    else:
        # 실패하면 구글이 뱉는 진짜 이유를 그대로 보여줍니다.
        send_telegram(f"❌ 여전히 에러 (코드: {res.status_code})\n사유: {res.text}")

except Exception as e:
    send_telegram(f"❌ 시스템 오류: {str(e)}")
