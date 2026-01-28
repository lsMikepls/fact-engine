import yfinance as yf

def lookup_financial_data(ticker, data_type):
    """
    Input: Ticker (str), data_type (str: 'price' or 'revenue')
    Output: The exact number or None.
    """
    stock = yf.Ticker(ticker)
    
    try:
        if data_type == "price":
            return round(stock.fast_info['last_price'], 2)
            
        elif data_type == "revenue":
            raw_rev = stock.financials.loc['Total Revenue'].iloc[0]
            
            revenue_in_billions = round(raw_rev / 1_000_000_000, 2)
            return f"{revenue_in_billions} Billion"
            
    except Exception as e:
        # If the ticker is private (e.g., OpenAI) or data is missing
        print(f"Error fetching {data_type} for {ticker}: {e}")
        return None

if __name__ == "__main__":
    # --- TEST ---
    print("Checking Google Price:", lookup_financial_data("GOOGL", "price"))
    print("Checking Tesla Revenue:", lookup_financial_data("TSLA", "revenue"))
    print("Checking OpenAI (Should Fail):", lookup_financial_data("OPENAI", "price"))