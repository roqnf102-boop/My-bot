"""
파워블로그 자동화 시스템 v2.0
"""

import os
import time
import json
import random
import requests
import anthropic
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SEED_KEYWORDS = [
    "korean convenience store snacks",
    "korean skincare routine steps",
    "korean drama filming location",
    "korean fried chicken recipe",
    "korean glass skin routine",
    "korean apartment tour",
    "korean lunch box ideas",
    "korean street food recipe",
    "korean face mask review",
    "korean traditional clothing",
    "korean ramen recipe",
    "korean work culture",
    "korean beauty ingredients",
    "korean grocery haul",
    "korean webtoon recommendation",
]

TREND_CATEGORIES = {
    "food": ["korean bbq", "korean food", "korean recipe", "korean snack"],
    "beauty": ["korean skincare", "k-beauty", "korean makeup", "korean serum"],
    "culture": ["kpop", "kdrama", "korean drama", "korean movie"],
    "travel": ["korea travel", "seoul travel", "busan travel", "korea trip"],
    "lifestyle": ["korean lifestyle", "korean culture", "korean language", "korean tradition"],
}

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

def get_trending_keywords():
    print("📈 Google Trends 키워드 수집 중...")
    trending = []
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        for category, keywords in TREND_CATEGORIES.items():
            try:
                pytrends.build_payload(
                    keywords[:4],
                    cat=0,
                    timeframe='now 1-d',
                    geo='US'
                )
                data = pytrends.interest_over_time()
                if not data.empty:
                    for kw in keywords[:4]:
                        if kw in data.columns:
                            score = int(data[kw].mean())
                            if score > 10:
                                trending.append({
                                    "keyword": kw,
                                    "category": category,
                                    "trend_score": score
                                })
                time.sleep(1)
            except Exception as e:
                print(f"  카테고리 {category} 에러: {e}")
                continue
        trending.sort(key=lambda x: x['trend_score'], reverse=True)
        print(f"  트렌딩 키워드 {len(trending)}개 수집 완료")
    except Exception as e:
        print(f"  Trends 에러: {e}, 시드 키워드로 대체합니다.")

    if not trending:
        for kw in random.sample(SEED_KEYWORDS, min(5, len(SEED_KEYWORDS))):
            trending.append({
                "keyword": kw,
                "category": "lifestyle",
                "trend_score": 50
            })
    return trending

def analyze_keyword_competition(trending_keywords):
    print("🔍 Search Console 경쟁도 분석 중...")
    try:
        creds = Credentials(
            token=None,
            refresh_token=os.environ.get('BLOGGER_REFRESH_TOKEN'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get('BLOGGER_CLIENT_ID'),
            client_secret=os.environ.get('BLOGGER_CLIENT_SECRET'),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        creds.refresh(Request())
        service = build('searchconsole', 'v1', credentials=creds)

        site_url = os.environ.get('BLOG_SITE_URL')
        if not site_url:
            print("  BLOG_SITE_URL 없음. 트렌드 점수만으로 선별합니다.")
            return trending_keywords[:3]

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['query'],
                'rowLimit': 1000
            }
        ).execute()

        existing_keywords = set()
        for row in response.get('rows', []):
            query = row['keys'][0].lower()
            clicks = row.get('clicks', 0)
            position = row.get('position', 100)
            if position <= 20 and clicks > 0:
                existing_keywords.add(query)

        print(f"  기존 상위 노출 키워드 {len(existing_keywords)}개 제외")

        niche_keywords = []
        for item in trending_keywords:
            kw = item['keyword'].lower()
            is_existing = any(kw in ex or ex in kw for ex in existing_keywords)
            if not is_existing:
                niche_keywords.append(item)

        print(f"  틈새 키워드 {len(niche_keywords)}개 선별 완료")
        return niche_keywords[:3] if niche_keywords else trending_keywords[:3]

    except Exception as e:
        print(f"  Search Console 에러: {e}. 트렌드 점수만으로 선별합니다.")
        return trending_keywords[:3]

