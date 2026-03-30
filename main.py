import os, requests, anthropic, json

# 1. 깃허브 금고에서 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY', '').strip()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
BLOG_KEY = os.environ.get('BLOGGER_API_KEY', '').strip() 
BLOG_ID = os.environ.get('BLOGGER_ID', '').strip() 

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})
    except:
        pass

try:
    # 2. 클로드로 부산 여행 글 생성 (모델명 사장님 워크벤치 기준)
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write a 3-paragraph blog post about Busan travel in English. Use HTML tags like <h1>, <p>."}]
    )
    content = message.content[0].text
    
    # 3. 구글 블로그 업로드 (주소에 직접 키를 박는 정석 방식)
    # 사진에서 본 'key=API_KEY' 파라미터 방식을 적용했습니다.
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOG_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "kind": "blogger#post",
        "title": "A Wonderful Journey to Busan",
        "content": content
    }
    
    # 실제 전송
    res = requests.post(post_url, data=json.dumps(data), headers=headers)
    
    if res.status_code == 200:
        send_telegram("✅ [성공] 사장님! 9시간 사투 끝에 블로그 포스팅 완료!")
    else:
        # 실패 시 구글의 실제 답변을 텔레그램으로 전송
        send_telegram(f"❌ 실패 ({res.status_code}): {res.text[:150]}")

except Exception as e:
    send_telegram(f"❌ 오류 발생: {str(e)}")
