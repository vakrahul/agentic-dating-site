import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
print(f"Testing Gemini API Key: {key[:8]}...{key[-4:] if key else 'NONE'}", flush=True)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = data.get("models", [])
        print(f"\nTotal models accessible: {len(models)}", flush=True)
        content_models = []
        for m in models:
            name = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            display = m.get("displayName", "")
            if "generateContent" in methods:
                content_models.append(name)
                print(f"  * {name:<35} | {display}", flush=True)

        print(f"\n--- Testing Top Flash / Pro Models ---", flush=True)
        priority_models = [m for m in content_models if any(k in m for k in ["flash", "pro", "gemini-2"])]
        for m_name in priority_models[:8]:
            test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={key}"
            payload = json.dumps({"contents": [{"parts": [{"text": "Reply with 'OK'"}]}]}).encode("utf-8")
            test_req = urllib.request.Request(test_url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(test_req, timeout=6) as t_resp:
                    t_data = json.loads(t_resp.read().decode("utf-8"))
                    text = t_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    print(f"  [AVAILABLE & WORKING] {m_name:<30} -> {text}", flush=True)
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", "")[:90]
                    code = err_json.get("error", {}).get("code", he.code)
                    print(f"  [{code}]                {m_name:<30} -> {msg}", flush=True)
                except Exception:
                    print(f"  [{he.code}]                {m_name:<30} -> {he.reason}", flush=True)
            except Exception as ex:
                print(f"  [ERROR]                {m_name:<30} -> {ex}", flush=True)

except urllib.error.HTTPError as he:
    print(f"HTTPError {he.code}: {he.read().decode('utf-8', errors='replace')}", flush=True)
except Exception as e:
    print(f"Error querying API: {e}", flush=True)
