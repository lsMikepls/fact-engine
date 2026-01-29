import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def decompose_user_query(user_text):
    """
    Role: The Fact Decomposer (Planner)
    Input: Unstructured text (e.g., "Google's revenue is up 5%")
    Output: A list of Atomic Claims (Target, Ticker, Attribute, Value)
    """
    
    # We ask for the 'ticker' specifically to help the DB Agent later.
    extraction_schema = [
        {
            "type": "function",
            "function": {
                "name": "extract_atomic_claims",
                "description": "Breaks complex text into isolated, verifiable atomic claims. Extracts tickers for public companies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "claims": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "target": {
                                        "type": "string", 
                                        "description": "The subject entity (e.g., 'Tesla', 'US GDP')"
                                    },
                                    "ticker": {
                                        "type": "string",
                                        "description": "The stock ticker if public (e.g. 'TSLA'). Set to null if private."
                                    },
                                    "attribute": {
                                        "type": "string", 
                                        "description": "The specific property being claimed (e.g., 'Q3 Revenue', 'CEO', 'Stock Price')"
                                    },
                                    "claimed_value": {
                                        "type": "string", 
                                        "description": "The value stated in the text (e.g., '+5%', 'Elon Musk', '$150')"
                                    }
                                },
                                "required": ["target", "ticker", "attribute", "claimed_value"]
                            }
                        }
                    },
                    "required": ["claims"]
                }
            }
        }
    ]

    print(f"\n🧠 Planner (Decomposer) is analyzing: '{user_text}'...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are The Fact Decomposer. Isolate verifiable units of information. Always extract the Stock Ticker for public companies so we can check the database."},
            {"role": "user", "content": user_text}
        ],
        tools=extraction_schema,
        tool_choice={"type": "function", "function": {"name": "extract_atomic_claims"}}
    )

    tool_call = response.choices[0].message.tool_calls[0]
    parsed_args = json.loads(tool_call.function.arguments)
    
    return parsed_args['claims']

# --- TEST ---
if __name__ == "__main__":

    # Test 1: A standard public company claim (Should get Ticker: GOOGL)
    text1 = "Google's Q4 revenue for 2025 was $100 Billion and the stock was at $220 in March 2023"
    claims1 = decompose_user_query(text1)

    
    print("\n--- TEST 1: Public Company (Google) ---")
    for i, claim in enumerate(claims1, 1):
        print(f"Claim {i}:")
        print(f"  Target:    {claim['target']}")
        print(f"  Ticker:    {claim['ticker']}  <-- DB Agent Enabled")
        print(f"  Attribute: {claim['attribute']}")
        print(f"  Value:     {claim['claimed_value']}")
        print("-" * 30)

    # Test 2: A private company claim (Should get Ticker: None)
    text2 = "OpenAI is projecting $1 billion in revenue next year."
    claims2 = decompose_user_query(text2)
    
    print("\n--- TEST 2: Private Company (OpenAI) ---")
    for i, claim in enumerate(claims2, 1):
        print(f"Claim {i}:")
        print(f"  Target:    {claim['target']}")
        print(f"  Ticker:    {claim['ticker']}  <-- DB Agent Disabled (only have yfinance API)")
        print(f"  Attribute: {claim['attribute']}")
        print(f"  Value:     {claim['claimed_value']}")
        print("-" * 30)