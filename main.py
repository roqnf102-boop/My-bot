import os
import requests
import anthropic

# 깃허브 금고(Secrets)에서 정보 가져오기
CLAUDE_KEY = os.environ.get('CLAUDE_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': TELEGRAM_ID, 'text': text}
    requests.get(url, params=params)

# 클로드에게 미국 타겟 SEO 블로그 포스팅 요청
client = anthropic.Anthropic(api_key=CLAUDE_KEY)
message = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=2000,
    messages=[
        {
            "role": "user", 
            "content": """
            미국인들이 구글에서 많이 검색하는 '한국 문화, 음식, 뷰티' 중 하나를 골라서 블로그 포스팅을 작성해줘.
            
            [조건]
            1. 언어: 영어 (English)
            2. 스타일: 미국 독자들이 읽기 편하고 매력적인 블로그 톤
            3. SEO 최적화: 검색 결과 상단에 노출될 수 있도록 'Catchy Title'과 'Meta Description', 'Keywords'를 포함할 것
            4. 구성: Title, Introduction, 3-4 Subheadings(H2), Conclusion 순서로 작성해줘.
            """
        }
    ]
)

# 결과물 추출 및 텔레그램 전송
content = message.content[0].text
send_telegram(f"🇺🇸 [미국향 K-콘텐츠 생성 완료]\n\n{content}")
