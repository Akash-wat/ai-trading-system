import os
import json
# --- UPDATED: Modern client import ---
import google.generativeai as genai
from google.genai import types
from dotenv import load_dotenv
from fundamentals.fundamentals import get_fundamentals
from market_context.market_context import get_market_context
from market_regime import detect_market_regime

load_dotenv()

# --- UPDATED: Modern initialization format ---
client = genai.Client()


def research_stock(symbol):
    """Deep AI research on a stock"""
    try:
        clean = symbol.replace(".NS", "")
        fundamentals = get_fundamentals(symbol)
        market = get_market_context()

        prompt = f"""You are a senior equity research analyst at a top Indian investment bank.

Perform deep research on {clean} stock with these known fundamentals:
- Sector: {fundamentals.get('sector')}
- PE Ratio: {fundamentals.get('pe_ratio')}
- ROE: {fundamentals.get('roe')}%
- Revenue Growth: {fundamentals.get('revenue_growth')}%
- Debt/Equity: {fundamentals.get('debt_to_equity')}
- Fundamental Score: {fundamentals.get('fundamental_score')}/100
- Red Flags: {fundamentals.get('red_flags')}
- Market Mood: {market.get('market_mood')}

Provide institutional-grade research in JSON:
{{
    "company_overview": "2 sentence business description",
    "investment_thesis": "why buy or avoid — 3 sentences",
    "key_catalysts": ["catalyst1", "catalyst2", "catalyst3"],
    "key_risks": ["risk1", "risk2", "risk3"],
    "sector_outlook": "sector trend in 2 sentences",
    "competitive_position": "market position vs competitors",
    "target_timeframe": "short/medium/long term",
    "analyst_rating": "STRONG BUY/BUY/HOLD/SELL/STRONG SELL",
    "price_outlook": "bullish/bearish/neutral",
    "institutional_view": "what smart money likely thinks"
}}"""

        # --- UPDATED: Execute modern model generation call ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        research = json.loads(text)
        research["symbol"] = clean
        research["fundamentals"] = fundamentals
        return research

    except Exception as e:
        return {"error": str(e), "symbol": symbol.replace(".NS", "")}


def research_sector(sector_name):
    """Research an entire sector"""
    try:
        market = get_market_context()

        prompt = f"""As a sector analyst, analyze the {sector_name} sector in Indian markets.
Current market mood: {market.get('market_mood')}
NIFTY: {market.get('nifty', {}).get('price')}

Respond in JSON:
{{
    "sector_trend": "BULLISH/BEARISH/NEUTRAL",
    "sector_score": 0-100,
    "key_drivers": ["driver1", "driver2", "driver3"],
    "headwinds": ["risk1", "risk2"],
    "top_picks": ["stock1", "stock2", "stock3"],
    "avoid": ["stock1", "stock2"],
    "outlook_3months": "outlook summary",
    "fii_activity": "what FIIs likely doing in this sector",
    "rotation_signal": "is money flowing in or out"
}}"""

        # --- UPDATED: Modern client mapping framework ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        return json.loads(text)

    except Exception as e:
        return {"error": str(e)}


def autonomous_market_scan():
    """AI autonomously identifies best opportunities in market"""
    try:
        market = get_market_context()
        regime = detect_market_regime()

        prompt = f"""You are an autonomous AI trading analyst scanning Indian markets.

Current conditions:
- Market Mood: {market.get('market_mood')}
- NIFTY: {market.get('nifty', {}).get('price')}
- India VIX: {market.get('india_vix')}
- Market Regime: {regime.get('regime')}
- Active Strategies: {regime.get('active_strategies')}

Identify the best trading opportunities right now.
Respond in JSON:
{{
    "market_summary": "2 sentence overall market view",
    "best_sectors": ["sector1", "sector2", "sector3"],
    "avoid_sectors": ["sector1", "sector2"],
    "opportunity_type": "what kind of trades work best now",
    "risk_level": "LOW/MEDIUM/HIGH",
    "suggested_stocks": [
        {{"symbol": "STOCK1", "reason": "why", "strategy": "which strategy"}},
        {{"symbol": "STOCK2", "reason": "why", "strategy": "which strategy"}},
        {{"symbol": "STOCK3", "reason": "why", "strategy": "which strategy"}}
    ],
    "avoid_stocks": ["STOCK1", "STOCK2"],
    "key_levels": {{"nifty_support": 0, "nifty_resistance": 0}},
    "trading_plan": "what to do today in 3 sentences"
}}"""

        # --- UPDATED: Using proper generation parameters ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        return json.loads(text)

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Running autonomous market scan...")
    result = autonomous_market_scan()
    print(f"\nMarket Summary: {result.get('market_summary')}")
    print(f"Best Sectors: {result.get('best_sectors')}")
    print(f"Trading Plan: {result.get('trading_plan')}")