from master_agent import master_agent
from full_market_watchlist import get_tiered_watchlists

if __name__ == '__main__':
    tiers = get_tiered_watchlists()
    print('Tiers:')
    for tier in tiers:
        print(f" - {tier['name']}: {len(tier['symbols'])} symbols, interval {tier['interval_minutes']}m")

    result = master_agent.start_full_scan()
    print('SCAN RESULT:', result)
    print('TOP SIGNALS COUNT:', len(master_agent.get_top_signals()))
    print('TOP SIGNALS:', master_agent.get_top_signals())
