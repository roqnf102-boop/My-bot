import os
import time
import json
import random
import requests
import feedparser
import anthropic
from datetime import datetime
from pytrends.request import TrendReq
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# ─────────────────────────────────────────
# 12개 세분화 카테고리 (롱테일 키워드)
# ─────────────────────────────────────────
CATEGORIES = {
    "korean_snacks": {
        "keywords": [
            "is buldak ramen actually from korea",
            "korean convenience store snacks ranked",
            "why korean chips taste different",
            "korean candy americans love"
        ],
        "angle": "Americans discovering Korean snacks — surprise, addiction, where to buy in US"
    },
    "korean_cooking": {
        "keywords": [
            "how to make kimchi jjigae without korean store",
            "gochujang substitute at walmart",
            "korean rice bowl recipe easy",
            "doenjang vs miso difference"
        ],
        "angle": "Authentic Korean cooking with ingredients from regular US grocery stores"
    },
    "korean_bbq": {
        "keywords": [
            "why korean bbq is different from american bbq",
            "how to do korean bbq at home without grill",
            "galbi vs kalbi spelling difference",
            "korean bbq side dishes names"
        ],
        "angle": "Replicating the full Korean BBQ experience at home in the US"
    },
    "kbeauty_routine": {
        "keywords": [
            "does korean skincare work for american skin",
            "korean 10 step routine simplified",
            "glass skin routine for beginners",
            "korean toner vs american toner difference"
        ],
        "angle": "K-beauty routines adapted for Western skin concerns and budgets"
    },
    "kbeauty_ingredients": {
        "keywords": [
            "what does snail mucin actually do",
            "centella asiatica vs niacinamide which is better",
            "korean skincare ingredients to avoid",
            "propolis serum benefits explained"
        ],
        "angle": "Korean beauty ingredients explained in plain science for skeptical Americans"
    },
    "kdrama_culture": {
        "keywords": [
            "why are kdrama so addictive psychology",
            "best kdrama for beginners on netflix 2025",
            "kdrama vs american tv show differences",
            "korean drama filming locations real places"
        ],
        "angle": "Why Americans can't stop watching K-dramas — honest cultural breakdown"
    },
    "kpop_lifestyle": {
        "keywords": [
            "kpop idol daily routine realistic version",
            "korean celebrity skin secret affordable",
            "kpop fashion style for everyday americans",
            "what kpop idols actually eat in a day"
        ],
        "angle": "Realistic Korean lifestyle habits Americans can actually adopt"
    },
    "korea_travel": {
        "keywords": [
            "things nobody tells you before going to korea",
            "seoul travel budget for americans 2025",
            "korea without speaking korean possible",
            "best neighborhoods in seoul for first timers"
        ],
        "angle": "Honest first-timer Korea travel guide from American perspective"
    },
    "korean_cafe": {
        "keywords": [
            "why korean cafe culture is different",
            "bingsu recipe without korean ingredients",
            "korean dalgona coffee original vs starbucks",
            "korean cafe aesthetic at home diy"
        ],
        "angle": "Korean cafe culture explained and recreated at home in the US"
    },
    "korean_wellness": {
        "keywords": [
            "is kimchi actually good for gut health science",
            "korean diet habits americans should steal",
            "gochujang health benefits real or hype",
            "korean fermented foods vs american probiotics"
        ],
        "angle": "Science-backed Korean wellness habits for health-conscious Americans"
    },
    "korean_fashion": {
        "keywords": [
            "korean street fashion vs american style difference",
            "how to dress like korean on amazon budget",
            "seoul fashion trends americans can wear",
            "korean minimal style for work outfits"
        ],
        "angle": "Korean fashion trends adapted for everyday American wardrobes"
    },
    "korean_language": {
        "keywords": [
            "is korean hard to learn for english speakers",
            "korean words english speakers already know",
            "how to read hangul in one hour",
            "korean phrases that have no english translation"
        ],
        "angle": "Korean language made approachable for K-pop and K-drama fans"
    },
}

HISTORY_FILE = "post_history.json"

# ─────────────────────────────────────────
# 히스토리
# ─────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"posted_categories": [], "posted_keywords": []}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ─────────────────────────────────────────
# 텔레그램
# ─────────────────────────────────────────
def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10
        )
    except Exception:
        pass

# ─────────────────────────────────────────
# Google News RSS 백업
# ─────────────────────────────────────────
def get_google_news_trending():
    trending = []
    try:
        rss_url = "https://news.google.com/rss/search?q=korean+culture+food+beauty&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            trending.append(entry.title.lower())
        print(f"Google News RSS {len(trending)}개 수집")
    except Exception as e:
        print(f"Google News RSS 에러: {e}")
    return trending

