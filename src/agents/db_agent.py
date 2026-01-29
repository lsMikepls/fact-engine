from src.tools.yfinance_tool import fetch_yfinance_data

# ==============================================================================
# THE REGISTRY
# Register all your provider functions here.
# ==============================================================================
DATA_PROVIDERS = [
    fetch_yfinance_data,
    # fetch_bloomberg_data,  <-- Easy to add later
]

def lookup_financial_data(ticker, attribute):
    """
    Main Entry Point.
    Iterates through all connected providers to find the data.
    """
    print(f"    DB Agent: Looking up '{attribute}' for {ticker}...")
    
    for provider in DATA_PROVIDERS:
        result = provider(ticker, attribute)
        
        if result:
            print(f"  Found via {provider.__name__}")
            return result
            
    print("    Data not found in any connected DB provider.")
    return None


if __name__ == "__main__":
    print("\n--- TEST SUITE: DB AGENT ---")

    print("\n3223233. Testing Price:")
    print(lookup_financial_data("GOOGL", "Projected Revenue Next Year"))

    
    
    # # Test 1: Simple Price (The "Hello World" of finance)
    # print("\n1. Testing Price:")
    # print(lookup_financial_data("TSLA", "What is the current price?"))

    # # Test 2: Complex History (The "Time Machine")
    # print("\n2. Testing History:")
    # print(lookup_financial_data("AAPL", "What was the price in 2022?"))

    # # Test 3: Financial Health (The "Deep Dive")
    # print("\n3. Testing Health:")
    # print(lookup_financial_data("NVDA", "How much cash do they have?"))

    # # Test 4: Ambiguous/Synonym (The "Smart Mapping")
    # print("\n4. Testing Synonyms (Profitability):")
    # print(lookup_financial_data("GOOGL", "Are they profitable?"))
    
    # # Test 5: Bad Ticker (The "Safety Check")
    # print("\n5. Testing Error Handling:")
    # print(lookup_financial_data("FAKE_CO", "price"))