import pandas as pd
import numpy as np


def get_indicators(data):
    """Calculate all indicators needed for strategies"""
    df = data.copy()

    # EMAs
    df['ema9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    df['rsi'] = 100 - (100 / (1 + gain.rolling(14).mean() / loss.rolling(14).mean()))

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_mid'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * bb_std
    df['bb_lower'] = df['bb_mid'] - 2 * bb_std
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']

    # VWAP
    df['vwap'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    # ATR
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift()).abs(),
        (df['Low'] - df['Close'].shift()).abs()
    ], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    # ADX
    plus_dm = df['High'].diff()
    minus_dm = -df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    atr14 = tr.rolling(14).mean()
    df['plus_di'] = 100 * (plus_dm.rolling(14).mean() / atr14)
    df['minus_di'] = 100 * (minus_dm.rolling(14).mean() / atr14)
    dx = 100 * ((df['plus_di'] - df['minus_di']).abs() / (df['plus_di'] + df['minus_di']))
    df['adx'] = dx.rolling(14).mean()

    # Volume average
    df['vol_avg'] = df['Volume'].rolling(20).mean()
    df['vol_ratio'] = df['Volume'] / df['vol_avg']

    # Stochastic
    low14 = df['Low'].rolling(14).min()
    high14 = df['High'].rolling(14).max()
    df['stoch_k'] = 100 * (df['Close'] - low14) / (high14 - low14)
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # OBV
    df['obv'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()

    # Supertrend
    hl2 = (df['High'] + df['Low']) / 2
    df['st_upper'] = hl2 + 3 * df['atr']
    df['st_lower'] = hl2 - 3 * df['atr']
    supertrend = [0] * len(df)
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['st_upper'].iloc[i-1]:
            supertrend[i] = 1
        elif df['Close'].iloc[i] < df['st_lower'].iloc[i-1]:
            supertrend[i] = -1
        else:
            supertrend[i] = supertrend[i-1]
    df['supertrend'] = supertrend
       
    return df


def run_strategy(df, entry_col, exit_col):
    """Generic strategy runner — returns trades list"""
    trades = []
    in_trade = False
    buy_price = 0
    buy_idx = 0

    for i in range(1, len(df)):
        try:
            entry = df[entry_col].iloc[i]
            exit_sig = df[exit_col].iloc[i]

            if entry and not in_trade and not pd.isna(entry):
                in_trade = True
                buy_price = float(df['Close'].iloc[i])
                buy_idx = i

            elif exit_sig and in_trade and not pd.isna(exit_sig):
                in_trade = False
                sell_price = float(df['Close'].iloc[i])
                pnl_pct = (sell_price - buy_price) / buy_price * 100
                hold_days = i - buy_idx
                trades.append({
                    "pnl_pct": pnl_pct,
                    "hold_days": hold_days,
                    "buy_price": buy_price,
                    "sell_price": sell_price
                })
        except:
            continue

    return trades


def calculate_metrics(trades, symbol, strategy_name):
    """Calculate performance metrics from trades"""
    if not trades or len(trades) < 3:
        return None

    pnls = np.array([t["pnl_pct"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    win_rate = len(wins) / len(pnls) * 100
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
    avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    expectancy = (win_rate/100 * avg_win) + ((1-win_rate/100) * avg_loss)
    avg_hold = float(np.mean([t["hold_days"] for t in trades]))

    # Sharpe
    daily_pnls = pd.Series(pnls)
    sharpe = float(daily_pnls.mean() / daily_pnls.std() * np.sqrt(252/avg_hold)) if daily_pnls.std() != 0 else 0

    # Max drawdown
    cumulative = (1 + daily_pnls/100).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min() * 100)

    # Score
    score = 0
    if win_rate > 60: score += 35
    elif win_rate > 50: score += 25
    elif win_rate > 40: score += 10

    if sharpe > 1.5: score += 25
    elif sharpe > 1.0: score += 18
    elif sharpe > 0.5: score += 10

    if profit_factor > 2: score += 25
    elif profit_factor > 1.5: score += 18
    elif profit_factor > 1: score += 10

    if max_drawdown > -15: score += 15
    elif max_drawdown > -25: score += 8

    return {
        "symbol": symbol.replace(".NS", ""),
        "strategy": strategy_name,
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "avg_hold_days": round(avg_hold, 1),
        "score": score,
        "is_active": score >= 40
    }


# ============================================================
# ALL 20 STRATEGIES
# ============================================================

def strategy_triple_ema(data, symbol):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (df['ema9'] > df['ema21']) &
            (df['ema21'] > df['ema50']) &
            (df['rsi'] > 50) & (df['rsi'] < 70) &
            (df['vol_ratio'] > 1.5) &
            (df['macd'] > df['macd_signal'])
        )
        df['exit'] = (df['ema9'] < df['ema21']) | (df['rsi'] > 75)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Triple EMA Confirmation")
    except: return None


def strategy_breakout_volume(data, symbol):
    try:
        df = get_indicators(data)
        df['20d_high'] = df['High'].rolling(20).max().shift(1)
        df['entry'] = (
            (df['Close'] > df['20d_high']) &
            (df['vol_ratio'] > 2.5) &
            (df['rsi'] < 70) &
            (df['adx'] > 20)
        )
        df['exit'] = (df['Close'] < df['ema21']) | (df['rsi'] > 80)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Breakout with Volume")
    except: return None


def strategy_52w_high_breakout(data, symbol):
    try:
        df = get_indicators(data)
        df['52w_high'] = df['High'].rolling(252).max().shift(1)
        df['entry'] = (
            (df['Close'] > df['52w_high'] * 0.98) &
            (df['vol_ratio'] > 2) &
            (df['rsi'] > 55) &
            (df['macd'] > df['macd_signal'])
        )
        df['exit'] = (df['rsi'] > 80) | (df['Close'] < df['ema50'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "52 Week High Breakout")
    except: return None


def strategy_relative_strength(data, symbol):
    try:
        import yfinance as yf
        nifty = yf.Ticker("^NSEI").history(period="1y", interval="1d")
        df = get_indicators(data)
        nifty_returns = nifty['Close'].pct_change(20)
        stock_returns = df['Close'].pct_change(20)
        df['rs'] = stock_returns.values[:len(df)] / nifty_returns.values[:len(nifty_returns)]
        df['entry'] = (
            (df['rs'] > 1.1) &
            (df['Close'] > df['ema50']) &
            (df['vol_ratio'] > 1.2)
        )
        df['exit'] = (df['rs'] < 0.9) | (df['Close'] < df['ema50'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Relative Strength Momentum")
    except: return None


def strategy_rsi_divergence(data, symbol):
    try:
        df = get_indicators(data)
        df['price_lower_low'] = (df['Close'] < df['Close'].shift(5)) & (df['Close'].shift(5) < df['Close'].shift(10))
        df['rsi_higher_low'] = (df['rsi'] > df['rsi'].shift(5)) & (df['rsi'].shift(5) > df['rsi'].shift(10))
        df['entry'] = (
            df['price_lower_low'] &
            df['rsi_higher_low'] &
            (df['rsi'] < 40) &
            (df['vol_ratio'] > 1.2)
        )
        df['exit'] = (df['rsi'] > 65) | (df['Close'] > df['bb_upper'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "RSI Divergence")
    except: return None


def strategy_vwap_reversal(data, symbol):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (df['Close'] < df['vwap']) &
            (df['rsi'] < 40) &
            (df['vol_ratio'] > 1.5) &
            (df['Close'] > df['ema50'])
        )
        df['exit'] = (df['Close'] > df['vwap'] * 1.02) | (df['rsi'] > 65)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "VWAP Reversal")
    except: return None


def strategy_bb_squeeze(data, symbol):
    try:
        df = get_indicators(data)
        df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(20).min().shift(1) * 1.1
        df['entry'] = (
            df['bb_squeeze'].shift(1) &
            (df['Close'] > df['bb_upper']) &
            (df['vol_ratio'] > 2) &
            (df['adx'] > 15)
        )
        df['exit'] = (df['Close'] < df['bb_mid']) | (df['rsi'] > 80)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Bollinger Squeeze Breakout")
    except: return None


def strategy_double_bottom(data, symbol):
    try:
        df = get_indicators(data)
        df['local_low'] = df['Low'].rolling(5, center=True).min()
        df['is_low'] = df['Low'] == df['local_low']
        df['entry'] = False
        closes = df['Close'].values
        lows = df['Low'].values
        rsi_vals = df['rsi'].values
        entries = [False] * len(df)
        for i in range(15, len(df)):
            prev_lows = [j for j in range(i-15, i-3) if df['is_low'].iloc[j]]
            if len(prev_lows) >= 1:
                prev_low_price = lows[prev_lows[-1]]
                curr_low = lows[i]
                if abs(curr_low - prev_low_price) / prev_low_price < 0.02:
                    if rsi_vals[i] > rsi_vals[prev_lows[-1]] and rsi_vals[i] < 40:
                        entries[i] = True
        df['entry'] = entries
        df['exit'] = (df['rsi'] > 65) | (df['Close'] > df['bb_upper'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Double Bottom Pattern")
    except: return None


def strategy_hammer_reversal(data, symbol):
    try:
        df = get_indicators(data)
        body = abs(df['Close'] - df['Open'])
        lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
        upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['hammer'] = (lower_wick > 2 * body) & (upper_wick < body) & (df['Close'] > df['Open'])
        df['entry'] = (
            df['hammer'] &
            (df['rsi'] < 40) &
            (df['vol_ratio'] > 1.3)
        )
        df['exit'] = (df['rsi'] > 65) | (df['Close'] < df['Low'].shift(1))
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Hammer Reversal")
    except: return None


def strategy_smart_money_accumulation(data, symbol):
    try:
        df = get_indicators(data)
        df['price_flat'] = df['Close'].rolling(10).std() / df['Close'].rolling(10).mean() < 0.02
        df['vol_increasing'] = df['vol_ratio'] > df['vol_ratio'].shift(5)
        df['obv_rising'] = df['obv'] > df['obv'].shift(5)
        df['entry'] = (
            df['price_flat'] &
            df['vol_increasing'] &
            df['obv_rising'] &
            (df['rsi'] > 40) & (df['rsi'] < 60)
        )
        df['exit'] = (df['vol_ratio'] > 3) | (df['rsi'] > 70)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Smart Money Accumulation")
    except: return None


def strategy_stop_hunt_reversal(data, symbol):
    try:
        df = get_indicators(data)
        df['recent_low'] = df['Low'].rolling(10).min().shift(1)
        df['sweep'] = (df['Low'] < df['recent_low']) & (df['Close'] > df['recent_low'])
        df['entry'] = (
            df['sweep'] &
            (df['vol_ratio'] > 1.5) &
            (df['rsi'] < 45)
        )
        df['exit'] = (df['rsi'] > 65) | (df['Close'] < df['Low'].shift(1) * 0.99)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Stop Hunt Reversal")
    except: return None


def strategy_ichimoku_breakout(data, symbol):
    try:
        df = get_indicators(data)
        high9 = df['High'].rolling(9).max()
        low9 = df['Low'].rolling(9).min()
        high26 = df['High'].rolling(26).max()
        low26 = df['Low'].rolling(26).min()
        df['tenkan'] = (high9 + low9) / 2
        df['kijun'] = (high26 + low26) / 2
        df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
        high52 = df['High'].rolling(52).max()
        low52 = df['Low'].rolling(52).min()
        df['senkou_b'] = ((high52 + low52) / 2).shift(26)
        df['above_cloud'] = (df['Close'] > df['senkou_a']) & (df['Close'] > df['senkou_b'])
        df['entry'] = (
            df['above_cloud'] &
            (df['tenkan'] > df['kijun']) &
            (df['vol_ratio'] > 1.2)
        )
        df['exit'] = (df['Close'] < df['kijun']) | (df['rsi'] > 75)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Ichimoku Cloud Breakout")
    except: return None


def strategy_adx_trend(data, symbol):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (df['adx'] > 25) &
            (df['plus_di'] > df['minus_di']) &
            (df['Close'] > df['ema50']) &
            (df['vol_ratio'] > 1.2)
        )
        df['exit'] = (df['adx'] < 20) | (df['plus_di'] < df['minus_di'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "ADX Trend Strength")
    except: return None


def strategy_macd_histogram(data, symbol):
    try:
        df = get_indicators(data)
        df['hist_turning'] = (df['macd_hist'] > df['macd_hist'].shift(1)) & (df['macd_hist'].shift(1) < df['macd_hist'].shift(2))
        df['entry'] = (
            df['hist_turning'] &
            (df['macd_hist'] < 0) &
            (df['rsi'] < 50) &
            (df['vol_ratio'] > 1.2)
        )
        df['exit'] = (df['macd_hist'] < df['macd_hist'].shift(1)) & (df['macd_hist'] > 0)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "MACD Histogram Reversal")
    except: return None


def strategy_supertrend_multi(data, symbol):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (df['supertrend'] == 1) &
            (df['supertrend'].shift(1) == -1) &
            (df['vol_ratio'] > 1.3) &
            (df['rsi'] < 65)
        )
        df['exit'] = df['supertrend'] == -1
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "SuperTrend Reversal")
    except: return None


def strategy_mean_reversion_uptrend(data, symbol):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (df['Close'] > df['ema200']) &
            (df['Close'] < df['ema21']) &
            (df['rsi'] > 35) & (df['rsi'] < 48) &
            (df['vol_ratio'] < 1.5)
        )
        df['exit'] = (df['Close'] > df['ema9']) | (df['rsi'] > 65)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Mean Reversion in Uptrend")
    except: return None


def strategy_fundamental_momentum(data, symbol, fundamental_score=0):
    try:
        df = get_indicators(data)
        df['entry'] = (
            (fundamental_score >= 60) &
            (df['Close'] > df['ema50']) &
            (df['rsi'] > 50) & (df['rsi'] < 65) &
            (df['vol_ratio'] > 1.3)
        )
        df['exit'] = (df['Close'] < df['ema50']) | (df['rsi'] > 75)
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Fundamental Momentum")
    except: return None


def strategy_order_block_entry(data, symbol):
    try:
        from smc_detector import find_order_blocks
        df = get_indicators(data)
        order_blocks = find_order_blocks(data)
        current_price = float(df['Close'].iloc[-1])
        entries = [False] * len(df)
        for ob in order_blocks:
            if ob['type'] == 'BULLISH_OB':
                idx = ob['index']
                if idx < len(df) and ob['bottom'] <= current_price <= ob['top'] * 1.02:
                    entries[min(idx+1, len(df)-1)] = True
        df['entry'] = entries
        df['exit'] = (df['rsi'] > 70) | (df['Close'] < df['ema21'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Order Block Entry")
    except: return None


def strategy_fvg_fill(data, symbol):
    try:
        from smc_detector import find_fair_value_gaps
        df = get_indicators(data)
        fvgs = find_fair_value_gaps(data)
        current_price = float(df['Close'].iloc[-1])
        entries = [False] * len(df)
        for fvg in fvgs:
            if fvg['type'] == 'BULLISH_FVG':
                idx = fvg['index']
                if idx < len(df) and fvg['bottom'] <= current_price <= fvg['top']:
                    entries[min(idx+2, len(df)-1)] = True
        df['entry'] = entries
        df['exit'] = (df['rsi'] > 68) | (df['Close'] > df['bb_upper'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Fair Value Gap Fill")
    except: return None


def strategy_liquidity_sweep_reversal(data, symbol):
    try:
        df = get_indicators(data)
        df['recent_low'] = df['Low'].rolling(15).min().shift(1)
        df['sweep_reversal'] = (
            (df['Low'] < df['recent_low']) &
            (df['Close'] > df['recent_low']) &
            (df['Close'] > df['Open'])
        )
        df['entry'] = (
            df['sweep_reversal'] &
            (df['vol_ratio'] > 2) &
            (df['rsi'] < 45)
        )
        df['exit'] = (df['rsi'] > 68) | (df['Close'] < df['ema21'])
        return calculate_metrics(run_strategy(df, 'entry', 'exit'), symbol, "Liquidity Sweep Reversal")
    except: return None


# All strategies list
ALL_STRATEGIES = [
    strategy_triple_ema,
    strategy_breakout_volume,
    strategy_52w_high_breakout,
    strategy_rsi_divergence,
    strategy_vwap_reversal,
    strategy_bb_squeeze,
    strategy_double_bottom,
    strategy_hammer_reversal,
    strategy_smart_money_accumulation,
    strategy_stop_hunt_reversal,
    strategy_ichimoku_breakout,
    strategy_adx_trend,
    strategy_macd_histogram,
    strategy_supertrend_multi,
    strategy_mean_reversion_uptrend,
    strategy_fundamental_momentum,
    strategy_order_block_entry,
    strategy_fvg_fill,
    strategy_liquidity_sweep_reversal,
    strategy_relative_strength,
]


if __name__ == "__main__":
    import yfinance as yf
    ticker = yf.Ticker("RELIANCE.NS")
    data = ticker.history(period="1y", interval="1d")
    print(f"\nTesting all strategies on RELIANCE...\n")
    results = []
    for strategy_fn in ALL_STRATEGIES:
        result = strategy_fn(data, "RELIANCE.NS")
        if result:
            results.append(result)
            print(f"{result['strategy']:<35} Win Rate: {result['win_rate']}%  Score: {result['score']}  {'✅' if result['is_active'] else '❌'}")
    print(f"\nBest strategy: {max(results, key=lambda x: x['score'])['strategy']}")