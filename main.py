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

def generate_english_post(news_item):
    api_key = os.environ.get('CLAUDE_API_KEY')
    print(f"API KEY 앞 10자리: {api_key[:10] if api_key else 'None'}")
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
"""
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response = message.content[0].text
    title = news_item['title']
    content = response
    
    if "TITLE:" in response and "CONTENT:" in response:
        parts = response.split("CONTENT:")
        title = parts[0].replace("TITLE:", "").strip()
        content = parts[1].strip()
    
    return title, content

def post_to_blogger(title, content):
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
    
    body = {
        "title": title,
        "content": f"<p>{content.replace(chr(10), '</p><p>')}</p>"
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
            title, content = generate_english_post(item)
            url = post_to_blogger(title, content)
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
