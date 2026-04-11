import os
import json
import time
import base64
import random
import requests
from datetime import datetime
from pytrends.request import TrendReq
import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

# ── 환경변수 ──────────────────────────────────────────
CLAUDE_API_KEY       = os.environ["CLAUDE_API_KEY"]
BLOGGER_CLIENT_ID    = os.environ["BLOGGER_CLIENT_ID"]
BLOGGER_CLIENT_SECRET= os.environ["BLOGGER_CLIENT_SECRET"]
BLOGGER_REFRESH_TOKEN= os.environ["BLOGGER_REFRESH_TOKEN"]
BLOG_ID              = os.environ["BLOG_ID"]
PEXELS_API_KEY       = os.environ["PEXELS_API_KEY"]
TELEGRAM_BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID     = os.environ["TELEGRAM_CHAT_ID"]
BLOG_SITE_URL        = os.environ["BLOG_SITE_URL"]
SEARCH_CONSOLE_KEY   = os.environ.get("SEARCH_CONSOLE_KEY", "")

# ── 상수 ──────────────────────────────────────────────
SEED_KEYWORDS = [
    "Korean food", "K-beauty", "Korean drama", "Korean culture",
    "Korean skincare", "BTS", "Korean fashion", "Korean travel",
    "Korean recipes", "Seoul travel", "K-pop", "Korean language",
    "Korean traditions", "Korean street food", "Korean wellness"
]

BLOG_LABELS = ["Korean Culture", "K-Beauty", "Korean Food",
               "Korean Travel", "K-Pop", "Korean Lifestyle"]


# ══════════════════════════════════════════════════════
# 1. TREND RESEARCH
# ══════════════════════════════════════════════════════
def get_trending_keywords():
    """pytrends로 미국 내 한국 관련 인기 키워드 추출"""
    try:
        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        seed = random.sample(SEED_KEYWORDS, min(5, len(SEED_KEYWORDS)))
        pt.build_payload(seed, cat=0, timeframe="now 7-d", geo="US")
        related = pt.related_queries()

        candidates = []
        for kw, data in related.items():
            if data and data.get("top") is not None:
                top_df = data["top"]
                for _, row in top_df.head(5).iterrows():
                    candidates.append((row["query"], int(row["value"])))

        if not candidates:
            return seed[:3]

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [c[0] for c in candidates[:5]]
        print(f"[TRENDS] Top keywords: {top_keywords}")
        return top_keywords

    except Exception as e:
        print(f"[TRENDS] Error: {e} — using seed keywords")
        return random.sample(SEED_KEYWORDS, 3)


# ══════════════════════════════════════════════════════
# 2. CONTENT STRATEGY
# ══════════════════════════════════════════════════════
def build_content_strategy(keywords: list) -> dict:
    """키워드 → 포스트 전략 설계"""
    primary_kw = keywords[0] if keywords else "Korean culture"
    secondary  = keywords[1:4]

    strategies = [
        {
            "angle": "ultimate guide",
            "title_template": "The Ultimate Guide to {kw}: Everything Americans Need to Know in {year}",
            "intro_hook": "If you've been curious about {kw}, you're not alone — millions of Americans are discovering why Koreans have mastered this better than anyone else.",
        },
        {
            "angle": "insider secrets",
            "title_template": "{kw}: {n} Secrets Korean Locals Don't Tell Tourists ({year})",
            "intro_hook": "Koreans have a word for it that doesn't translate easily — and that's exactly why most Americans miss the whole point of {kw}.",
        },
        {
            "angle": "why it works",
            "title_template": "Why {kw} Is Taking Over America (And Why It's Not Just a Trend)",
            "intro_hook": "Walk into any major American city right now and you'll find {kw} everywhere. Here's the real story behind why it's sticking.",
        },
        {
            "angle": "beginners practical",
            "title_template": "How to Actually Start With {kw}: A No-BS Guide for Beginners",
            "intro_hook": "You've seen {kw} all over TikTok and Instagram. But where do you actually begin? We asked Korean experts so you don't have to.",
        },
    ]

    strategy = random.choice(strategies)
    n_secrets = random.randint(7, 15)
    year = datetime.now().year

    title = (strategy["title_template"]
             .replace("{kw}", primary_kw.title())
             .replace("{year}", str(year))
             .replace("{n}", str(n_secrets)))

    hook = (strategy["intro_hook"]
            .replace("{kw}", primary_kw)
            .replace("{n}", str(n_secrets)))

    label = random.choice(BLOG_LABELS)

    return {
        "title": title,
        "primary_keyword": primary_kw,
        "secondary_keywords": secondary,
        "hook": hook,
        "angle": strategy["angle"],
        "label": label,
        "n": n_secrets,
    }


