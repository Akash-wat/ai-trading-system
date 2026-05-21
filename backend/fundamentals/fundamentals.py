import yfinance as yf


def get_fundamentals(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Raw metrics
        pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        ps = info.get("priceToSalesTrailing12Months")

        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        profit_margins = info.get("profitMargins")
        operating_margins = info.get("operatingMargins")
        gross_margins = info.get("grossMargins")

        revenue_growth = info.get("revenueGrowth")
        earnings_growth = info.get("earningsGrowth")
        eps = info.get("trailingEps")
        forward_eps = info.get("forwardEps")

        debt_to_equity = info.get("debtToEquity")
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        interest_coverage = info.get("coverageRatio")
        free_cashflow = info.get("freeCashflow")
        operating_cashflow = info.get("operatingCashflow")

        beta = info.get("beta")
        market_cap = info.get("marketCap")
        week52_high = info.get("fiftyTwoWeekHigh")
        week52_low = info.get("fiftyTwoWeekLow")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        sector = info.get("sector")
        industry = info.get("industry")

        # Institutional holdings
        fii_holding = info.get("heldPercentInstitutions")
        insider_holding = info.get("heldPercentInsiders")

        # --- SCORING SYSTEM (max 150 pts) ---
        score = 0
        reasons = []
        red_flags = []

        # VALUATION (30 pts)
        if pe and pe < 15:
            score += 8
            reasons.append(f"PE {round(pe,1)} is very attractive")
        elif pe and pe < 25:
            score += 5
            reasons.append(f"PE {round(pe,1)} is reasonable")
        elif pe and pe > 40:
            red_flags.append(f"PE {round(pe,1)} is expensive")

        if peg and peg < 1:
            score += 9
            reasons.append(f"PEG {round(peg,2)} — undervalued relative to growth")
        elif peg and peg < 1.5:
            score += 5
            reasons.append(f"PEG {round(peg,2)} is fair")

        if ev_ebitda and ev_ebitda < 10:
            score += 7
            reasons.append(f"EV/EBITDA {round(ev_ebitda,1)} is attractive")
        elif ev_ebitda and ev_ebitda < 15:
            score += 4

        if pb and pb < 3:
            score += 6
            reasons.append(f"Price to Book {round(pb,1)} is reasonable")

        # PROFITABILITY (30 pts)
        if roe and roe > 0.20:
            score += 8
            reasons.append(f"ROE {round(roe*100,1)}% is excellent")
        elif roe and roe > 0.15:
            score += 5
            reasons.append(f"ROE {round(roe*100,1)}% is good")
        elif roe and roe < 0.08:
            red_flags.append(f"ROE {round(roe*100,1)}% is weak")

        if roa and roa > 0.10:
            score += 8
            reasons.append(f"ROA {round(roa*100,1)}% is strong")
        elif roa and roa > 0.05:
            score += 4

        if profit_margins and profit_margins > 0.15:
            score += 7
            reasons.append(f"Profit margin {round(profit_margins*100,1)}% is healthy")
        elif profit_margins and profit_margins > 0.10:
            score += 4
        elif profit_margins and profit_margins < 0.05:
            red_flags.append("Thin profit margins")

        if operating_margins and operating_margins > 0.15:
            score += 7
            reasons.append(f"Operating margin {round(operating_margins*100,1)}% expanding")

        # GROWTH (25 pts)
        if revenue_growth and revenue_growth > 0.20:
            score += 8
            reasons.append(f"Revenue growing {round(revenue_growth*100,1)}% — strong")
        elif revenue_growth and revenue_growth > 0.10:
            score += 5
            reasons.append(f"Revenue growing {round(revenue_growth*100,1)}%")
        elif revenue_growth and revenue_growth < 0:
            red_flags.append("Revenue declining")

        if earnings_growth and earnings_growth > 0.20:
            score += 9
            reasons.append(f"Earnings growing {round(earnings_growth*100,1)}% — excellent")
        elif earnings_growth and earnings_growth > 0.10:
            score += 6
        elif earnings_growth and earnings_growth < 0:
            red_flags.append("Earnings declining")

        if eps and forward_eps and forward_eps > eps:
            score += 8
            reasons.append("Forward EPS higher — growth expected")

        # FINANCIAL HEALTH (25 pts)
        if debt_to_equity is not None:
            if debt_to_equity < 30:
                score += 7
                reasons.append("Very low debt")
            elif debt_to_equity < 100:
                score += 4
                reasons.append("Manageable debt levels")
            elif debt_to_equity > 200:
                red_flags.append(f"High debt to equity {round(debt_to_equity,1)}")
                score -= 10

        if current_ratio and current_ratio > 2:
            score += 6
            reasons.append(f"Current ratio {round(current_ratio,1)} — strong liquidity")
        elif current_ratio and current_ratio > 1.5:
            score += 4
        elif current_ratio and current_ratio < 1:
            red_flags.append("Poor liquidity")
            score -= 5

        if free_cashflow and free_cashflow > 0:
            score += 6
            reasons.append("Positive free cash flow")
        elif free_cashflow and free_cashflow < 0:
            red_flags.append("Negative free cash flow")
            score -= 10

        if operating_cashflow and operating_cashflow > 0:
            score += 6
            reasons.append("Strong operating cash flow")

        # INSTITUTIONAL ACTIVITY (25 pts)
        if fii_holding and fii_holding > 0.20:
            score += 8
            reasons.append(f"FII holding {round(fii_holding*100,1)}% — institutional confidence")
        elif fii_holding and fii_holding > 0.10:
            score += 5

        if insider_holding and insider_holding > 0.50:
            score += 9
            reasons.append(f"Promoter holding {round(insider_holding*100,1)}% — high skin in game")
        elif insider_holding and insider_holding > 0.35:
            score += 6
        elif insider_holding and insider_holding < 0.25:
            red_flags.append("Low promoter holding")

        # 52 WEEK POSITION BONUS
        if current_price and week52_high and week52_low:
            range_pct = ((current_price - week52_low) / (week52_high - week52_low)) * 100 if week52_high != week52_low else 50
            if range_pct > 90:
                score += 10
                reasons.append("Near 52 week high — strong momentum")
            elif range_pct < 20:
                score += 5
                reasons.append("Near 52 week low — potential reversal")
        else:
            range_pct = 50

        # Cap score at 100 for display
        final_score = max(0, min(score, 100))

        return {
            "symbol": symbol.replace(".NS", ""),
            "sector": sector,
            "industry": industry,
            "market_cap": market_cap,
            "current_price": current_price,
            "pe_ratio": round(pe, 2) if pe else None,
            "forward_pe": round(forward_pe, 2) if forward_pe else None,
            "peg_ratio": round(peg, 2) if peg else None,
            "price_to_book": round(pb, 2) if pb else None,
            "ev_ebitda": round(ev_ebitda, 2) if ev_ebitda else None,
            "roe": round(roe * 100, 2) if roe else None,
            "roa": round(roa * 100, 2) if roa else None,
            "profit_margins": round(profit_margins * 100, 2) if profit_margins else None,
            "operating_margins": round(operating_margins * 100, 2) if operating_margins else None,
            "revenue_growth": round(revenue_growth * 100, 2) if revenue_growth else None,
            "earnings_growth": round(earnings_growth * 100, 2) if earnings_growth else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
            "current_ratio": round(current_ratio, 2) if current_ratio else None,
            "free_cashflow": free_cashflow,
            "fii_holding": round(fii_holding * 100, 2) if fii_holding else None,
            "insider_holding": round(insider_holding * 100, 2) if insider_holding else None,
            "week52_high": week52_high,
            "week52_low": week52_low,
            "week52_position_pct": round(range_pct, 1),
            "beta": round(beta, 2) if beta else None,
            "fundamental_score": final_score,
            "fundamental_reasons": reasons,
            "red_flags": red_flags,
            "is_fundamentally_strong": final_score >= 50,
        }

    except Exception as e:
        return {
            "symbol": symbol.replace(".NS", ""),
            "error": str(e),
            "fundamental_score": 0,
            "is_fundamentally_strong": False,
            "red_flags": [],
            "fundamental_reasons": []
        }


if __name__ == "__main__":
    result = get_fundamentals("RELIANCE.NS")
    print(f"\nSymbol: {result['symbol']}")
    print(f"Sector: {result['sector']}")
    print(f"Fundamental Score: {result['fundamental_score']}/100")
    print(f"\nReasons:")
    for r in result['fundamental_reasons']:
        print(f"  ✅ {r}")
    print(f"\nRed Flags:")
    for r in result['red_flags']:
        print(f"  🚩 {r}")