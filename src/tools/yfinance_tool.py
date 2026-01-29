import os
import yfinance as yf
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _map_attribute_to_yfinance_key(attribute_text):
    system_prompt = """
    You are a financial attribute mapper. Map user text to these exact keys:

    ### PRIORITY RULES (Follow in Order):
    1. ⚠️ **TIME CHECK**: Does the user mention a specific year (e.g., "2021", "2023"), a month ("March"), or words like "last year", "history", "past"? 
       -> If YES, and they want price, YOU MUST RETURN "historical_price".
       -> If YES, and they want revenue/income, YOU MUST RETURN "total_revenue" or "net_income".
    
    2. **TOPIC CHECK**: If no specific past time is mentioned, MATCH THE TEXT TO THE LIST BELOW AND LOOK AT SYNONYMS.
       (e.g., "profitable" -> "net_income", "debt" -> "financial_health")

    [
      "price",          (Synonyms: "stock", "stock price", "current price", "value", "trading")
      "historical_price", (Synonyms: "price in 2022", "value last year", "price history")
      "market_cap",     (Current Only. Synonyms: "valuation", "market value", "cap")
      "pe_ratio",       (Current Only. Synonyms: "p/e", "price to earnings")
      "dividend_yield", (Current Only. Synonyms: "dividend", "yield", "payout")
      "volume",         (Current Only. Synonyms: "trading volume", "shares traded")
      "high_low",       (Current Only. Synonyms: "52 week high", "52 week low", "range")
      "company_info",   (Synonyms: "sector", "industry", "what do they do", "profile", "employees")
      "financial_health", (Synonyms: "cash", "debt", "balance sheet", "safe", "liabilities")
      "analyst_rating",   (Synonyms: "buy or sell", "rating", "recommendation", "target price")
      "total_revenue",  (Current AND Historical. Synonyms: "sales", "revenue", "income", "how much money do they make")
      "net_income",     (Current AND Historical. Synonyms: "profit", "earnings", "net profit", "net income", "profitable", "losing money")
      "future_estimates", (Synonyms: "forecast", "projected revenue", "future growth", "estimates", "next year")
      "unknown"
    ]
    RETURN ONLY THE KEY NAME.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": attribute_text}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()

def _format_series(series, label):
    """Helper to turn a pandas series into a readable string."""
    try:
        series = series.sort_index(ascending=False)
        parts = []
        for date, val in series.items():
            parts.append(f"{date.strftime('%Y-%m-%d')}: ${round(val/1e9, 2)}B")
        return f"{label}: [{', '.join(parts)}]"
    except Exception:
        return ""

def fetch_yfinance_data(ticker, attribute):
    metric_key = _map_attribute_to_yfinance_key(attribute)
    
    if metric_key == "unknown":
        return None

    stock = yf.Ticker(ticker)
    
    try:
        _ = stock.fast_info['last_price']
    except Exception:
        print(f"[yfinance Tool] Error: Ticker '{ticker}' not found or delisted.")
        return None

    try:
        info = stock.fast_info
        metadata = stock.info 

        if metric_key == "price":
            return f"${round(info['last_price'], 2)} (Current)"
            
        elif metric_key == "market_cap":
            return f"${round(info['market_cap'] / 1e9, 2)} Billion (Current)"
        
        elif metric_key == "volume":
            vol = "{:,}".format(int(info['last_volume']))
            avg_vol = "{:,}".format(int(metadata.get('averageVolume10days', 0)))
            return f"Volume: {vol} shares (Avg: {avg_vol})"

        # --- METADATA (Ratios & Info) ---
        elif metric_key == "pe_ratio":
            return f"Trailing P/E: {metadata.get('trailingPE', 'N/A')} | Forward P/E: {metadata.get('forwardPE', 'N/A')}"
            
        elif metric_key == "dividend_yield":
            yield_val = metadata.get('dividendYield', 'N/A')
            if yield_val != 'N/A':
                yield_val = f"{round(yield_val * 100, 2)}%"
            return f"Dividend Yield: {yield_val} (Payout Ratio: {round(metadata.get('payoutRatio', 0)*100, 2)}%)"
            
        elif metric_key == "high_low":
            return f"52-Week High: ${metadata.get('fiftyTwoWeekHigh')} | Low: ${metadata.get('fiftyTwoWeekLow')}"
            
        elif metric_key == "company_info":
            return f"Sector: {metadata.get('sector')} | Industry: {metadata.get('industry')} | Employees: {metadata.get('fullTimeEmployees')}"

        elif metric_key == "financial_health":
            total_cash = metadata.get('totalCash', 0)
            total_debt = metadata.get('totalDebt', 0)
            cash_per_share = metadata.get('totalCashPerShare', 0)
            return f"Total Cash: ${round(total_cash/1e9, 2)}B | Total Debt: ${round(total_debt/1e9, 2)}B | Cash per Share: ${cash_per_share}"

        elif metric_key == "analyst_rating":
            recommendation = metadata.get('recommendationKey', 'none').upper()
            target_price = metadata.get('targetMeanPrice', 'N/A')
            num_analysts = metadata.get('numberOfAnalystOpinions', 'N/A')
            return f"Consensus: {recommendation} | Target Price: ${target_price} | Analysts: {num_analysts}"

        # --- HISTORICAL DATA ---
        elif metric_key == "historical_price":
            hist = stock.history(period="5y")
            annual_close = hist['Close'].resample('YE').last().sort_index(ascending=False)
            
            parts = [f"Year-End {date.year}: ${round(price, 2)}" for date, price in annual_close.items()]
            return f"Price History: [{', '.join(parts)}]"

        elif metric_key == "total_revenue":
            annual = stock.financials.loc['Total Revenue']
            quarterly = stock.quarterly_financials.loc['Total Revenue']
            return f"{_format_series(annual, 'Annual Revenue')} | {_format_series(quarterly, 'Quarterly Revenue')}"

        elif metric_key == "net_income":
            annual = stock.financials.loc['Net Income']
            quarterly = stock.quarterly_financials.loc['Net Income']
            return f"{_format_series(annual, 'Annual Net Income')} | {_format_series(quarterly, 'Quarterly Net Income')}"
        # --- PROJECTED DATA ---
        elif metric_key == "future_estimates":
            rev_growth = metadata.get('revenueGrowth', 'N/A')
            earn_growth = metadata.get('earningsGrowth', 'N/A')
            target_price = metadata.get('targetMeanPrice', 'N/A')
            return f"Revenue Growth (YoY): {rev_growth} | Earnings Growth: {earn_growth} | Target Price: ${target_price}"

    except Exception as e:
        print(f"      [yfinance Tool] Error processing {metric_key}: {e}")
        return None
    
    return None

if __name__ == "__main__":

    print("\n--- 🧪 TEST SUITE: YFINANCE TOOL ---")
    
    # 1. THE FIX TEST (Historical Price)
    print("\n--- 1. Historical Price (The Fix) ---")
    print(fetch_yfinance_data("GOOGL", "What is 2022 stock price?"))

    # 2. FINANCIAL HEALTH (New)
    print("\n--- 2. Financial Health (Cash vs Debt) ---")
    print(fetch_yfinance_data("TSLA", "How much cash do they have?"))

    # 3. ANALYST RATINGS (New)
    print("\n--- 3. Analyst Ratings ---")
    print(fetch_yfinance_data("NVDA", "What is the target price?"))

    # 4. COMPANY INFO (New)
    print("\n--- 4. Company Profile ---")
    print(fetch_yfinance_data("AAPL", "What sector is this stock in?"))

    # 5. TRADING INFO (New)
    print("\n--- 5. Trading Info (Volume/Range) ---")
    print(fetch_yfinance_data("AMD", "What is the 52 week high?"))

    # 6. STANDARD METRICS (Regression Test)
    print("\n--- 6. Standard Metrics (Price/Cap) ---")
    print(fetch_yfinance_data("MSFT", "current price"))
    print(fetch_yfinance_data("MSFT", "market cap"))

    # 7. ERROR HANDLING
    print("\n--- 7. Error Handling (Should be None) ---")
    print(fetch_yfinance_data("FAKE_TICKER_123", "price"))


    print("\n--- 🧪 TEST SUITE: ATTRIBUTE MAPPING ---")
    
    # 1. PRICE (Current)
    print("\n--- CATEGORY: PRICE (Current) ---")
    print(f"1. 'What is the stock price?':  {_map_attribute_to_yfinance_key('What is the stock price?')}")
    print(f"2. 'How much is it trading for?': {_map_attribute_to_yfinance_key('How much is it trading for?')}")
    print(f"3. 'Current value of the stock':  {_map_attribute_to_yfinance_key('Current value of the stock')}")

    # 2. HISTORICAL PRICE
    print("\n--- CATEGORY: HISTORICAL PRICE ---")
    print(f"1. 'Price in 2022':             {_map_attribute_to_yfinance_key('Price in 2022')}")
    print(f"2. 'What was the stock worth last year?': {_map_attribute_to_yfinance_key('What was the stock worth last year?')}")
    print(f"3. 'Show me the price history':   {_map_attribute_to_yfinance_key('Show me the price history')}")

    # 3. VALUATION & RATIOS
    print("\n--- CATEGORY: VALUATION (Cap, P/E) ---")
    print(f"1. 'What is the market cap?':     {_map_attribute_to_yfinance_key('What is the market cap?')}")
    print(f"2. 'How much is the company worth?': {_map_attribute_to_yfinance_key('How much is the company worth?')}")
    print(f"3. 'What is the P/E ratio?':      {_map_attribute_to_yfinance_key('What is the P/E ratio?')}")
    print(f"4. 'Is it expensive relative to earnings?': {_map_attribute_to_yfinance_key('Is it expensive relative to earnings?')}")

    # 4. FINANCIALS (Revenue, Income)
    print("\n--- CATEGORY: FINANCIALS (Revenue, Profit) ---")
    print(f"1. 'How much sales do they have?': {_map_attribute_to_yfinance_key('How much sales do they have?')}")
    print(f"2. 'Total revenue for the last 4 years': {_map_attribute_to_yfinance_key('Total revenue for the last 4 years')}")
    print(f"3. 'Are they profitable?':        {_map_attribute_to_yfinance_key('Are they profitable?')}")
    print(f"4. 'What is the net income?':     {_map_attribute_to_yfinance_key('What is the net income?')}")

    # 5. HEALTH & DIVIDENDS
    print("\n--- CATEGORY: HEALTH & DIVIDENDS ---")
    print(f"1. 'Do they pay a dividend?':     {_map_attribute_to_yfinance_key('Do they pay a dividend?')}")
    print(f"2. 'What is the yield?':          {_map_attribute_to_yfinance_key('What is the yield?')}")
    print(f"3. 'How much cash do they have?': {_map_attribute_to_yfinance_key('How much cash do they have?')}")
    print(f"4. 'Do they have a lot of debt?': {_map_attribute_to_yfinance_key('Do they have a lot of debt?')}")

    # 6. TRADING INFO (Volume, High/Low)
    print("\n--- CATEGORY: TRADING INFO ---")
    print(f"1. 'What is the volume today?':   {_map_attribute_to_yfinance_key('What is the volume today?')}")
    print(f"2. 'Is it near the 52 week high?':{_map_attribute_to_yfinance_key('Is it near the 52 week high?')}")
    print(f"3. 'What is the trading range?':  {_map_attribute_to_yfinance_key('What is the trading range?')}")

    # 7. COMPANY PROFILE & RATINGS
    print("\n--- CATEGORY: PROFILE & RATINGS ---")
    print(f"1. 'What does this company do?':  {_map_attribute_to_yfinance_key('What does this company do?')}")
    print(f"2. 'Which sector are they in?':   {_map_attribute_to_yfinance_key('Which sector are they in?')}")
    print(f"3. 'Is it a buy or sell?':        {_map_attribute_to_yfinance_key('Is it a buy or sell?')}")
    print(f"4. 'What do analysts think?':     {_map_attribute_to_yfinance_key('What do analysts think?')}")

    # 8. NEGATIVE TESTS (Should be 'unknown')
    print("\n--- CATEGORY: UNKNOWN (Should Fail) ---")
    print(f"1. 'Who is the CEO?':             {_map_attribute_to_yfinance_key('Who is the CEO?')}")
    print(f"2. 'Latest news about them':      {_map_attribute_to_yfinance_key('Latest news about them')}")
    print(f"3. 'Who are their competitors?':  {_map_attribute_to_yfinance_key('Who are their competitors?')}")