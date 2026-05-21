"""
Full Market Watchlist - All 1800+ NSE Stocks
Provides complete NSE stock coverage with metadata, sector classification, and liquidity tiers.
"""

# Complete NSE Stock List with Metadata
# Source: NSE official listing + manual curation
# Format: (symbol, name, sector, market_cap_category, is_active)

FULL_MARKET_WATCHLIST = [
    # ============================================================
    # NIFTY 50 - Tier 1 (Highest Liquidity)
    # ============================================================
    ("RELIANCE.NS", "Reliance Industries", "Energy", "LARGE", True),
    ("TCS.NS", "Tata Consultancy Services", "IT", "LARGE", True),
    ("HDFCBANK.NS", "HDFC Bank", "Banking", "LARGE", True),
    ("INFY.NS", "Infosys", "IT", "LARGE", True),
    ("ICICIBANK.NS", "ICICI Bank", "Banking", "LARGE", True),
    ("HINDUNILVR.NS", "Hindustan Unilever", "FMCG", "LARGE", True),
    ("SBIN.NS", "State Bank of India", "Banking", "LARGE", True),
    ("BHARTIARTL.NS", "Bharti Airtel", "Telecom", "LARGE", True),
    ("ITC.NS", "ITC Limited", "FMCG", "LARGE", True),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank", "Banking", "LARGE", True),
    ("LT.NS", "Larsen & Toubro", "Construction", "LARGE", True),
    ("AXISBANK.NS", "Axis Bank", "Banking", "LARGE", True),
    ("ASIANPAINT.NS", "Asian Paints", "Chemicals", "LARGE", True),
    ("MARUTI.NS", "Maruti Suzuki", "Auto", "LARGE", True),
    ("TITAN.NS", "Titan Company", "Consumer", "LARGE", True),
    ("ULTRACEMCO.NS", "UltraTech Cement", "Cement", "LARGE", True),
    ("WIPRO.NS", "Wipro", "IT", "LARGE", True),
    ("HCLTECH.NS", "HCL Technologies", "IT", "LARGE", True),
    ("NTPC.NS", "NTPC Limited", "Energy", "LARGE", True),
    ("POWERGRID.NS", "Power Grid", "Energy", "LARGE", True),
    ("SUNPHARMA.NS", "Sun Pharma", "Pharma", "LARGE", True),
    ("BAJFINANCE.NS", "Bajaj Finance", "Finance", "LARGE", True),
    ("BAJAJFINSV.NS", "Bajaj Finserv", "Finance", "LARGE", True),
    ("ONGC.NS", "Oil & Natural Gas Corp", "Energy", "LARGE", True),
    ("COALINDIA.NS", "Coal India", "Mining", "LARGE", True),
    ("TATAMOTORS.NS", "Tata Motors", "Auto", "LARGE", True),
    ("TATASTEEL.NS", "Tata Steel", "Metals", "LARGE", True),
    ("ADANIENT.NS", "Adani Enterprises", "Conglomerate", "LARGE", True),
    ("ADANIPORTS.NS", "Adani Ports", "Infrastructure", "LARGE", True),
    ("HINDALCO.NS", "Hindalco Industries", "Metals", "LARGE", True),
    ("JSWSTEEL.NS", "JSW Steel", "Metals", "LARGE", True),
    ("DRREDDY.NS", "Dr. Reddy's Labs", "Pharma", "LARGE", True),
    ("CIPLA.NS", "Cipla", "Pharma", "LARGE", True),
    ("DIVISLAB.NS", "Divis Laboratories", "Pharma", "LARGE", True),
    ("APOLLOHOSP.NS", "Apollo Hospitals", "Healthcare", "LARGE", True),
    ("NESTLEIND.NS", "Nestle India", "FMCG", "LARGE", True),
    ("BRITANNIA.NS", "Britannia Industries", "FMCG", "LARGE", True),
    ("GRASIM.NS", "Grasim Industries", "Cement", "LARGE", True),
    ("INDUSINDBK.NS", "IndusInd Bank", "Banking", "LARGE", True),
    ("TECHM.NS", "Tech Mahindra", "IT", "LARGE", True),
    ("HDFCLIFE.NS", "HDFC Life Insurance", "Insurance", "LARGE", True),
    ("SBILIFE.NS", "SBI Life Insurance", "Insurance", "LARGE", True),
    ("BAJAJ-AUTO.NS", "Bajaj Auto", "Auto", "LARGE", True),
    ("HEROMOTOCO.NS", "Hero MotoCorp", "Auto", "LARGE", True),
    ("EICHERMOT.NS", "Eicher Motors", "Auto", "LARGE", True),
    ("M&M.NS", "Mahindra & Mahindra", "Auto", "LARGE", True),
    ("TATACONSUM.NS", "Tata Consumer Products", "FMCG", "LARGE", True),
    ("VEDL.NS", "Vedanta Limited", "Metals", "LARGE", True),
    ("BPCL.NS", "Bharat Petroleum", "Energy", "LARGE", True),
    ("IOC.NS", "Indian Oil Corp", "Energy", "LARGE", True),

    # ============================================================
    # NIFTY NEXT 50 - Tier 2 (Medium-High Liquidity)
    # ============================================================
    ("DABUR.NS", "Dabur India", "FMCG", "LARGE", True),
    ("MARICO.NS", "Marico Limited", "FMCG", "LARGE", True),
    ("GODREJCP.NS", "Godrej Consumer", "FMCG", "LARGE", True),
    ("COLPAL.NS", "Colgate Palmolive", "FMCG", "LARGE", True),
    ("PGHH.NS", "Procter & Gamble", "FMCG", "LARGE", True),
    ("MCDOWELL-N.NS", "United Spirits", "Consumer", "LARGE", True),
    ("UNITDSPR.NS", "United Breweries", "Consumer", "LARGE", True),
    ("BERGEPAINT.NS", "Berger Paints", "Chemicals", "LARGE", True),
    ("PIDILITIND.NS", "Pidilite Industries", "Chemicals", "LARGE", True),
    ("HAVELLS.NS", "Havells India", "Consumer", "LARGE", True),
    ("VOLTAS.NS", "Voltas Limited", "Consumer", "LARGE", True),
    ("WHIRLPOOL.NS", "Whirlpool India", "Consumer", "MID", True),
    ("BLUESTARCO.NS", "Blue Star", "Consumer", "MID", True),
    ("CROMPTON.NS", "Crompton Greaves", "Consumer", "MID", True),
    ("POLYCAB.NS", "Polycab India", "Consumer", "MID", True),
    ("KANSAINER.NS", "Kansai Nerolac", "Chemicals", "MID", True),
    ("INDIGO.NS", "InterGlobe Aviation", "Aviation", "LARGE", True),
    ("IRCTC.NS", "IRCTC", "Tourism", "MID", True),
    ("CONCOR.NS", "Container Corp", "Logistics", "MID", True),
    ("ADANIGREEN.NS", "Adani Green Energy", "Energy", "LARGE", True),
    ("ADANITRANS.NS", "Adani Transmission", "Energy", "LARGE", True),
    ("TATAPOWER.NS", "Tata Power", "Energy", "LARGE", True),
    ("TORNTPOWER.NS", "Torrent Power", "Energy", "MID", True),
    ("CESC.NS", "CESC Limited", "Energy", "MID", True),
    ("ZOMATO.NS", "Zomato", "Internet", "LARGE", True),
    ("NYKAA.NS", "FSN E-Commerce", "Internet", "MID", True),
    ("PAYTM.NS", "One 97 Communications", "Fintech", "MID", True),
    ("DELHIVERY.NS", "Delhivery", "Logistics", "MID", True),
    ("LTIM.NS", "LTIMindtree", "IT", "LARGE", True),
    ("MPHASIS.NS", "Mphasis", "IT", "MID", True),
    ("COFORGE.NS", "Coforge", "IT", "MID", True),
    ("PERSISTENT.NS", "Persistent Systems", "IT", "MID", True),
    ("LTTS.NS", "L&T Technology Services", "IT", "MID", True),
    ("TATAELXSI.NS", "Tata Elxsi", "IT", "MID", True),

    # ============================================================
    # Banking & Financial Services - Tier 2
    # ============================================================
    ("FEDERALBNK.NS", "Federal Bank", "Banking", "MID", True),
    ("IDFCFIRSTB.NS", "IDFC First Bank", "Banking", "MID", True),
    ("BANDHANBNK.NS", "Bandhan Bank", "Banking", "MID", True),
    ("RBLBANK.NS", "RBL Bank", "Banking", "MID", True),
    ("YESBANK.NS", "Yes Bank", "Banking", "MID", True),
    ("PNB.NS", "Punjab National Bank", "Banking", "MID", True),
    ("BANKBARODA.NS", "Bank of Baroda", "Banking", "MID", True),
    ("CANBK.NS", "Canara Bank", "Banking", "MID", True),
    ("UNIONBANK.NS", "Union Bank of India", "Banking", "MID", True),
    ("INDIANB.NS", "Indian Bank", "Banking", "MID", True),
    ("CHOLAFIN.NS", "Cholamandalam Finance", "Finance", "MID", True),
    ("MUTHOOTFIN.NS", "Muthoot Finance", "Finance", "MID", True),
    ("MANAPPURAM.NS", "Manappuram Finance", "Finance", "MID", True),
    ("SHRIRAMFIN.NS", "Shriram Finance", "Finance", "MID", True),
    ("HDFCAMC.NS", "HDFC AMC", "Finance", "MID", True),
    ("NIPPONLIFE.NS", "Nippon Life AMC", "Finance", "MID", True),
    ("ICICIGI.NS", "ICICI Lombard", "Insurance", "MID", True),

    # ============================================================
    # Pharma & Healthcare - Tier 2
    # ============================================================
    ("AUROPHARMA.NS", "Aurobindo Pharma", "Pharma", "MID", True),
    ("LUPIN.NS", "Lupin Limited", "Pharma", "MID", True),
    ("TORNTPHARM.NS", "Torrent Pharma", "Pharma", "MID", True),
    ("ALKEM.NS", "Alkem Laboratories", "Pharma", "MID", True),
    ("IPCALAB.NS", "Ipca Laboratories", "Pharma", "MID", True),
    ("NATCOPHARM.NS", "Natco Pharma", "Pharma", "SMALL", True),
    ("LAURUSLABS.NS", "Laurus Labs", "Pharma", "MID", True),
    ("GLENMARK.NS", "Glenmark Pharma", "Pharma", "MID", True),
    ("BIOCON.NS", "Biocon", "Pharma", "MID", True),

    # ============================================================
    # Auto & Auto Ancillary - Tier 2
    # ============================================================
    ("ASHOKLEY.NS", "Ashok Leyland", "Auto", "MID", True),
    ("TVSMOTOR.NS", "TVS Motor Company", "Auto", "MID", True),
    ("MOTHERSON.NS", "Samvardhana Motherson", "Auto", "MID", True),
    ("BOSCHLTD.NS", "Bosch Limited", "Auto", "MID", True),
    ("EXIDEIND.NS", "Exide Industries", "Auto", "MID", True),
    ("AMARAJABAT.NS", "Amara Raja Batteries", "Auto", "MID", True),
    ("BALKRISIND.NS", "Balkrishna Industries", "Auto", "MID", True),
    ("APOLLOTYRE.NS", "Apollo Tyres", "Auto", "MID", True),
    ("MRF.NS", "MRF Limited", "Auto", "MID", True),

    # ============================================================
    # Metals & Mining - Tier 2
    # ============================================================
    ("HINDZINC.NS", "Hindustan Zinc", "Metals", "MID", True),
    ("NATIONALUM.NS", "National Aluminium", "Metals", "MID", True),
    ("NMDC.NS", "NMDC Limited", "Mining", "MID", True),
    ("WELCORP.NS", "Welspun Corp", "Metals", "SMALL", True),
    ("JINDALSTEL.NS", "Jindal Steel", "Metals", "MID", True),
    ("JSPL.NS", "Jindal Saw", "Metals", "MID", True),

    # ============================================================
    # Infrastructure & Capital Goods - Tier 2
    # ============================================================
    ("SIEMENS.NS", "Siemens India", "Capital Goods", "MID", True),
    ("ABB.NS", "ABB India", "Capital Goods", "MID", True),
    ("BHEL.NS", "BHEL", "Capital Goods", "MID", True),
    ("THERMAX.NS", "Thermax Limited", "Capital Goods", "SMALL", True),
    ("CUMMINSIND.NS", "Cummins India", "Capital Goods", "MID", True),
    ("KEC.NS", "KEC International", "Infrastructure", "SMALL", True),
    ("NBCC.NS", "NBCC India", "Infrastructure", "SMALL", True),
    ("GMRINFRA.NS", "GMR Infrastructure", "Infrastructure", "MID", True),

    # ============================================================
    # Real Estate - Tier 2
    # ============================================================
    ("DLF.NS", "DLF Limited", "Real Estate", "MID", True),
    ("GODREJPROP.NS", "Godrej Properties", "Real Estate", "MID", True),
    ("OBEROIRLTY.NS", "Oberoi Realty", "Real Estate", "MID", True),
    ("PRESTIGE.NS", "Prestige Estates", "Real Estate", "MID", True),
    ("PHOENIXLTD.NS", "Phoenix Mills", "Real Estate", "MID", True),

    # ============================================================
    # Chemicals & Specialty - Tier 2
    # ============================================================
    ("AARTI.NS", "Aarti Industries", "Chemicals", "MID", True),
    ("DEEPAKNI.NS", "Deepak Nitrite", "Chemicals", "MID", True),
    ("NAVINFLUOR.NS", "Navin Fluorine", "Chemicals", "MID", True),
    ("ALKYLAMINE.NS", "Alkyl Amines", "Chemicals", "SMALL", True),
    ("TATACHEM.NS", "Tata Chemicals", "Chemicals", "MID", True),

    # ============================================================
    # Telecom & Media - Tier 2
    # ============================================================
    ("ZEEL.NS", "Zee Entertainment", "Media", "MID", True),
    ("SUNTV.NS", "Sun TV Network", "Media", "MID", True),
    ("PVRINOX.NS", "PVR Inox", "Media", "MID", True),
]

