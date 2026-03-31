import os
import requests
import feedparser
import anthropic
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=korean+food&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=korean+culture+kpop&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=korean+health+medicine&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=korea+travel+tourism&hl=en-US&gl=US&ceid=US:en",
]

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

def get_news_items(max_items=2):
    items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                entry = feed.entries[0]
                items.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", "")
                })
                print(f"뉴스 수집 성공: {entry.get('title', '')}")
            if len(items) >= max_items:
                return items
        except Exception as e:
            print(f"RSS 에러: {e}")
            continue
    return items

def get_unsplash_image(keyword):
    """Unsplash에서 관련 이미지 가져오기"""
    try:
        access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        url = f"https://api.unsplash.com/search/photos"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape"
        }
        headers = {"Authorization": f"Client-ID {access_key}"}
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data["results"]:
            photo = data["results"][0]
            image_url = photo["urls"]["regular"]
            photographer = photo["user"]["name"]
            photo_link = photo["links"]["html"]
            return image_url, photographer, photo_link
    except Exception as e:
        print(f"Unsplash 에러: {e}")
    return None, None, None

def generate_english_post(news_item):
    api_key = os.environ.get('CLAUDE_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a blogger writing for an English-speaking audience interested in Korean culture.

Based on this news:
Title: {news_item['title']}
Summary: {news_item['summary']}

Write an engaging English blog post that:
- Has an attractive title for English readers
- Is 300-400 words
- Explains Korean context for Western readers
- Is friendly and informative
- Ends with why this matters to international readers

Format your response as:
TITLE: [your title here]
CONTENT: [your blog post content here]
KEYWORD: [one English keyword for finding a relevant photo, e.g. "korean food" or "kpop" or "korea travel"]
"""
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response = message.content[0].text
    title = news_item['title']
    content = response
    keyword = "korea"
    
    if "TITLE:" in response:
        title = response.split("TITLE:")[1].split("\n")[0].strip()
    if "CONTENT:" in response:
        content = response.split("CONTENT:")[1].split("KEYWORD:")[0].strip()
    if "KEYWORD:" in response:
        keyword = response.split("KEYWORD:")[1].strip().split("\n")[0].strip()
    
    return title, content, keyword

def post_to_blogger(title, content, image_url=None, photographer=None, photo_link=None):
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get('BLOGGER_REFRESH_TOKEN'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get('BLOGGER_CLIENT_ID'),
        client_secret=os.environ.get('BLOGGER_CLIENT_SECRET'),
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    creds.refresh(Request())
    
    service = build('blogger', 'v3', credentials=creds)
    
    # 이미지 HTML 추가
    image_html = ""
    if image_url:
        image_html = f'''
<div style="text-align:center; margin-bottom:20px;">
    <img src="{image_url}" style="max-width:100%; border-radius:8px;" />
    <p style="font-size:12px; color:#888;">Photo by <a href="{photo_link}" target="_blank">{photographer}</a> on <a href="https://unsplash.com" target="_blank">Unsplash</a></p>
</div>
'''
    
    full_content = image_html + f"<p>{content.replace(chr(10), '</p><p>')}</p>"
    
    body = {
        "title": title,
        "content": full_content
    }
    
    result = service.posts().insert(
        blogId=os.environ.get('BLOG_ID'),
        body=body
    ).execute()
    
    return result.get('url')

def main():
    print("뉴스 수집 시작...")
    news_items = get_news_items(max_items=2)
    
    if not news_items:
        msg = "⚠️ 뉴스를 가져오지 못했습니다."
        print(msg)
        send_telegram(msg)
        return
    
    success_count = 0
    for i, item in enumerate(news_items):
        try:
            print(f"포스팅 {i+1} 생성 중: {item['title']}")
            title, content, keyword = generate_english_post(item)
            
            print(f"이미지 검색 중: {keyword}")
            image_url, photographer, photo_link = get_unsplash_image(keyword)
            
            url = post_to_blogger(title, content, image_url, photographer, photo_link)
            msg = f"✅ 포스팅 {i+1} 성공!\n제목: {title}\n주소: {url}"
            print(msg)
            send_telegram(msg)
            success_count += 1
        except Exception as e:
            msg = f"❌ 포스팅 {i+1} 실패: {e}"
            print(msg)
            send_telegram(msg)
    
    send_telegram(f"🎉 오늘 자동 포스팅 완료! {success_count}/{len(news_items)}개 성공")

if __name__ == "__main__":
    main()
