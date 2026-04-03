import os
import time
import json
import random
import requests
import anthropic
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────
# 12개 세분화 카테고리 (겹침 최소화)
# ─────────────────────────────────────────
CATEGORIES = {
    "korean_snacks": {
        "keywords": ["korean convenience store snacks", "korean chip flavors", "korean candy", "buldak noodles"],
        "angle": "Americans discovering Korean snacks for the first time — surprise, comparison, where to buy"
    },
    "korean_cooking": {
        "keywords": ["korean home cooking", "gochujang recipes", "doenjang jjigae", "korean rice dishes"],
        "angle": "Making authentic Korean food at home with US grocery store ingredients"
    },
    "korean_bbq": {
        "keywords": ["korean bbq at home", "samgyeopsal", "galbi recipe", "korean bbq sauce"],
        "angle": "Replicating the Korean BBQ restaurant experience at home"
    },
    "kbeauty_routine": {
        "keywords": ["korean skincare routine", "glass skin routine", "double cleansing", "korean toner pad"],
        "angle": "Step-by-step K-beauty routines that actually work for Western skin types"
    },
    "kbeauty_ingredients": {
        "keywords": ["snail mucin skincare", "centella asiatica benefits", "niacinamide korean", "propolis serum"],
        "angle": "Science behind Korean beauty ingredients explained simply"
    },
    "kdrama_culture": {
        "keywords": ["kdrama recommendations", "korean drama explained", "kdrama tropes", "best kdrama 2024"],
        "angle": "Why Americans are obsessed with K-dramas — cultural analysis and picks"
    },
    "kpop_lifestyle": {
        "keywords": ["kpop idol diet", "kpop workout routine", "korean celebrity skincare", "kpop fashion"],
        "angle": "What everyday Korean lifestyle habits we can realistically adopt"
    },
    "korea_travel": {
        "keywords": ["seoul travel tips", "busan itinerary", "korea hidden gems", "korea travel budget"],
        "angle": "First-timer and off-the-beaten-path Korea travel from American perspective"
    },
    "korean_cafe": {
        "keywords": ["korean cafe culture", "korean dalgona coffee", "korean dessert cafe", "bingsu recipe"],
        "angle": "The Korean cafe aesthetic and how to bring it home"
    },
    "korean_wellness": {
        "keywords": ["korean health food", "korean diet habits", "korean fermented food", "kimchi health benefits"],
        "angle": "Korean wellness habits backed by science that Americans should try"
    },
    "korean_fashion": {
        "keywords": ["korean street fashion", "korean minimalist style", "korean outfit ideas", "seoul fashion"],
        "angle": "How to incorporate Korean fashion trends into everyday American wardrobe"
    },
    "korean_language": {
        "keywords": ["learn korean basics", "korean phrases for travel", "korean honorifics", "hangul for beginners"],
        "angle": "Practical Korean language tips for pop culture fans and travelers"
    },
}

HISTORY_FILE = "post_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"posted_categories": [], "posted_keywords": []}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
    except Exception:
        pass

def get_google_news_trending():
    """pytrends 실패 시 Google News RSS로 한국 관련 트렌드 수집"""
    trending = []
    try:
        rss_url = "https://news.google.com/rss/search?q=korean+culture+food+beauty&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(rss_url, timeout=10)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:10]
        for item in items:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                trending.append(title_el.text.lower())
        print(f"Google News RSS에서 {len(trending)}개 트렌드 수집")
    except Exception as e:
        print(f"Google News RSS 에러: {e}")
    return trending

