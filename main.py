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

STRICT HTML STRUCTURE (no h1 tag — platform adds it automatically):

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
- Do NOT use h1 tag anywhere

OUTPUT FORMAT:
TITLE​​​​​​​​​​​​​​​​
