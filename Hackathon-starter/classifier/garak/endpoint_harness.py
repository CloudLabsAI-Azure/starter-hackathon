import json
        import sys
        import requests

        CLASSIFY_URL = "http://localhost:8000/api/v1/classify"


        def classify_via_endpoint(prompt: str) -> str:
            try:
                resp = requests.post(
                    CLASSIFY_URL,
                    json={"description": prompt, "amount": 0.00},
                    timeout=30,
                )
                if resp.status_code == 200:
                    return json.dumps(resp.json())
                if resp.status_code == 400:
                    return f"[BLOCKED] {resp.json().get('detail', 'Request blocked by guardrails')}"
                return f"[ERROR] HTTP {resp.status_code}"
            except requests.exceptions.ConnectionError:
                print("ERROR: FastAPI app not running. Start with: uvicorn classifier.main:app --port 8000")
                sys.exit(1)


        if __name__ == "__main__":
            prompt = sys.stdin.read().strip()
            print(classify_via_endpoint(prompt))