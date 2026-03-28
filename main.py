import os
import requests
import anthropic
import json

# 1. 깃허브 Secrets에서 모든 열쇠 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOGGER_ID')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY') 

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})
    except:
        pass

def generate_image(prompt):
    if not OPENAI_KEY:
        return None
    
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['data'][0]['url']
        return None
    except:
        return None

def post_to_blogger(title, content):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {'Content-Type': 'application/json'}
    data = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }
    try:
        response = requests.post(f"{url}?key={BLOGGER_API_KEY}", json=data, headers=headers)
        return response.status_code
    except:
        return 500

# 2. 클로드에게 블로그 글 요청 (정식 명칭: claude-3-5-sonnet-20241022)
try:
    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=3000,
        messages=[{
            "role": "user", 
            "content": "Write an engaging English blog post for Americans about a trending Korean topic (Beauty, Food, or Travel). Format the first line as [Title: Title Here]. Use HTML tags (h1, p, ul, li) for the body. At the end, add one line: [Image Prompt: English prompt for DALL-E 3]."
        }]
    )
    full_text = message.content[0].text
except Exception as e:
    send_telegram(f"❌ 클로드 에러 발생: {str(e)}")
    exit()

# 3. 제목, 본문, 이미지 프롬프트 분리
try:
    title = full_text.split("[Title:")[1].split("]")[0].strip()
    content = full_text.split("]")[1].split("[Image Prompt:")[0].strip()
    image_prompt = full_text.split("[Image Prompt:")[1].split("]")[0].strip()
except:
    title = "K-Culture Trends You Should Know"
    content = full_text
    image_prompt = None

# 4. 사진 생성 시도 (안전장치)
image_url = None
if image_prompt and OPENAI_KEY:
    image_url = generate_image(image_prompt)

# 5. 본문에 사진 삽입
final_content = content
if image_url:
    final_content = f'<img src="{image_url}" style="max-width:100%; height:auto;" /><br><br>' + content

# 6. 블로그 업로드 실행
status = post_to_blogger(title, final_content)

# 7. 결과 보고
if status == 200:
    msg = f"✅ 블로그 업로드 성공!\n제목: {title}"
    if not image_url and OPENAI_KEY:
        msg += "\n(사진 생성은 실패했습니다)"
    send_telegram(msg)
else:
    send_telegram(f"❌ 블로그 업로드 실패 (코드: {status})\n블로그 ID나 API 권한을 확인하세요.")