# ─────────────────────────────────────────
# 트렌드 키워드 수집
# ─────────────────────────────────────────
def get_trending_keywords(history):
    print("트렌드 키워드 수집 중...")

    posted_cats = set(history.get("posted_categories", []))
    posted_kws = set(history.get("posted_keywords", []))

    available_categories = {k: v for k, v in CATEGORIES.items() if k not in posted_cats}

    if not available_categories:
        print("모든 카테고리 순환 완료 — 히스토리 초기화")
        history["posted_categories"] = []
        history["posted_keywords"] = []
        available_categories = CATEGORIES.copy()

    trending_scores = {}
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        for cat_name, cat_data in available_categories.items():
            keywords = cat_data["keywords"][:4]
            try:
                pytrends.build_payload(keywords, cat=0, timeframe="now 1-d", geo="US")
                data = pytrends.interest_over_time()
                score = 0
                if not data.empty:
                    for kw in keywords:
                        if kw in data.columns:
                            score += int(data[kw].mean())
                trending_scores[cat_name] = score if score > 0 else random.randint(30, 70)
                time.sleep(2)
            except Exception:
                trending_scores[cat_name] = random.randint(30, 70)
    except Exception as e:
        print(f"pytrends 실패, 랜덤 점수 사용: {e}")
        for cat_name in available_categories:
            trending_scores[cat_name] = random.randint(30, 70)

    sorted_cats = sorted(trending_scores.items(), key=lambda x: x[1], reverse=True)

    result = []
    for cat_name, score in sorted_cats[:3]:
        cat_data = available_categories[cat_name]
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

    print(f"선택된 카테고리: {[r['category'] for r in result]}")
    return result, history

