import os
import json
from datetime import datetime
# --- UPDATED: Modern client import statements ---
import google.generativeai as genai
from google.genai import types
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import supabase

load_dotenv()

# --- UPDATED: Instantiating client tool --
client = genai.Client()


def create_trade_journal_entry(trade_data):
    """AI generates a journal entry for a trade"""
    try:
        prompt = f"""You are an expert trading coach analyzing a trade for learning purposes.

Trade Details:
- Symbol: {trade_data.get('symbol')}
- Type: {trade_data.get('trade_type')}
- Buy Price: ₹{trade_data.get('buy_price')}
- Sell Price: ₹{trade_data.get('sell_price', 'Still open')}
- Quantity: {trade_data.get('quantity')}
- P&L: ₹{trade_data.get('pnl', 'Open')} ({trade_data.get('pnl_pct', 0)}%)
- Strategy Used: {trade_data.get('strategy', 'Unknown')}
- Entry Reasons: {trade_data.get('reasons', [])}
- Market Mood at Entry: {trade_data.get('market_mood', 'Unknown')}

Write a trading journal entry in JSON:
{{
    "trade_summary": "2 sentence trade summary",
    "what_went_right": ["point1", "point2"],
    "what_went_wrong": ["point1", "point2"],
    "lessons_learned": ["lesson1", "lesson2"],
    "emotional_assessment": "was this a disciplined trade or emotional?",
    "process_score": 0-10,
    "outcome_score": 0-10,
    "improvement_areas": ["area1", "area2"],
    "next_time": "what to do differently next time"
}}"""

        # --- UPDATED: Execution mapping via current SDK model structures ---
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
        journal = json.loads(text)
        journal["symbol"] = trade_data.get("symbol")
        journal["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save to Supabase
        try:
            supabase.table("trade_journal").insert({
                "symbol": trade_data.get("symbol"),
                "trade_summary": journal.get("trade_summary"),
                "lessons_learned": journal.get("lessons_learned"),
                "process_score": journal.get("process_score"),
                "outcome_score": journal.get("outcome_score"),
                "full_journal": journal,
                "pnl_pct": trade_data.get("pnl_pct", 0)
            }).execute()
        except:
            pass

        return journal

    except Exception as e:
        return {"error": str(e)}


def get_performance_analysis():
    """AI analyzes overall trading performance"""
    try:
        trades = supabase.table("trades").select("*").order("created_at", desc=True).limit(50).execute()
        trade_data = trades.data if trades.data else []

        if not trade_data:
            return {"message": "No trades to analyze yet"}

        closed = [t for t in trade_data if t.get("status") == "CLOSED"]
        if not closed:
            return {"message": "No closed trades to analyze yet"}

        wins = [t for t in closed if (t.get("pnl") or 0) > 0]
        identity_losses = [t for t in closed if (t.get("pnl") or 0) <= 0]
        total_pnl = sum(t.get("pnl") or 0 for t in closed)
        win_rate = len(wins) / len(closed) * 100 if closed else 0

        prompt = f"""You are a trading performance coach analyzing a trader's results.

Performance Stats:
- Total Trades: {len(closed)}
- Win Rate: {round(win_rate, 1)}%
- Total P&L: ₹{round(total_pnl, 2)}
- Winning Trades: {len(wins)}
- Losing Trades: {len(identity_losses)}
- Best Trade: ₹{max([t.get('pnl') or 0 for t in closed])}
- Worst Trade: ₹{min([t.get('pnl') or 0 for t in closed])}

Provide performance analysis in JSON:
{{
    "performance_grade": "A/B/C/D/F",
    "overall_assessment": "2 sentence assessment",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2", "weakness3"],
    "win_rate_analysis": "is win rate good for the strategy used?",
    "risk_management_score": 0-10,
    "consistency_score": 0-10,
    "top_recommendations": ["rec1", "rec2", "rec3"],
    "focus_areas": ["area1", "area2"],
    "projected_improvement": "what improvement is possible with adjustments"
}}"""

        # --- UPDATED: Modern execution pipeline syntax ---
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
        analysis = json.loads(text)
        analysis["stats"] = {
            "total_trades": len(closed),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "wins": len(wins),
            "losses": len(identity_losses)
        }
        return analysis

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test journal entry
    test_trade = {
        "symbol": "RELIANCE",
        "trade_type": "BUY",
        "buy_price": 1347.7,
        "sell_price": 1420.0,
        "quantity": 10,
        "pnl": 723,
        "pnl_pct": 5.4,
        "strategy": "Smart Money Accumulation",
        "reasons": ["RSI oversold", "Order block zone", "Strong fundamentals"],
        "market_mood": "SIDEWAYS"
    }
    journal = create_trade_journal_entry(test_trade)
    print(f"\nTrade Summary: {journal.get('trade_summary')}")
    print(f"Process Score: {journal.get('process_score')}/10")
    print(f"Lessons: {journal.get('lessons_learned')}")