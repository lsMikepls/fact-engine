import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_temporal_context(user_text):

    today_str = datetime.now().strftime("%Y-%m-%d")

    system_prompt = (
        "You are a Temporal Reasoning Engine. "
        f"CRITICAL CONTEXT: Today's date is {today_str}. "
        "All relative dates (like 'last year', 'recent', 'next month') MUST be calculated relative to this date."
    )

    temporal_schema = [
        {
            "type": "function",
            "function": {
                "name": "extract_temporal_logic",
                "description": "Extracts explicit dates, infers implicit eras, and resolves relative time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_anchors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entity_or_concept": {"type": "string"},
                                    "time_type": {
                                        "type": "string",
                                        "enum": ["explicit_date", "implicit_era", "relative_time", "timeless"]
                                    },
                                    "inferred_timeframe": {
                                        "type": "string", 
                                        "description": "The calculated year/date. E.g. If today is 2026 and user says 'last year', return '2025'."
                                    },
                                    "reasoning": {"type": "string"}
                                },
                                "required": ["entity_or_concept", "time_type", "inferred_timeframe"]
                            }
                        },
                        "consistency_check": {
                            "type": "string",
                            "enum": ["Consistent", "Conflict/Anachronism Detected", "Timeless"]
                        },
                        "explanation": {"type": "string"}
                    },
                    "required": ["time_anchors", "consistency_check", "explanation"]
                }
            }
        }
    ]

    print(f"\n⏳ Temporal Agent Analyzing: '{user_text}'...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        tools=temporal_schema,
        tool_choice={"type": "function", "function": {"name": "extract_temporal_logic"}}
    )

    tool_call = response.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)

# --- TEST ---
if __name__ == "__main__":
    
    # 1. Implicit Tech Context
    query1 = "Write a Python script using pandas to analyze the Titanic dataset."
    print(json.dumps(analyze_temporal_context(query1), indent=2))

    # 2. Explicit Date & Context
    query2 = "Who won the Super Bowl in 1996?"
    print(json.dumps(analyze_temporal_context(query2), indent=2))
    
    # 3. Timeless Logic
    query3 = "Solve 2 + 2."
    print(json.dumps(analyze_temporal_context(query3), indent=2))

    # 4. Anachronism / Conflict
    query4 = "Imagine you are a knight in 1500. Use your smartphone to call the king."
    print(json.dumps(analyze_temporal_context(query4), indent=2))

    # 5. Relative Time Test
    query5 = "The company's revenue grew 20% last year."
    print("\n--- Test 5: Relative Time (Context Aware) ---")
    print(json.dumps(analyze_temporal_context(query5), indent=2))