def get_trending_keywords(history):
    """pytrends + Google News RSS 듀얼 소스, 중복 카테고리 제외"""
    print("트렌드 키워드 수집 중...")
    
    posted_cats = set(history.get("posted_categories", []))
    posted_kws = set(history.get("posted_keywords", []))
    
    # 최근 7일 이내 포스팅한 카테고리 제외 (순환)
    available_categories = {
        k: v for k, v in CATEGORIES.items() 
        if k not in posted_cats
    }
    # 모두 포스팅했으면 히스토리 리셋
    if not available_categories:
        print("모든 카테고리 순환 완료 — 히스토리 초기화")
        history["posted_categories"] = []
        history["posted_keywords"] = []
        available_categories = CATEGORIES.copy()

    # pytrends 시도
    trending_scores = {}
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        for cat_name, cat_data in available_categories.items():
            keywords = cat_data["keywords"][:4]
            try:
                pytrends.build_payload(keywords, cat=0, timeframe="now 1-d", geo="US")
                data = pytrends.interest_over_time()
                if not data.empty:
                    score = 0
                    for kw in keywords:
                        if kw in data.columns:
                            score += int(data[kw].mean())
                    trending_scores[cat_name] = score
                time.sleep(2)
            except Exception:
                trending_scores[cat_name] = random.randint(30, 70)
    except Exception as e:
        print(f"pytrends 전체 실패, RSS 백업 사용: {e}")
        for cat_name in available_categories:
            trending_scores[cat_name] = random.randint(30, 70)

    # 점수 기반 정렬, 상위 3개 카테고리 선택
    sorted_cats = sorted(trending_scores.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for cat_name, score in sorted_cats[:3]:
        cat_data = available_categories[cat_name]
        # 포스팅 안 한 키워드 선택
        available_kws = [kw for kw in cat_data["keywords"] if kw not in posted_kws]
        if not available_kws:
            available_kws = cat_data["keywords"]
        
        keyword = random.choice(available_kws)
        result.append({
            "category": cat_name,
            "keyword": keyword,
            "angle": cat_data["angle"],
            "trend_score": score
        })
    
    print(f"오늘 선택된 카테고리: {[r['category'] for r in result]}")
    return result, history

def generate_power_post(keyword_item):
    api_key = os.environ.get("CLAUDE_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    keyword = keyword_item["keyword"]
    category = keyword_item["category"]
    angle = keyword_item["angle"]
    trend_score = keyword_item["trend_score"]

    # 카테고리별 특화 지시사항
    category_instructions = {
        "korean_snacks": "Include specific product names available on Amazon or H-Mart. Add a 'Where to Buy' mini-section.",
        "korean_cooking": "Include substitution tips for hard-to-find Korean ingredients at US grocery stores.",
        "korean_bbq": "Compare experience vs US BBQ culture. Include specific cuts of meat and where to buy them.",
        "kbeauty_routine": "Address common concerns: will this work for oily/dry/sensitive Western skin? Be specific.",
        "kbeauty_ingredients": "Explain the science in plain English. Compare to familiar Western skincare equivalents.",
        "kdrama_culture": "Include specific episode/show recommendations with streaming platform info.",
        "kpop_lifestyle": "Be realistic about what's achievable. Avoid diet content that could be harmful.",
        "korea_travel": "Include specific subway lines, neighborhoods, and realistic budget numbers in USD.",
        "korean_cafe": "Include DIY recipes to recreate cafe drinks at home.",
        "korean_wellness": "Cite health benefits with balanced perspective. Connect to habits Americans already have.",
        "korean_fashion": "Link to specific styles Americans can find at accessible price points.",
        "korean_language": "Include romanization + actual Hangul + audio-description pronunciation tips.",
    }

    special_instruction = category_instructions.get(category, "Be specific and practical.")

    prompt = f"""You are an American who lived in Korea for 8 years and now writes the most-read Korean culture blog in the US.
Your readers trust you because you're honest, specific, and you understand both cultures deeply.
You are NOT generic — you have strong opinions and real experiences.

TARGET KEYWORD: {keyword}
CATEGORY: {category}
TODAY'S ANGLE: {angle}
SPECIAL INSTRUCTION: {special_instruction}

Write a POWERFUL, SEO-optimized blog post of 1,500-2,000 words.

CONTENT RULES:
1. Open with a HOOK — a surprising fact, personal story, or bold claim (NOT "Are you curious about...")
2. Every section must have at least one SPECIFIC detail (brand name, street name, price, or personal anecdote)
3. Include one "Myth vs Reality" or "What Most Blogs Get Wrong" point
4. Natural keyword usage — write for humans, not search engines
5. End with a genuine question that invites comments

HTML FORMAT (NO h1 tags — platform adds title automatically):

<p class="intro"><strong>[Hook sentence — surprising, specific, personal]</strong> [2-3 follow-up sentences building intrigue.]</p>

<h2>[Keyword-rich subheading — what readers actually want to know]</h2>
<p>[250-300 words — deep cultural context + personal experience]</p>

<h2>[Practical How-To subheading]</h2>
<p>[250-300 words — step-by-step, specific product/place names, tips]</p>

<h2>What Most Blogs Get Wrong About [topic]</h2>
<p>[200-250 words — contrarian take, myth-busting, insider knowledge]</p>

<h2>[American Perspective / Why This Matters for You subheading]</h2>
<p>[200-250 words — bridge Korean → American lifestyle, practical application]</p>

<h2>My Honest Take</h2>
<p>[150-200 words — personal wrap-up, what to try first, final recommendation]</p>

<p><strong>Question for you: [specific, engaging question related to the topic]</strong></p>

OUTPUT FORMAT (follow EXACTLY, each on its own line):
TITLE: [SEO title 50-60 chars, include main keyword naturally]
META: [155 chars max — benefit-driven, not keyword-stuffed]
KEYWORD: [ONE word for Pexels image search: food OR beauty OR travel OR lifestyle OR fashion OR wellness]
TAGS: [exactly 5 tags, comma-separated, mix of broad and specific]
CONTENT:
[full HTML content starting with <p class="intro">]"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text
    
    # 파싱
    title = keyword.replace("-", " ").title()
    meta = ""
    pexels_keyword = "korea"
    tags = []
    content = ""

    lines = response.split("\n")
    content_start = False
    content_lines = []

    for i, line in enumerate(lines):
        if line.startswith("TITLE:") and not content_start:
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("META:") and not content_start:
            meta = line.replace("META:", "").strip()
        elif line.startswith("KEYWORD:") and not content_start:
            pexels_keyword = line.replace("KEYWORD:", "").strip().lower()
        elif line.startswith("TAGS:") and not content_start:
            tags_raw = line.replace("TAGS:", "").strip()
            tags = [t.strip() for t in tags_raw.split(",")][:5]
        elif line.startswith("CONTENT:") and not content_start:
            content_start = True
        elif content_start:
            content_lines.append(line)

    content = "\n".join(content_lines).strip()
    
    # CONTENT 파싱 실패 시 폴백
    if not content and "CONTENT:" in response:
        content = response.split("CONTENT:")[1].strip()

    word_count = len(content.split())
    print(f"생성된 글: {word_count}단어")
    return title, content, pexels_keyword, meta, tags

def get_pexels_image(keyword, title=""):
    try:
        api_key = os.environ.get("PEXELS_API_KEY")
        keyword_map = {
            "food": "korean food dish restaurant",
            "beauty": "skincare beauty korean products",
            "travel": "seoul korea cityscape",
            "lifestyle": "korea daily life modern",
            "fashion": "korean street style fashion",
            "wellness": "healthy korean food lifestyle",
            "music": "kpop concert music",
        }
        search_query = keyword_map.get(keyword.lower(), f"korea {keyword}")
        
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": search_query, "per_page": 5, "orientation": "landscape", "size": "large"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if data.get("photos"):
            # 첫 번째 사진 선택 (가장 관련성 높음)
            photo = data["photos"][0]
            image_url = photo["src"]["large2x"]  # 고화질
            photographer = photo["photographer"]
            photo_link = photo["url"]
            alt_text = (title[:80] if title else search_query) + " | Korean lifestyle"
            return image_url, photographer, photo_link, alt_text
    except Exception as e:
        print(f"Pexels 에러: {e}")
    return None, None, None, None

def post_to_blogger(title, content, meta="", tags=None, image_url=None, photographer=None, photo_link=None, alt_text=None):
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("BLOGGER_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("BLOGGER_CLIENT_ID"),
        client_secret=os.environ.get("BLOGGER_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    creds.refresh(Request())
    service = build("blogger", "v3", credentials=creds)

    # JSON-LD 스키마
    json_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": meta,
        "datePublished": datetime.now().isoformat(),
        "author": {"@type": "Person", "name": "KBeauty Insider"},
        "publisher": {
            "@type": "Organization", 
            "name": "Korean Lifestyle Insider",
            "logo": {"@type": "ImageObject", "url": ""}
        },
        "image": image_url or "",
        "keywords": ", ".join(tags) if tags else ""
    }

    meta_tags = (
        f'<meta name="description" content="{meta}" />\n' if meta else ""
    )
    schema = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>\n'

    # 이미지 HTML (크레딧 포함)
    image_html = ""
    if image_url:
        image_html = f"""<div style="text-align:center; margin:0 0 36px 0;">
<img src="{image_url}" alt="{alt_text}" title="{alt_text}"
  style="max-width:100%; border-radius:16px; box-shadow:0 6px 24px rgba(0,0,0,0.15);" loading="lazy" />
<p style="font-size:11px; color:#999; margin-top:8px;">
Photo by <a href="{photo_link}" target="_blank" rel="noopener noreferrer">{photographer}</a>
on <a href="https://www.pexels.com" target="_blank" rel="noopener noreferrer">Pexels</a>
</p></div>\n"""

    full_content = meta_tags + schema + image_html + content
    
    body = {"title": title, "content": full_content}
    if tags:
        body["labels"] = tags[:5]

    result = service.posts().insert(
        blogId=os.environ.get("BLOG_ID"),
        body=body,
        isDraft=False
    ).execute()

    return result.get("url", "")

def request_google_indexing(post_url):
    try:
        sa_json = os.environ.get("GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON", "{}")
        sa_info = json.loads(sa_json)
        if not sa_info.get("private_key"):
            print("Indexing API 서비스 계정 없음 — 건너뜀")
            return False
        
        credentials = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/indexing"]
        )
        credentials.refresh(Request())
        
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        body = {"url": post_url, "type": "URL_UPDATED"}
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        
        if response.status_code == 200:
            print(f"Google 색인 요청 성공: {post_url}")
            return True
        else:
            print(f"색인 요청 실패 ({response.status_code}): {response.text[:200]}")
            return False
    except Exception as e:
        print(f"색인 요청 에러: {e}")
        return False

def main():
    start_time = datetime.now()
    print(f"파워블로그 자동화 v3.0 시작 — {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 히스토리 로드 (중복 방지)
    history = load_history()
    
    # 트렌드 키워드 수집
    keyword_items, history = get_trending_keywords(history)
    
    if not keyword_items:
        send_telegram("❌ 키워드 수집 실패 — 포스팅 중단")
        return

    print(f"\n오늘 포스팅 계획 ({len(keyword_items)}개):")
    for item in keyword_items:
        print(f"  [{item['category']}] {item['keyword']} (트렌드: {item['trend_score']})")

    success_count = 0
    posted_urls = []

    for i, keyword_item in enumerate(keyword_items):
        print(f"\n{'='*50}")
        print(f"포스팅 {i+1}/{len(keyword_items)}: {keyword_item['keyword']}")
        
        try:
            # 글 생성
            print("글 생성 중...")
            title, content, pexels_kw, meta, tags = generate_power_post(keyword_item)
            print(f"제목: {title}")

            # 이미지
            print(f"Pexels 이미지 검색: {pexels_kw}")
            image_url, photographer, photo_link, alt_text = get_pexels_image(pexels_kw, title)
            print("이미지: " + ("찾음" if image_url else "없음 (이미지 없이 발행)"))

            # 발행
            print("Blogger 발행 중...")
            url = post_to_blogger(title, content, meta, tags, image_url, photographer, photo_link, alt_text)
            print(f"발행 완료: {url}")

            # Google 색인
            if url:
                request_google_indexing(url)
                posted_urls.append(url)

            # 히스토리 업데이트
            history["posted_categories"].append(keyword_item["category"])
            history["posted_keywords"].append(keyword_item["keyword"])
            # 최근 30개만 유지
            history["posted_categories"] = history["posted_categories"][-30:]
            history["posted_keywords"] = history["posted_keywords"][-30:]

            msg = f"✅ 포스팅 성공!\n카테고리: {keyword_item['category']}\n키워드: {keyword_item['keyword']}\n제목: {title}\nURL: {url}"
            send_telegram(msg)
            success_count += 1

            # 포스팅 간격 (Blogger API 안정성)
            if i < len(keyword_items) - 1:
                wait = 45
                print(f"{wait}초 대기...")
                time.sleep(wait)

        except Exception as e:
            error_msg = f"❌ 포스팅 실패 [{keyword_item['keyword']}]\n에러: {str(e)}"
            print(error_msg)
            send_telegram(error_msg)

    # 히스토리 저장
    save_history(history)

    # 완료 요약
    elapsed = (datetime.now() - start_time).seconds // 60
    summary = (
        f"🎉 오늘 포스팅 완료!\n"
        f"성공: {success_count}/{len(keyword_items)}개\n"
        f"소요시간: {elapsed}분\n"
        f"발행 URL:\n" + "\n".join(posted_urls)
    )
    print(summary)
    send_telegram(summary)

if __name__ == "__main__":
    main()
