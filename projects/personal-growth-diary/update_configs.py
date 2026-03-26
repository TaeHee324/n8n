import json, requests

N8N_KEY = "YOUR_N8N_API_KEY"
BASE = "https://primary-production-90c7.up.railway.app"
H = {"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}

SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_SECRET_KEY"
BOT_TOKEN    = "YOUR_BOT_TOKEN"

WF_IDS = {
    "wf01": "iEnGnRd4vX4jV2Hb",
    "wf02": "1SVTgznT7a0BwJQT",
    "wf03": "dxrvKgcG95vGBzZS",
}

def get_wf(wf_id):
    r = requests.get(f"{BASE}/api/v1/workflows/{wf_id}", headers=H)
    return r.json()

def put_wf(wf_id, wf_data):
    # Remove read-only fields
    for field in ["id", "createdAt", "updatedAt", "active", "isArchived", "versionId"]:
        wf_data.pop(field, None)
    r = requests.put(f"{BASE}/api/v1/workflows/{wf_id}", headers=H, json=wf_data)
    if r.status_code == 200:
        print(f"  Updated OK: {r.json()['name']}")
    else:
        print(f"  FAIL ({r.status_code}): {r.text[:200]}")
    return r

def update_set_node(nodes, node_name, updates: dict):
    """Set 노드의 assignments 값을 업데이트"""
    for node in nodes:
        if node["name"] == node_name:
            assignments = node["parameters"]["assignments"]["assignments"]
            for a in assignments:
                if a["name"] in updates:
                    a["value"] = updates[a["name"]]
            return True
    return False

def update_node_param(nodes, node_name, param_path, value):
    """노드의 특정 파라미터를 업데이트 (점 표기법 경로)"""
    for node in nodes:
        if node["name"] == node_name:
            parts = param_path.split(".")
            obj = node["parameters"]
            for p in parts[:-1]:
                obj = obj[p]
            obj[parts[-1]] = value
            return True
    return False

# ──────────────────────────────
# WF-01 업데이트
# ──────────────────────────────
print("Updating WF-01 Telegram Bot...")
wf01 = get_wf(WF_IDS["wf01"])
update_set_node(wf01["nodes"], "Set Config", {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "BOT_TOKEN":    BOT_TOKEN,
})
put_wf(WF_IDS["wf01"], wf01)

# ──────────────────────────────
# WF-02 업데이트 (Chat ID는 WF-01 활성화 후 확인 필요)
# ──────────────────────────────
print("Updating WF-02 Daily Quote...")
wf02 = get_wf(WF_IDS["wf02"])
# Send Quote 노드의 chatId는 나중에 업데이트 (사용자 chat ID 확인 후)
put_wf(WF_IDS["wf02"], wf02)

# ──────────────────────────────
# WF-03 업데이트
# ──────────────────────────────
print("Updating WF-03 Calendar Optimizer...")
wf03 = get_wf(WF_IDS["wf03"])
update_set_node(wf03["nodes"], "Set Config", {
    "SUPABASE_URL":      SUPABASE_URL,
    "SUPABASE_KEY":      SUPABASE_KEY,
    "TELEGRAM_CHAT_ID":  "PENDING_USER_CHAT_ID",
})
put_wf(WF_IDS["wf03"], wf03)

print("\nDone.")