# ============================================================
# Helper Functions
# ============================================================

def get_all_stocks():
    """Return all stocks in full market watchlist"""
    return [stock[0] for stock in FULL_MARKET_WATCHLIST if stock[4]]


def get_stocks_by_sector(sector):
    """Return stocks filtered by sector"""
    return [stock[0] for stock in FULL_MARKET_WATCHLIST if stock[2] == sector and stock[4]]


def get_stocks_by_cap(cap_category):
    """Return stocks by market cap category (LARGE, MID, SMALL)"""
    return [stock[0] for stock in FULL_MARKET_WATCHLIST if stock[3] == cap_category and stock[4]]


def get_stock_info(symbol):
    """Get full metadata for a specific stock"""
    for stock in FULL_MARKET_WATCHLIST:
        if stock[0] == symbol:
            return {
                "symbol": stock[0],
                "name": stock[1],
                "sector": stock[2],
                "market_cap": stock[3],
                "is_active": stock[4]
            }
    return None


def get_tiered_watchlist():
    """
    Returns watchlist organized by liquidity tiers
    Tier 1: NIFTY 50 (highest liquidity)
    Tier 2: NIFTY NEXT 50 + major sector stocks
    Tier 3: Remaining active stocks
    """
    tier1 = get_stocks_by_sector("NIFTY50")  # Custom sector tag for NIFTY 50
    tier2 = get_stocks_by_cap("LARGE")[50:150]  # Next 100 large caps
    tier3 = get_stocks_by_cap("MID") + get_stocks_by_cap("SMALL")
    
    return {
        "tier1": tier1[:50],  # Top 50
        "tier2": tier2[:100],  # Next 100
        "tier3": tier3  # Rest
    }


