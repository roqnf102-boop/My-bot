import os
import requests
import feedparser
import anthropic
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

RSS_FEEDS = [
    ("korean food restaurant", "🍜 Korean Food"),
    ("k-beauty skincare korean cosmetics", "💄 K-Beauty"),
    ("kpop korean culture hallyu", "🎵 K-Culture"),
    ("korea travel tourism", "✈️ Korea Travel"),
    ("korean health wellness", "💪 Korean Wellness"),
    ("korean drama movie netflix", "📺 Korean Entertainment"),
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
    import random
    feeds = random.sample(RSS_FEEDS, min(max_items, len(RSS_FEEDS)))
    for query, category in feeds:
        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            if feed.entries:
                entry = feed.entries[0]
                items.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "category": category
                })
                print(f"뉴스 수집 성공 [{category}]: {entry.get('title', '')}")
            if len(items) >= max_items:
                return items
        except Exception as e:
            print(f"RSS 에러: {e}")
            continue
    return items

def get_pexels_image(keyword):
    try:
        api_key = os.environ.get('PEXELS_API_KEY')
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": keyword, "per_page": 1, "orientation": "landscape"}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get("photos"):
            photo = data["photos"][0]
            image_url = photo["src"]["large"]
            photographer = photo["photographer"]
            photo_link = photo["url"]
            return image_url, photographer, photo_link
    except Exception as e:
        print(f"Pexels 에러: {e}")
    return None, None, None

def generate_english_post(news_item):
    api_key = os.environ.get('CLAUDE_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a top Korean lifestyle blogger writing for an international English-speaking audience. 
You write like a passionate expert who loves Korean culture, food, beauty, and travel.
Your writing style is engaging, personal, and informative - like a knowledgeable friend sharing insider tips.

Category: {news_item['category']}

Based on this news/topic:
Title: {news_item['title']}
Summary: {news_item['summary']}

Write a creative, engaging English blog post that:
- Has a catchy, SEO-friendly title that would appeal to Western readers
- Is 400-500 words
- Includes personal insights and Korean cultural context
- Has 2-3 subheadings to break up the content
- Includes practical tips or recommendations where relevant
- Uses a warm, enthusiastic tone like a passionate blogger
- Ends with an engaging question or call-to-action for readers

DO NOT just summarize the news. Use it as inspiration to write an original, creative blog post.

Format your response EXACTLY as:
TITLE: [your catchy title]
KEYWORD: [one English keyword for photo search like "korean food" or "kpop" or "korea beauty"]
CONTENT: [your full blog post with subheadings using <h2> tags]
"""
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response = message.content[0].text
    title = news_item['title']
    content = response
    keyword = "korea"
    
    if "TITLE:" in response:
        title = response.split("TITLE:")[1].split("\n")[0].strip()
    if "KEYWORD:" in response:
        keyword = response.split("KEYWORD:")[1].split("\n")[0].strip()
    if "CONTENT:" in response:
        content = response.split("CONTENT:")[1].strip()
    
    return title, content, keyword

def post_to_blogger(title, content, category, image_url=None, photographer=None, photo_link=None):
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
    
    image_html = ""
    if image_url:
        image_html = f'''
<div style="text-align:center; margin-bottom:24px;">
    <img src="{image_url}" style="max-width:100%; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
    <p style="font-size:11px; color:#999; margin-top:6px;">Photo by <a href="{photo_link}" target="_blank">{photographer}</a> on <a href="https://www.pexels.com" target="_blank">Pexels</a></p>
</div>
'''
    
    category_badge = f'<div style="display:inline-block; background:#ff6b6b; color:white; padding:4px 12px; border-radius:20px; font-size:13px; margin-bottom:16px;">{category}</div>'
    
    full_content = category_badge + image_html + content
    
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
            image_url, photographer, photo_link = get_pexels_image(keyword)
            if image_url:
                print(f"이미지 찾음: {image_url}")
            else:
                print("이미지 없음, 텍스트만 포스팅")
            
            url = post_to_blogger(title, content, item['category'], image_url, photographer, photo_link)
            msg = f"✅ 포스팅 {i+1} 성공!\n카테고리: {item['category']}\n제목: {title}\n주소: {url}"
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
