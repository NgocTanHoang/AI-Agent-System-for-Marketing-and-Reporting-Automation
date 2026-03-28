import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

def test_llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Missing OPENROUTER_API_KEY")
        return

    print(f"Testing with: openrouter/meta-llama/llama-3.3-70b-instruct")
    try:
        llm = LLM(
            model="openrouter/meta-llama/llama-3.3-70b-instruct",
            api_key=api_key
        )
        response = llm.call(messages=[{"role": "user", "content": "Say hello"}])
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_llm()
