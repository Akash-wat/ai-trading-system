import pandas as pd
import numpy as np


def find_order_blocks(data, lookback=20):
    """Find institutional order blocks — last bearish candle before big bullish move"""
    order_blocks = []
    closes = data['Close'].values
    opens = data['Open'].values
    highs = data['High'].values
    lows = data['Low'].values
    volumes = data['Volume'].values

    for i in range(2, len(data) - 3):
        # Bullish order block — bearish candle followed by strong bullish move
        if opens[i] > closes[i]:  # bearish candle
            next_move = (closes[i+2] - closes[i+1]) / closes[i+1] * 100
            if next_move > 1.0:  # strong move up after
                order_blocks.append({
                    "type": "BULLISH_OB",
                    "index": i,
                    "top": opens[i],
                    "bottom": closes[i],
                    "volume": volumes[i],
                    "strength": next_move
                })

        # Bearish order block — bullish candle followed by strong bearish move
        if closes[i] > opens[i]:  # bullish candle
            next_move = (closes[i+1] - closes[i+2]) / closes[i+1] * 100
            if next_move > 1.0:
                order_blocks.append({
                    "type": "BEARISH_OB",
                    "index": i,
                    "top": closes[i],
                    "bottom": opens[i],
                    "volume": volumes[i],
                    "strength": next_move
                })

    return order_blocks[-5:] if order_blocks else []


def find_fair_value_gaps(data, lookback=30):
    """Find Fair Value Gaps — imbalance zones price tends to fill"""
    fvgs = []
    highs = data['High'].values
    lows = data['Low'].values
    closes = data['Close'].values

    for i in range(1, len(data) - 1):
        # Bullish FVG — gap between candle 1 high and candle 3 low
        if lows[i+1] > highs[i-1]:
            fvgs.append({
                "type": "BULLISH_FVG",
                "index": i,
                "top": lows[i+1],
                "bottom": highs[i-1],
                "midpoint": (lows[i+1] + highs[i-1]) / 2,
                "size_pct": (lows[i+1] - highs[i-1]) / highs[i-1] * 100
            })

        # Bearish FVG
        if highs[i+1] < lows[i-1]:
            fvgs.append({
                "type": "BEARISH_FVG",
                "index": i,
                "top": lows[i-1],
                "bottom": highs[i+1],
                "midpoint": (lows[i-1] + highs[i+1]) / 2,
                "size_pct": (lows[i-1] - highs[i+1]) / lows[i-1] * 100
            })

    return fvgs[-5:] if fvgs else []


def detect_break_of_structure(data, lookback=20):
    """Detect Break of Structure — trend change signal"""
    closes = data['Close'].values
    highs = data['High'].values
    lows = data['Low'].values

    recent_high = max(highs[-lookback:-1])
    recent_low = min(lows[-lookback:-1])
    current_price = closes[-1]
    prev_price = closes[-2]

    bos = {
        "bullish_bos": False,
        "bearish_bos": False,
        "recent_high": round(float(recent_high), 2),
        "recent_low": round(float(recent_low), 2),
        "current_price": round(float(current_price), 2)
    }

    if current_price > recent_high and prev_price <= recent_high:
        bos["bullish_bos"] = True
        bos["bos_level"] = round(float(recent_high), 2)

    if current_price < recent_low and prev_price >= recent_low:
        bos["bearish_bos"] = True
        bos["bos_level"] = round(float(recent_low), 2)

    return bos


def detect_liquidity_sweep(data, lookback=10):
    """Detect liquidity sweeps — stop hunts before reversal"""
    highs = data['High'].values
    lows = data['Low'].values
    closes = data['Close'].values
    volumes = data['Volume'].values

    avg_volume = np.mean(volumes[-lookback:])
    recent_low = min(lows[-lookback:-1])
    recent_high = max(highs[-lookback:-1])

    sweep = {
        "bullish_sweep": False,
        "bearish_sweep": False,
    }

    # Bullish sweep — price briefly goes below recent low then closes above
    if lows[-1] < recent_low and closes[-1] > recent_low:
        if volumes[-1] > avg_volume * 1.5:
            sweep["bullish_sweep"] = True
            sweep["sweep_level"] = round(float(recent_low), 2)
            sweep["recovery"] = round(float(closes[-1] - lows[-1]), 2)

    # Bearish sweep
    if highs[-1] > recent_high and closes[-1] < recent_high:
        if volumes[-1] > avg_volume * 1.5:
            sweep["bearish_sweep"] = True
            sweep["sweep_level"] = round(float(recent_high), 2)

    return sweep


