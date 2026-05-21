import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
# --- UPDATED: Use the modern SDK package ---
import google.generativeai as genai
from google.genai import types

load_dotenv()

# --- UPDATED: Modern client initialization ---
client = genai.Client()


def fetch_news(symbol, company_name=None):
    """Fetch recent news for a stock"""
    try:
        clean_symbol = symbol.replace(".NS", "")
        query = company_name or clean_symbol

        # Use GNews API (free tier)
        url = f"https://gnews.io/api/v4/search"
        params = {
            "q": f"{query} stock India",
            "lang": "en",
            "country": "in",
            "max": 5,
            "apikey": os.getenv("GNEWS_API_KEY", "")
        }

        news_items = []

        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    news_items.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "published": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name")
                    })
        except:
            pass

        # Fallback — use Gemini to generate recent context
        if not news_items:
            news_items = get_ai_news_context(clean_symbol)

        return news_items

    except Exception as e:
        return []


def get_ai_news_context(symbol):
    """Use Gemini to provide market context when no news API available"""
    try:
        # --- UPDATED: Use proper modern client generation call ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""What is the recent market sentiment and key factors for {symbol} stock in Indian markets?
            Provide 3-4 key points about:
            1. Recent business developments
            2. Sector trends affecting this stock
            3. Any known concerns or positives
            Keep each point to one sentence. Format as JSON list with keys: title, description""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        import json
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        items = json.loads(text)
        return items if isinstance(items, list) else []
    except:
        return []


def analyze_sentiment(symbol, news_items):
    """Use Gemini to analyze sentiment of news"""
    try:
        if not news_items:
            return {
                "sentiment": "NEUTRAL",
                "score": 50,
                "summary": "No recent news available",
                "trading_implication": "No structural news context. Follow core technical rules.",
                "key_positives": [],
                "key_negatives": [],
                "key_points": []
            }

        news_text = "\n".join([
            f"- {item.get('title', '')}: {item.get('description', '')}"
            for item in news_items
        ])

        prompt = f"""Analyze the sentiment of these news items for {symbol} stock:

{news_text}

Respond in JSON format:
{{
    "sentiment": "BULLISH" or "BEARISH" or "NEUTRAL",
    "score": 0-100 (0=very bearish, 50=neutral, 100=very bullish),
    "summary": "2 sentence summary",
    "key_positives": ["point1", "point2"],
    "key_negatives": ["point1", "point2"],
    "trading_implication": "one sentence on what this means for trading"
}}"""

        # --- UPDATED: Modern structural client parameters ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        result = json.loads(text)
        return result

    except Exception as e:
        return {
            "sentiment": "NEUTRAL",
            "score": 50,
            "summary": "Could not analyze sentiment",
            "key_positives": [],
            "key_negatives": [],
            "trading_implication": "No data available"
        }


def get_full_sentiment(symbol):
    """Complete sentiment analysis pipeline"""
    news = fetch_news(symbol)
    sentiment = analyze_sentiment(symbol, news)
    return {
        "symbol": symbol.replace(".NS", ""),
        "news_count": len(news),
        "news": news,
        "sentiment": sentiment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    result = get_full_sentiment("RELIANCE.NS")
    print(f"\nSymbol: {result['symbol']}")
    print(f"Sentiment: {result['sentiment']['sentiment']}")
    print(f"Score: {result['sentiment']['score']}/100")
    print(f"Summary: {result['sentiment']['summary']}")
    print(f"Trading: {result['sentiment']['trading_implication']}")