def generate_power_post(keyword_item):
    api_key = os.environ.get('CLAUDE_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)

    keyword = keyword_item['keyword']
    category = keyword_item['category']
    trend_score = keyword_item['trend_score']

    prompt = f"""You are a passionate Korean culture expert and power blogger with 10+ years living between Korea and the US.
You write deeply personal, insightful, and practical content that American readers absolutely love.
Your writing style: warm, specific, opinionated, and packed with details Americans can't find elsewhere.

TARGET KEYWORD: "{keyword}"
CATEGORY: {category}
TREND SCORE: {trend_score}/100 (this keyword is currently trending in the US)

Write a COMPREHENSIVE, SEO-optimized blog post of 1,500-2,000 words.

CONTENT STRATEGY:
- Answer exactly what Americans are searching for with "{keyword}"
- Include personal anecdotes or specific examples (can be semi-fictional but realistic)
- Add practical, actionable information they can use TODAY
- Reference specific Korean brands, places, or products when relevant
- Compare Korean and American perspectives to create "aha" moments
- Include insider tips most blogs don't share

STRICT HTML STRUCTURE (no <h1> — platform adds it automatically):

<p class="intro">[Hook: Start with a surprising fact, question, or personal story. 2-3 sentences.]</p>

<h2>[Keyword-rich subheading #1]</h2>
<p>[250-300 words: Deep dive with specific details, personal angle, cultural context]</p>

<h2>[Subheading #2 — practical/how-to angle]</h2>
<p>[250-300 words: Actionable info, step-by-step if relevant, specific product/place names]</p>

<h2>[Subheading #3 — insider secrets or comparison]</h2>
<p>[200-250 words: The insider knowledge angle — what most blogs miss]</p>

<h2>[Subheading #4 — why it matters for Americans]</h2>
<p>[200-250 words: Connect to American lifestyle, where to find/buy, how to start]</p>

<h2>Final Thoughts</h2>
<p>[150-200 words: Personal wrap-up, encourage comments, ask a specific engaging question]</p>

<p><strong>Question for you: [Specific engaging question that invites comments]</strong></p>

WRITING RULES:
- Total: 1,500-2,000 words
- No fluff, every sentence must add value
- Use "you" and "I" naturally
- Mention specific Korean brands, neighborhoods, products by name
- Include at least 3 specific examples or data points
- Natural keyword placement
- Do NOT use <h1> anywhere

OUTPUT FORMAT:
TITLE: [Compelling SEO title, 50-60 chars, includes main keyword]
META: [Meta description under 155 chars, includes keyword, creates curiosity]
KEYWORD: [Single English word for Pexels image search: food/beauty/travel/music/lifestyle]
TAGS: [5 relevant blog tags separated by commas]
CONTENT: [Full HTML content starting with <p class="intro">]
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text
    title = keyword.title()
    meta = ""
    pexels_keyword = "korea"
    tags = []
    content = response

    if "TITLE:" in response:
        title = response.split("TITLE:")[1].split("\n")[0].strip()
    if "META:" in response:
        meta = response.split("META:")[1].split("\n")[0].strip()
    if "KEYWORD:" in response:
        pexels_keyword = response.split("KEYWORD:")[1].split("\n")[0].strip().lower()
    if "TAGS:" in response:
        tags_raw = response.split("TAGS:")[1].split("\n")[0].strip()
        tags = [t.strip() for t in tags_raw.split(",")]
    if "CONTENT:" in response:
        content = response.split("CONTENT:")[1].strip()

    word_count = len(content.replace('<', ' <').split())
    print(f"  생성된 글 단어 수: {word_count}단어")
    return title, content, pexels_keyword, meta, tags

def get_pexels_image(keyword, title=""):
    try:
        api_key = os.environ.get('PEXELS_API_KEY')
        keyword_map = {
            "food": "korean food dish",
            "beauty": "skincare beauty products",
            "travel": "korea city landscape",
            "music": "kpop music concert",
            "lifestyle": "korea daily life",
            "culture": "korean traditional culture",
        }
        search_keyword = keyword_map.get(keyword.lower(), f"korea {keyword}")
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": search_keyword, "per_page": 3, "orientation": "landscape"}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get("photos") and len(data["photos"]) > 0:
            photo = random.choice(data["photos"])
            image_url = photo["src"]["large"]
            photographer = photo["photographer"]
            photo_link = photo["url"]
            alt_text = title[:100] if title else f"{search_keyword} - Korean lifestyle"
            return image_url, photographer, photo_link, alt_text
    except Exception as e:
        print(f"  Pexels 에러: {e}")
    return None, None, None, None

def post_to_blogger(title, content, meta="", tags=None, image_url=None, photographer=None, photo_link=None, alt_text=None):
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

    json_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": meta,
        "datePublished": datetime.now().isoformat(),
        "author": {
            "@type": "Person",
            "name": "Korean Lifestyle Expert"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Korean Lifestyle Blog"
        },
        "image": image_url or "",
        "keywords": ", ".join(tags) if tags else ""
    }

    meta_jsonld = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>\n'

    image_html = ""
    if image_url:
        image_html = f'''
<div style="text-align:center; margin: 0 0 32px 0;">
    <img src="{image_url}" alt="{alt_text}" title="{alt_text}"
         style="max-width:100%; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.12);" />
    <p style="font-size:11px; color:#aaa; margin-top:8px;">
        Photo by <a href="{photo_link}" target="_blank" rel="noopener">{photographer}</a>
        on <a href="https://www.pexels.com" target="_blank" rel="noopener">Pexels</a>
    </p>
</div>
'''

    full_content = meta_jsonld + image_html + content

    body = {
        "title": title,
        "content": full_content,
    }
    if tags:
        body["labels"] = tags[:5]

    result = service.posts().insert(
        blogId=os.environ.get('BLOG_ID'),
        body=body
    ).execute()

    return result.get('url')

def request_google_indexing(post_url):
    try:
        service_account_json = os.environ.get('GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON', '{}')
        service_account_info = json.loads(service_account_json)
        if not service_account_info:
            print("  ⚠️ Indexing API 서비스 계정 없음. 건너뜁니다.")
            return False
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/indexing"]
        )
        credentials.refresh(Request())
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        body = {"url": post_url, "type": "URL_UPDATED"}
        response = requests.post(endpoint, headers=headers, json=body)
        if response.status_code == 200:
            print(f"  ✅ Google 색인 요청 성공: {post_url}")
            return True
        else:
            print(f"  ⚠️ 색인 요청 실패 ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"  색인 요청 에러: {e}")
        return False

def main():
    print("=" * 50)
    print("🚀 파워블로그 자동화 시스템 v2.0 시작")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    trending = get_trending_keywords()
    if not trending:
        send_telegram("⚠️ 트렌드 키워드 수집 실패")
        return

    niche_keywords = analyze_keyword_competition(trending)
    print(f"\n✅ 오늘 공략할 키워드:")
    for item in niche_keywords:
        print(f"  - [{item['category']}] {item['keyword']} (트렌드: {item['trend_score']})")

    success_count = 0
    for i, keyword_item in enumerate(niche_keywords):
        print(f"\n--- 포스팅 {i+1}/{len(niche_keywords)}: {keyword_item['keyword']} ---")
        try:
            print("  ✍️ 글 생성 중 (1,500단어+)...")
            title, content, pexels_kw, meta, tags = generate_power_post(keyword_item)
            print(f"  제목: {title}")

            print(f"  🖼️ 이미지 검색: {pexels_kw}")
            image_url, photographer, photo_link, alt_text = get_pexels_image(pexels_kw, title)

            print("  📤 Blogger 발행 중...")
            url = post_to_blogger(title, content, meta, tags, image_url, photographer, photo_link, alt_text)
            print(f"  URL: {url}")

            if url:
                request_google_indexing(url)

            msg = (
                f"✅ 포스팅 {i+1} 성공!\n"
                f"키워드: {keyword_item['keyword']}\n"
                f"제목: {title}\n"
                f"URL: {url}"
            )
            send_telegram(msg)
            success_count += 1

            if i < len(niche_keywords) - 1:
                print("  ⏳ 30초 대기 중...")
                time.sleep(30)

        except Exception as e:
            msg = f"❌ 포스팅 {i+1} 실패 [{keyword_item['keyword']}]: {e}"
            print(f"  {msg}")
            send_telegram(msg)

    summary = (
        f"🎉 오늘 포스팅 완료!\n"
        f"성공: {success_count}/{len(niche_keywords)}개\n"
        f"키워드: {', '.join([k['keyword'] for k in niche_keywords])}"
    )
    print(f"\n{summary}")
    send_telegram(summary)

if __name__ == "__main__":
    main()