def detect_premium_discount(data, lookback=50):
    """Detect if price is in premium or discount zone"""
    highs = data['High'].values
    lows = data['Low'].values
    closes = data['Close'].values

    range_high = max(highs[-lookback:])
    range_low = min(lows[-lookback:])
    current = closes[-1]

    if range_high == range_low:
        return {"zone": "NEUTRAL", "position_pct": 50}

    position = (current - range_low) / (range_high - range_low) * 100

    if position < 30:
        zone = "DISCOUNT"
    elif position > 70:
        zone = "PREMIUM"
    else:
        zone = "EQUILIBRIUM"

    return {
        "zone": zone,
        "position_pct": round(float(position), 1),
        "range_high": round(float(range_high), 2),
        "range_low": round(float(range_low), 2),
    }


def get_smc_analysis(data):
    """Complete SMC analysis for a stock"""
    try:
        if data is None or len(data) < 30:
            return None

        order_blocks = find_order_blocks(data)
        fvgs = find_fair_value_gaps(data)
        bos = detect_break_of_structure(data)
        sweep = detect_liquidity_sweep(data)
        pd_zone = detect_premium_discount(data)

        current_price = float(data['Close'].iloc[-1])

        # Check if price is near any order block
        near_bullish_ob = False
        ob_level = None
        for ob in order_blocks:
            if ob["type"] == "BULLISH_OB":
                if ob["bottom"] <= current_price <= ob["top"] * 1.02:
                    near_bullish_ob = True
                    ob_level = ob["top"]

        # Check if price is near any FVG
        near_fvg = False
        fvg_level = None
        for fvg in fvgs:
            if fvg["type"] == "BULLISH_FVG":
                if fvg["bottom"] <= current_price <= fvg["top"]:
                    near_fvg = True
                    fvg_level = fvg["midpoint"]

        # SMC Signal
        smc_bullish = (
            (near_bullish_ob or near_fvg or sweep["bullish_sweep"]) and
            pd_zone["zone"] == "DISCOUNT" and
            not bos["bearish_bos"]
        )

        smc_score = 0
        smc_reasons = []

        if near_bullish_ob:
            smc_score += 30
            smc_reasons.append("Price at institutional Order Block — high probability buy zone")
        if near_fvg:
            smc_score += 25
            smc_reasons.append("Price filling Fair Value Gap — institutional imbalance zone")
        if sweep["bullish_sweep"]:
            smc_score += 30
            smc_reasons.append("Liquidity sweep detected — stop hunt complete, reversal likely")
        if bos["bullish_bos"]:
            smc_score += 25
            smc_reasons.append("Break of Structure confirmed — trend change to bullish")
        if pd_zone["zone"] == "DISCOUNT":
            smc_score += 15
            smc_reasons.append(f"Price in discount zone ({pd_zone['position_pct']}%) — smart money buying area")

        return {
            "smc_bullish": smc_bullish,
            "smc_score": min(smc_score, 100),
            "smc_reasons": smc_reasons,
            "order_blocks": len(order_blocks),
            "fair_value_gaps": len(fvgs),
            "break_of_structure": bos,
            "liquidity_sweep": sweep,
            "premium_discount": pd_zone,
            "near_order_block": near_bullish_ob,
            "near_fvg": near_fvg,
        }

    except Exception as e:
        return {"error": str(e), "smc_score": 0, "smc_bullish": False, "smc_reasons": []}


if __name__ == "__main__":
    import yfinance as yf
    ticker = yf.Ticker("RELIANCE.NS")
    data = ticker.history(period="3mo", interval="1d")
    result = get_smc_analysis(data)
    print(f"\nSMC Analysis:")
    print(f"Bullish Signal: {result['smc_bullish']}")
    print(f"SMC Score: {result['smc_score']}")
    print(f"Zone: {result['premium_discount']['zone']}")
    print(f"\nReasons:")
    for r in result['smc_reasons']:
        print(f"  → {r}")