# ══════════════════════════════════════════════════════
# 3. AI CONTENT GENERATION
# ══════════════════════════════════════════════════════
def generate_post(strategy: dict) -> str:
    """Claude API로 파워블로거 수준 영어 포스트 생성"""
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    secondary_str = ", ".join(strategy["secondary_keywords"]) if strategy["secondary_keywords"] else ""

    system_prompt = (
        "You are an expert American lifestyle blogger who specializes in Korean culture. "
        "You write for a mainstream US audience aged 25-45 who are curious but know little about Korea. "
        "Your writing style is: warm, conversational, slightly witty, never condescending. "
        "You use real anecdotes, specific details, and cultural context that makes readers feel they're learning insider knowledge. "
        "You naturally weave in SEO keywords without it feeling forced. "
        "You write in HTML format suitable for a blog post — use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em> tags. "
        "Never use markdown. Never add preamble or meta-commentary. Output only the blog post HTML body."
    )

    user_prompt = (
        "Write a high-quality, in-depth blog post with the following specifications:\n\n"
        "Title: " + strategy["title"] + "\n"
        "Primary keyword: " + strategy["primary_keyword"] + "\n"
        "Secondary keywords to naturally include: " + secondary_str + "\n"
        "Opening hook to use: " + strategy["hook"] + "\n"
        "Angle/style: " + strategy["angle"] + "\n\n"
        "Requirements:\n"
        "- Length: 1,800 to 2,500 words\n"
        "- Structure: engaging intro (2-3 paragraphs using the hook), "
        "5-8 main sections with H2 headers, practical tips or lists in each section, "
        "a warm conclusion with a call to action\n"
        "- Tone: like a knowledgeable American friend who loves Korea, not an academic\n"
        "- Include specific Korean words with explanations (e.g., 'han (한) — a uniquely Korean feeling of...')\n"
        "- Add relatable American comparisons where helpful\n"
        "- End with 3 FAQs in <h3> format\n"
        "- Primary keyword must appear in first 100 words and naturally throughout\n"
        "- Do NOT include the <h1> title tag — just the body content starting from intro paragraphs\n"
        "- Output only raw HTML, no markdown, no explanation"
    )

    print("[CLAUDE] Generating post...")
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        system=system_prompt,
    )

    content = msg.content[0].text.strip()
    print(f"[CLAUDE] Generated {len(content)} characters")
    return content


# ══════════════════════════════════════════════════════
# 4. IMAGE FETCH
# ══════════════════════════════════════════════════════
def fetch_pexels_image(keyword: str) -> dict | None:
    """Pexels에서 관련 이미지 URL 가져오기"""
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params  = {"query": keyword + " Korea", "per_page": 10, "orientation": "landscape"}
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            params["query"] = keyword
            r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            photos = r.json().get("photos", [])
        if photos:
            photo = random.choice(photos[:5])
            return {
                "url": photo["src"]["large2x"],
                "photographer": photo["photographer"],
                "alt": photo.get("alt", keyword),
            }
    except Exception as e:
        print(f"[PEXELS] Error: {e}")
    return None


def build_featured_image_html(image: dict, keyword: str) -> str:
    if not image:
        return ""
    return (
        '<div style="text-align:center;margin:20px 0;">'
        '<img src="' + image["url"] + '" alt="' + image["alt"] + '" '
        'style="max-width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);">'
        '<p style="font-size:12px;color:#888;margin-top:6px;">Photo by ' + image["photographer"] + ' / Pexels</p>'
        '</div>'
    )


# ══════════════════════════════════════════════════════
# 5. BLOGGER OAuth TOKEN
# ══════════════════════════════════════════════════════
def get_access_token() -> str:
    creds = Credentials(
        token=None,
        refresh_token=BLOGGER_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=BLOGGER_CLIENT_ID,
        client_secret=BLOGGER_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    creds.refresh(GoogleRequest())
    print("[OAUTH] Access token obtained via google-auth")
    return creds.token


# ══════════════════════════════════════════════════════
# 6. PUBLISH TO BLOGGER
# ══════════════════════════════════════════════════════
def publish_to_blogger(title: str, body_html: str, label: str, token: str) -> dict:
    url = "https://www.googleapis.com/blogger/v3/blogs/" + BLOG_ID + "/posts/"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type":  "application/json",
    }
    payload = {
        "title":  title,
        "content": body_html,
        "labels": [label, "Korea", "Auto-Published"],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    result = r.json()
    print("[BLOGGER] Published: " + result.get("url", ""))
    return result


# ══════════════════════════════════════════════════════
# 7. SEARCH CONSOLE INDEXING
# ══════════════════════════════════════════════════════
def request_indexing(post_url: str):
    if not SEARCH_CONSOLE_KEY:
        print("[INDEX] No Search Console key — skipping")
        return
    try:
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        headers  = {
            "Authorization": "Bearer " + SEARCH_CONSOLE_KEY,
            "Content-Type":  "application/json",
        }
        payload = {"url": post_url, "type": "URL_UPDATED"}
        r = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        print("[INDEX] Status: " + str(r.status_code))
    except Exception as e:
        print("[INDEX] Error: " + str(e))


# ══════════════════════════════════════════════════════
# 8. TELEGRAM NOTIFICATION
# ══════════════════════════════════════════════════════
def send_telegram(msg: str):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print("[TELEGRAM] Error: " + str(e))


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
def main():
    print("\n" + "="*50)
    print("Korean Blog Auto-Publisher — " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*50)

    # 1. 트렌드 키워드
    keywords = get_trending_keywords()

    # 2. 전략 설계
    strategy = build_content_strategy(keywords)
    print("[STRATEGY] Title: " + strategy["title"])

    # 3. 이미지
    image = fetch_pexels_image(strategy["primary_keyword"])

    # 4. AI 글 생성
    body_content = generate_post(strategy)

    # 5. 이미지 + 본문 조합
    featured_html = build_featured_image_html(image, strategy["primary_keyword"])
    full_body = featured_html + "\n" + body_content

    # 6. Blogger 발행
    token  = get_access_token()
    result = publish_to_blogger(strategy["title"], full_body, strategy["label"], token)
    post_url = result.get("url", BLOG_SITE_URL)

    # 7. Search Console 인덱싱
    time.sleep(3)
    request_indexing(post_url)

    # 8. Telegram 알림
    msg = (
        "✅ <b>New Post Published!</b>\n\n"
        "📝 " + strategy["title"] + "\n"
        "🏷 " + strategy["label"] + "\n"
        "🔑 " + strategy["primary_keyword"] + "\n"
        "🔗 " + post_url + "\n\n"
        "📅 " + datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    )
    send_telegram(msg)
    print("\n[DONE] All steps complete!")


if __name__ == "__main__":
    main()