# ─────────────────────────────────────────
# 글 생성 (E-E-A-T + 롱테일 SEO 최적화)
# ─────────────────────────────────────────
def generate_power_post(keyword_item):
    api_key = os.environ.get("CLAUDE_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    keyword = keyword_item["keyword"]
    category = keyword_item["category"]
    angle = keyword_item["angle"]

    category_instructions = {
        "korean_snacks": "Include specific product names on Amazon/H-Mart. Add 'Where to Buy in the US' section. Mention exact prices in USD.",
        "korean_cooking": "Include substitution tips for US grocery stores. Mention specific US store names like Whole Foods, Trader Joe's.",
        "korean_bbq": "Compare vs American BBQ culture with specific differences. Include meat cuts with US supermarket names.",
        "kbeauty_routine": "Address oily/dry/sensitive Western skin specifically. Name exact products with Amazon search terms.",
        "kbeauty_ingredients": "Explain science in plain English. Compare to CeraVe/Neutrogena equivalents Americans know.",
        "kdrama_culture": "Include Netflix/Viki/Hulu specific show names with release years. Add episode count.",
        "kpop_lifestyle": "Focus only on realistic healthy habits. Avoid any diet restriction content.",
        "korea_travel": "Use specific subway line numbers, USD budget amounts, neighborhood names.",
        "korean_cafe": "Include DIY recipes with US grocery store ingredients and measurements in cups/oz.",
        "korean_wellness": "Reference specific studies or traditional Korean medicine terms. Connect to US health trends.",
        "korean_fashion": "Name specific styles with ASOS/Zara/Amazon accessible alternatives.",
        "korean_language": "Write romanization + Hangul + phonetic pronunciation like 'sounds like...'"
    }

    special_instruction = category_instructions.get(category, "Be specific with names, prices, and places.")

    longtail_prompts = {
        "korean_snacks": f"why is {keyword} so addictive",
        "korean_cooking": f"how to make {keyword} without korean grocery store",
        "korean_bbq": f"what makes {keyword} different from american bbq",
        "kbeauty_routine": f"does {keyword} actually work for western skin",
        "kbeauty_ingredients": f"what does {keyword} actually do to your skin",
        "kdrama_culture": f"why are americans obsessed with {keyword}",
        "kpop_lifestyle": f"what {keyword} habits are actually realistic",
        "korea_travel": f"what nobody tells you about {keyword}",
        "korean_cafe": f"how to recreate {keyword} at home",
        "korean_wellness": f"is {keyword} actually good for you",
        "korean_fashion": f"how to dress like {keyword} on a budget",
        "korean_language": f"easiest way to learn {keyword} as an adult",
    }

    longtail_keyword = longtail_prompts.get(category, keyword)

    prompt = f"""You are Sarah Kim — Korean-American blogger, lived in Seoul 8 years, now in Austin TX.
You write for real Americans who are curious but skeptical. Your readers call you out if you're vague.
You NEVER write like AI. You write like a friend texting you the real truth.

PRIMARY KEYWORD: {keyword}
LONGTAIL TARGET: {longtail_keyword}
SPECIAL INSTRUCTION: {special_instruction}

CRITICAL SEO RULES:
- Use PRIMARY KEYWORD in: first 100 words, one h2, last paragraph
- Use LONGTAIL KEYWORD in: one h2 heading naturally
- Total keyword density: 1-2% maximum (do NOT stuff)
- Write 1,800-2,000 words minimum

CONTENT MUST INCLUDE:
1. HOOK — first sentence must have a number OR surprising fact OR personal fail story
   Example: "I wasted $200 on Korean skincare before I learned this one thing."
   Example: "73% of Americans mispronounce gochujang — and Korean chefs notice."

2. PERSONAL STORY — one paragraph of real-sounding specific experience
   (specific location, year, Korean person's name, exact price in Korean won + USD)

3. MYTH BUSTING — "What influencers / other blogs / Americans get wrong about [topic]"

4. SPECIFIC DETAILS — every claim needs one of:
   - Brand name (Olive Young, Innisfree, CJ, etc.)
   - Price (₩3,500 / about $2.70)
   - Location (Myeongdong, Gangnam, H-Mart aisle 4)
   - Statistic or study reference

5. COMPARISON — Korean vs American version of the same thing

6. ACTIONABLE ENDING — exact first step reader can take TODAY

HTML STRUCTURE (NO h1 — platform adds it):

<p class="intro"><strong>[Number or shocking fact hook.]</strong> [Personal connection. Why you specifically are writing this.]</p>

<h2>[Longtail keyword phrased as question or statement]</h2>
<p>[250-300 words: personal story + cultural context + specific details]</p>

<h2>[Main keyword + practical angle]</h2>
<p>[250-300 words: step-by-step with brand names, prices, where to buy in US]</p>

<h2>What [Influencers/Blogs/Americans] Get Wrong About [topic]</h2>
<p>[200-250 words: myth bust, insider truth, specific example of wrong advice]</p>

<h2>The Korean Way vs The American Way</h2>
<p>[200-250 words: direct comparison, cultural insight, which is better and why]</p>

<h2>Your First Step (Do This Tonight)</h2>
<p>[150-200 words: ONE specific action, where to get it, exact cost, what to expect]</p>

<p><strong>Have you tried [specific thing]? Tell me in the comments — especially if [specific scenario].</strong></p>

OUTPUT FORMAT — follow EXACTLY:
TITLE: [question or number format, 50-60 chars, include main keyword]
META: [benefit + keyword + curiosity gap, under 155 chars]
KEYWORD: [ONE: food OR beauty OR travel OR lifestyle OR fashion OR wellness]
TAGS: [5 tags: 2 broad + 2 specific + 1 longtail phrase]
CONTENT:
[HTML starting with <p class="intro">]"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text

    title = keyword.replace("-", " ").title()
    meta = ""
    pexels_keyword = "korea"
    tags = []
    content = ""

    lines = response.split("\n")
    content_start = False
    content_lines = []

    for line in lines:
        if content_start:
            content_lines.append(line)
        elif line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("META:"):
            meta = line.replace("META:", "").strip()
        elif line.startswith("KEYWORD:"):
            pexels_keyword = line.replace("KEYWORD:", "").strip().lower()
        elif line.startswith("TAGS:"):
            tags_raw = line.replace("TAGS:", "").strip()
            tags = [t.strip() for t in tags_raw.split(",")][:5]
        elif line.startswith("CONTENT:"):
            content_start = True

    content = "\n".join(content_lines).strip()
    if not content and "CONTENT:" in response:
        content = response.split("CONTENT:")[1].strip()

    print(f"생성된 글: {len(content.split())}단어")
    return title, content, pexels_keyword, meta, tags

# ─────────────────────────────────────────
# Pexels 이미지
# ─────────────────────────────────────────
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
        }
        search_query = keyword_map.get(keyword.lower(), f"korea {keyword}")

        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": search_query, "per_page": 5, "orientation": "landscape", "size": "large"},
            timeout=10
        )
        data = response.json()

        if data.get("photos"):
            photo = data["photos"][0]
            alt_text = (title[:80] if title else search_query) + " | Korean lifestyle"
            return photo["src"]["large2x"], photo["photographer"], photo["url"], alt_text
    except Exception as e:
        print(f"Pexels 에러: {e}")
    return None, None, None, None

# ─────────────────────────────────────────
# Blogger 발행
# ─────────────────────────────────────────
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

    json_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": meta,
        "datePublished": datetime.now().isoformat(),
        "author": {"@type": "Person", "name": "Sarah Kim"},
        "publisher": {"@type": "Organization", "name": "Korean Lifestyle Insider"},
        "image": image_url or "",
        "keywords": ", ".join(tags) if tags else ""
    }

    schema = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>\n'
    meta_tag = f'<meta name="description" content="{meta}" />\n' if meta else ""

    image_html = ""
    if image_url:
        image_html = (
            f'<div style="text-align:center; margin:0 0 36px 0;">'
            f'<img src="{image_url}" alt="{alt_text}" title="{alt_text}"'
            f' style="max-width:100%; border-radius:16px; box-shadow:0 6px 24px rgba(0,0,0,0.15);" loading="lazy" />'
            f'<p style="font-size:11px; color:#999; margin-top:8px;">'
            f'Photo by <a href="{photo_link}" target="_blank" rel="noopener noreferrer">{photographer}</a>'
            f' on <a href="https://www.pexels.com" target="_blank" rel="noopener noreferrer">Pexels</a>'
            f'</p></div>\n'
        )

    full_content = meta_tag + schema + image_html + content
    body = {"title": title, "content": full_content}
    if tags:
        body["labels"] = tags[:5]

    result = service.posts().insert(
        blogId=os.environ.get("BLOG_ID"),
        body=body,
        isDraft=False
    ).execute()

    return result.get("url", "")

# ─────────────────────────────────────────
# Google 색인 요청
# ─────────────────────────────────────────
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

        response = requests.post(
            "https://indexing.googleapis.com/v3/urlNotifications:publish",
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            },
            json={"url": post_url, "type": "URL_UPDATED"},
            timeout=10
        )

        if response.status_code == 200:
            print(f"색인 요청 성공: {post_url}")
            return True
        else:
            print(f"색인 요청 실패 ({response.status_code})")
            return False
    except Exception as e:
        print(f"색인 요청 에러: {e}")
        return False

# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    start_time = datetime.now()
    print(f"파워블로그 자동화 v3.0 시작 — {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    history = load_history()
    keyword_items, history = get_trending_keywords(history)

    if not keyword_items:
        send_telegram("❌ 키워드 수집 실패")
        return

    print(f"\n오늘 포스팅 {len(keyword_items)}개:")
    for item in keyword_items:
        print(f"  [{item['category']}] {item['keyword']} (트렌드: {item['trend_score']})")

    success_count = 0
    posted_urls = []

    for i, keyword_item in enumerate(keyword_items):
        print(f"\n{'='*50}")
        print(f"포스팅 {i+1}/{len(keyword_items)}: {keyword_item['keyword']}")

        try:
            print("글 생성 중...")
            title, content, pexels_kw, meta, tags = generate_power_post(keyword_item)
            print(f"제목: {title}")

            print(f"이미지 검색: {pexels_kw}")
            image_url, photographer, photo_link, alt_text = get_pexels_image(pexels_kw, title)

            print("Blogger 발행 중...")
            url = post_to_blogger(title, content, meta, tags, image_url, photographer, photo_link, alt_text)
            print(f"발행 완료: {url}")

            if url:
                request_google_indexing(url)
                posted_urls.append(url)

            history["posted_categories"].append(keyword_item["category"])
            history["posted_keywords"].append(keyword_item["keyword"])
            history["posted_categories"] = history["posted_categories"][-30:]
            history["posted_keywords"] = history["posted_keywords"][-30:]

            send_telegram(
                f"✅ 포스팅 성공!\n"
                f"카테고리: {keyword_item['category']}\n"
                f"키워드: {keyword_item['keyword']}\n"
                f"제목: {title}\n"
                f"URL: {url}"
            )
            success_count += 1

            if i < len(keyword_items) - 1:
                print("45초 대기...")
                time.sleep(45)

        except Exception as e:
            print(f"포스팅 실패: {e}")
            send_telegram(f"❌ 포스팅 실패 [{keyword_item['keyword']}]\n{str(e)}")

    save_history(history)

    elapsed = (datetime.now() - start_time).seconds // 60
    summary = (
        f"🎉 완료! 성공 {success_count}/{len(keyword_items)}개\n"
        f"소요: {elapsed}분\n"
        + "\n".join(posted_urls)
    )
    print(summary)
    send_telegram(summary)

if __name__ == "__main__":
    main()
