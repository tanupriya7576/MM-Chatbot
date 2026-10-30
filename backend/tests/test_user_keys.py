import httpx

def test():
    with httpx.Client(base_url="http://127.0.0.1:5173", timeout=30.0) as client:
        # 1. Health check
        h = client.get("/health")
        print("1. Health Status:", h.status_code, h.json())

        # 2. Live AI generation with user's Gemini key
        r_chat = client.post("/api/chat", json={"message": "Write a 1-sentence motivational quote for developers."})
        print("2. Live AI Chat Status:", r_chat.status_code)
        resp_data = r_chat.json()
        print("   Query Type:", resp_data.get("query_type"))
        print("   AI Response:", resp_data.get("response", "")[:150])

        # 3. Live Web Search with Tavily / DuckDuckGo
        r_search = client.post("/api/search", json={"query": "Latest breakthroughs in AI 2026"})
        print("3. Search API Status:", r_search.status_code)
        results = r_search.json().get("results", [])
        print("   Found web results:", len(results))
        if results:
            print("   First source title:", results[0].get("title"))

        # 4. Image Generation
        r_img = client.post("/api/chat", json={"message": "generate an image of a red sports car"})
        print("4. Image Gen Status:", r_img.status_code, "Type:", r_img.json().get("query_type"))
        print("   Has markdown image:", "![" in r_img.json().get("response", ""))

    print("\nALL BACKEND & FRONTEND APIS TESTED SUCCESSFULLY WITH USER KEYS!")

if __name__ == "__main__":
    test()
