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
OPENAI_KEY = os.environ.get('OPENAI_API_KEY') # 나중에 추가할 OpenAI 키

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.get(url, params={'chat_id': TELEGRAM_ID, 'text': text})
    except:
        pass # 텔레그램 전송 실패는 무시

def generate_image(prompt):
    # 사진 생성 API (OpenAI DALL-E 3)
    if not OPENAI_KEY: # 만약 OpenAI 키가 없다면 사진 생성 건너뜀
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
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['data'][0]['url'] # 이미지 URL 반환
        else:
            return None # 이미지 생성 실패
    except:
        return None # 이미지 생성 실패

def post_to_blogger(title, content):
    # 구글 블로거 API로 포스팅
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
        return 500 # 업로드 실패

# 2. 클로드에게 미국 타겟 블로그 글 요청
client = anthropic.Anthropic(api_key=CLAUDE_KEY)
message = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=3000,
    messages=[{
        "role": "user", 
        "content": "미국인들이 흥미로워할 한국의 뷰티, 음식, 또는 여행지 중 하나를 골라 영어 블로그 글을 써줘. 제목은 맨 첫 줄에 [Title: 제목] 형식으로 적어주고, 본문은 HTML 태그(h1, p, ul, li)를 써서 작성해줘. 그리고 맨 밑에 이 글에 어울리는 DALL-E 3 이미지 생성 프롬프트를 영어로 [Image Prompt: 프롬프트] 형식으로 한 줄 적어줘."
    }]
)

full_text = message.content[0].text

# 3. 제목, 본문, 이미지 프롬프트 분리
try:
    title = full_text.split("[Title:")[1].split("]")[0].strip()
    content = full_text.split("]")[1].split("[Image Prompt:")[0].strip()
    image_prompt = full_text.split("[Image Prompt:")[1].split("]")[0].strip()
except:
    title = "K-Culture Trends You Should Know"
    content = full_text
    image_prompt = None

# 4. 사진 생성 시도 (안전장치 포함)
image_url = None
if image_prompt and OPENAI_KEY:
    image_url = generate_image(image_prompt)

# 5. 본문에 사진 삽입 (사진 생성 성공 시)
final_content = content
if image_url:
    final_content = f'<img src="{image_url}" style="max-width:100%; height:auto;" /><br><br>' + content

# 6. 블로그 업로드 실행
status = post_to_blogger(title, final_content)

# 7. 결과 보고 (텔레그램)
if status == 200:
    if image_url:
        send_telegram(f"✅ 블로그 글+사진 업로드 성공!\n제목: {title}")
    else:
        send_telegram(f"✅ 블로그 글 업로드 성공! (사진은 실패/건너뜀)\n제목: {title}")
else:
    send_telegram(f"❌ 업로드 실패 (코드: {status})\n나중에 다시 시도하세요.")