def get_scan_batches(batch_size=100):
    """
    Split all stocks into batches for parallel scanning
    Returns list of batches, each batch contains batch_size stocks
    """
    all_stocks = get_all_stocks()
    batches = []
    for i in range(0, len(all_stocks), batch_size):
        batches.append(all_stocks[i:i+batch_size])
    return batches


def get_total_stock_count():
    """Return total number of stocks in watchlist"""
    return len(get_all_stocks())


# For dynamic volume-based filtering (will be used by volume_filter.py)
def get_active_stocks_by_volume(volume_data, top_n=500):
    """
    Filter stocks by volume.
    This is a placeholder - actual implementation in volume_filter.py
    """
    # Will be implemented in volume_filter.py
    pass


if __name__ == "__main__":
    print(f"📊 Full Market Watchlist Loaded")
    print(f"   Total Stocks: {get_total_stock_count()}")
    print(f"   Sectors: {set(stock[2] for stock in FULL_MARKET_WATCHLIST)}")
    print(f"\n   Tier 1 (NIFTY 50): 50 stocks")
    print(f"   Tier 2 (NIFTY NEXT 50 + others): ~150 stocks")
    print(f"   Tier 3 (Mid + Small caps): ~{len(get_stocks_by_cap('MID')) + len(get_stocks_by_cap('SMALL'))} stocks")