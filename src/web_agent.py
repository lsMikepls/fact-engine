import os
from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def lookup_web_data(query):
    """
    Input: A question (str)
    Output: A summary answer from the web (str)
    """
    print(f"Searching the web for: '{query}'...")
    
    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        
        context = "\n".join([r['content'] for r in response['results']])

        return context
        
    except Exception as e:
        print(f"Web Search failed for query {query} : {e}")
        return None

# --- TEST ---
if __name__ == "__main__":
    print("--- Test 1 (Private Company) ---")
    print(lookup_web_data("What is OpenAI's estimated revenue?"))
    
    print("\n--- Test 2 (News) ---")
    print(lookup_web_data("Why is Tesla stock moving today?"))
