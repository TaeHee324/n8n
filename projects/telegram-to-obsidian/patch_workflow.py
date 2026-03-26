import json
import urllib.request
import urllib.error

N8N_URL = "https://primary-production-90c7.up.railway.app"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzU1NmRiZi1jNmY5LTQ1OTctODBmNy05ODgxMTUyMzFlMjEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiYTllNTc2ODEtNjQ2Zi00MzdmLWE1NDAtMTQ4NTMzNTgzZGJiIiwiaWF0IjoxNzczNzUxNzIwLCJleHAiOjE3NzYzMTIwMDB9.R2kmxDW-Gh5VBYfv6TOTVd4MfWyv41v6v87D6jVCtj0"
WORKFLOW_ID = "a5RvxdkYFp9VLw5A"
BOT_TOKEN = "8690935139:AAGV_Bhildl6AVag91HkAizBtlXJYFTs3bw"

def api_request(method, path, data=None):
    url = f"{N8N_URL}/api/v1{path}"
    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise

# 1. Fetch workflow
print("Fetching workflow...")
wf = api_request("GET", f"/workflows/{WORKFLOW_ID}")

# 2. Replace $vars.BOT_TOKEN in all nodes
replaced = 0
for node in wf.get("nodes", []):
    params = node.get("parameters", {})
    for key, val in list(params.items()):
        if isinstance(val, str) and "$vars.BOT_TOKEN" in val:
            params[key] = val.replace("$vars.BOT_TOKEN", BOT_TOKEN)
            print(f"  [{node['name']}] {key}: replaced")
            replaced += 1

print(f"Total replacements: {replaced}")

# 3. Build PUT payload (only allowed fields)
print(f"Workflow keys: {list(wf.keys())}")
ALLOWED = {"name", "description", "nodes", "connections", "settings", "staticData", "meta", "pinData"}
payload = {k: v for k, v in wf.items() if k in ALLOWED}
print(f"Payload keys: {list(payload.keys())}")

# 4. PUT workflow
print("Updating workflow...")
result = api_request("PUT", f"/workflows/{WORKFLOW_ID}", payload)
print(f"Updated workflow: {result.get('id')} — {result.get('name')}")
print("Done.")
