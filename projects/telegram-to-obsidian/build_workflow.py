import json

TELEGRAM_CRED_ID = "BCqwmNg6iOHm2Dpf"
OPENAI_CRED_ID   = "pt0BOOXg6IRrrCQW"
ONEDRIVE_CRED_ID = "vDMXfiLw3K2FBkrH"

PREPARE_CODE = r"""
const msg = $json.message;
if (!msg) return [{ json: { is_allowed: false, error: 'no message' } }];

const allowedUsers = ($vars && $vars.ALLOWED_USERS) ? $vars.ALLOWED_USERS : '';
const userId = String(msg.from.id);

let isAllowed = true;
if (allowedUsers && allowedUsers.trim() !== '') {
  const list = allowedUsers.split(',').map(u => u.trim());
  isAllowed = list.includes(userId);
}

let msgType = 'text';
let fileId = null;
let fileUniqueId = null;
let fileName = null;
let videoDuration = null;

if (msg.photo && msg.photo.length > 0) {
  msgType = 'photo';
  const best = msg.photo[msg.photo.length - 1];
  fileId = best.file_id;
  fileUniqueId = best.file_unique_id;
  fileName = fileUniqueId + '.jpg';
} else if (msg.video) {
  msgType = 'video';
  videoDuration = msg.video.duration || 0;
  if (msg.video.thumb && msg.video.thumb.file_id) {
    fileId = msg.video.thumb.file_id;
    fileUniqueId = msg.video.thumb.file_unique_id;
    fileName = fileUniqueId + '_thumb.jpg';
  }
} else if (msg.document) {
  msgType = 'document';
  fileId = msg.document.file_id;
  fileUniqueId = msg.document.file_unique_id;
  fileName = msg.document.file_name || (fileUniqueId + '.bin');
}

const text = msg.text || msg.caption || '';
const fromUser = msg.from || {};
const fromName = (fromUser.first_name || '') + (fromUser.username ? ' (@' + fromUser.username + ')' : '');
const chatId = String(msg.chat.id);

const now = new Date();
const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = kst.toISOString().slice(0, 10);
const dateTimeStr = kst.toISOString().replace('Z', '+09:00');

return [{
  json: {
    is_allowed: isAllowed,
    user_id: userId,
    msg_type: msgType,
    file_id: fileId,
    file_name: fileName,
    has_attachment: fileId !== null,
    video_duration: videoDuration,
    text: text,
    from_name: fromName,
    chat_id: chatId,
    date_str: dateStr,
    date_time_str: dateTimeStr
  }
}];
"""

# Parse GPT: always reads from Prepare Message for original data
PARSE_GPT_CODE = r"""
// Always get original message data from Prepare Message node
const prep = $('Prepare Message').first().json;

let title = '\uBA54\uBAA8';
let tags = ['telegram'];

try {
  let content = $input.first().json?.choices?.[0]?.message?.content || '';
  content = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const parsed = JSON.parse(content);
  if (parsed.title) {
    title = parsed.title.replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_').slice(0, 40);
  }
  if (Array.isArray(parsed.tags)) tags = parsed.tags;
} catch(e) {}

const text = prep.text || '';
const hasUrl = /https?:\/\/[^\s]+/.test(text);
const urlMatch = text.match(/https?:\/\/[^\s]+/);
const firstUrl = urlMatch ? urlMatch[0] : null;

return [{
  json: {
    ...prep,
    gpt_title: title,
    gpt_tags: tags,
    has_url: hasUrl,
    first_url: firstUrl,
    file_name_md: prep.date_str + '_' + title + '.md',
    onedrive_md_path: 'Telegram/' + prep.date_str + '/' + prep.date_str + '_' + title + '.md',
    onedrive_att_path: prep.file_name ? ('Telegram/attachments/' + prep.file_name) : null
  }
}];
"""

EXTRACT_PREVIEW_CODE = r"""
const html = $input.first().json.data || '';
let title = '';
let desc = '';
const tm = html.match(/<title[^>]*>([^<]+)<\/title>/i);
if (tm) title = tm[1].replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').trim();
const dm = html.match(/<meta[^>]+(?:name="description"|property="og:description")[^>]+content="([^"]+)"/i)
  || html.match(/<meta[^>]+content="([^"]+)"[^>]+(?:name="description"|property="og:description")/i);
if (dm) desc = dm[1].trim();
return [{ json: { preview_title: title, preview_desc: desc } }];
"""

# Build MD: gets all data from Parse GPT Response; optionally reads Extract Preview
BUILD_MD_CODE = r"""
const item = $('Parse GPT Response').first().json;

const tagsYaml = (item.gpt_tags || []).map(t => '  - ' + t).join('\n');
let md = '---\n';
md += 'date: ' + item.date_time_str + '\n';
md += 'source: telegram\n';
md += 'type: ' + item.msg_type + '\n';
md += 'from: "' + item.from_name + '"\n';
md += 'tags:\n' + tagsYaml + '\n';
md += '---\n\n';

if (item.msg_type === 'photo') {
  if (item.file_name) md += '![[attachments/' + item.file_name + ']]\n\n';
  if (item.text) md += item.text + '\n';
} else if (item.msg_type === 'video') {
  if (item.file_name) md += '![[attachments/' + item.file_name + ']]\n\n';
  else md += '\uD83C\uDFAC \uC368\uB124\uC77C \uC5C6\uC74C\n\n';
  md += '\uD83C\uDFAC \uC601\uC0C1 \uAE38\uC774: ' + (item.video_duration || 0) + '\uCD08\n\n';
  if (item.text) md += item.text + '\n';
} else if (item.msg_type === 'document') {
  if (item.file_name) md += '[[attachments/' + item.file_name + '|' + item.file_name + ']]\n\n';
  if (item.text) md += item.text + '\n';
} else {
  md += (item.text || '') + '\n';
}

// Optionally append URL preview if it was fetched
try {
  const p = $('Extract Preview').first().json;
  if (p && p.preview_title) {
    md += '\n## \uB9C1\uD06C \uBBF8\uB9AC\uBCF4\uAE30\n\n';
    md += '**\uC81C\uBAA9**: ' + p.preview_title + '\n';
    if (p.preview_desc) md += '**\uC124\uBA85**: ' + p.preview_desc + '\n';
    md += '**URL**: ' + (item.first_url || '') + '\n';
  }
} catch(e) {}

return [{ json: { ...item, md_content: md } }];
"""

# OpenAI body: use $('Prepare Message') so it works regardless of which branch fed into this node
openai_content_expr = (
    "아래 텔레그램 메시지를 분석해서 JSON 형식으로만 응답하세요. 다른 텍스트 절대 포함 금지.\\n\\n"
    "규칙:\\n- title: 파일명으로 쓸 한국어 제목 (15자 이내, 언더스코어)\\n"
    "- tags: 핵심 키워드 3~5개\\n\\n"
    "예시: {\\\"title\\\": \\\"삼성전자_실적\\\", \\\"tags\\\": [\\\"삼성전자\\\"]}\\n\\n메시지:\\n"
)
openai_body = (
    "={{ JSON.stringify({ model: \"gpt-4o-mini\","
    " messages: [{ role: \"user\", content: \""
    + openai_content_expr
    + "\" + ($('Prepare Message').item.json.text || \"\").slice(0, 800) }],"
    " max_tokens: 200 }) }}"
)

# Use encoded path to avoid URL issues with Korean characters
ONEDRIVE_ATT_URL = (
    "=https://graph.microsoft.com/v1.0/me/drive/root:/"
    "%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8/Startegy_Investment/"
    "{{ $('Prepare Message').item.json.onedrive_att_path || ('Telegram/attachments/' + $('Prepare Message').item.json.file_name) }}"
    ":/content"
)

ONEDRIVE_MD_URL = (
    "=https://graph.microsoft.com/v1.0/me/drive/root:/"
    "%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8/Startegy_Investment/"
    "{{ $json.onedrive_md_path }}"
    ":/content"
)

workflow = {
  "name": "Telegram to Obsidian",
  "settings": {"executionOrder": "v1"},
  "nodes": [
    # 1. Telegram Trigger
    {
      "id": "n01", "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger", "typeVersion": 1.1,
      "position": [0, 300],
      "parameters": {"updates": ["message"], "additionalFields": {}},
      "credentials": {"telegramApi": {"id": TELEGRAM_CRED_ID, "name": "\ud154\ub808\uadf8\ub7a8 \uc635\uc2dc\ub514\uc5b8 \uc800\uc7a5 \ubc07"}}
    },
    # 2. Prepare Message
    {
      "id": "n02", "name": "Prepare Message",
      "type": "n8n-nodes-base.code", "typeVersion": 2,
      "position": [220, 300],
      "parameters": {"jsCode": PREPARE_CODE}
    },
    # 3. Check Access (true=allowed, false=blocked)
    {
      "id": "n03", "name": "Check Access",
      "type": "n8n-nodes-base.if", "typeVersion": 2,
      "position": [440, 300],
      "parameters": {
        "conditions": {
          "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 1},
          "conditions": [{"id": "c01", "leftValue": "={{ $json.is_allowed }}", "rightValue": True,
                          "operator": {"type": "boolean", "operation": "equals"}}],
          "combinator": "and"
        },
        "options": {}
      }
    },
    # 4. Send No Access (false branch of Check Access)
    {
      "id": "n04", "name": "Send No Access",
      "type": "n8n-nodes-base.telegram", "typeVersion": 1.2,
      "position": [660, 500],
      "parameters": {
        "chatId": "={{ $json.chat_id }}",
        "text": "\uc811\uadfc \uad8c\ud55c\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.",
        "additionalFields": {}
      },
      "credentials": {"telegramApi": {"id": TELEGRAM_CRED_ID, "name": "\ud154\ub808\uadf8\ub7a8 \uc635\uc2dc\ub514\uc5b8 \uc800\uc7a5 \ubc07"}}
    },
    # 5. Check Attachment (true=has file, false=text only)
    {
      "id": "n05", "name": "Check Attachment",
      "type": "n8n-nodes-base.if", "typeVersion": 2,
      "position": [660, 300],
      "parameters": {
        "conditions": {
          "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 1},
          "conditions": [{"id": "c02", "leftValue": "={{ $json.has_attachment }}", "rightValue": True,
                          "operator": {"type": "boolean", "operation": "equals"}}],
          "combinator": "and"
        },
        "options": {}
      }
    },
    # 6. Get File Info (Telegram getFile API)
    {
      "id": "n06", "name": "Get File Info",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [880, 180],
      "parameters": {
        "method": "GET",
        "url": "=https://api.telegram.org/bot{{ $vars.BOT_TOKEN }}/getFile",
        "sendQuery": True,
        "queryParameters": {"parameters": [{"name": "file_id", "value": "={{ $json.file_id }}"}]},
        "options": {}
      },
      "onError": "continueErrorOutput"
    },
    # 7. Download File (binary)
    {
      "id": "n07", "name": "Download File",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [1100, 180],
      "parameters": {
        "method": "GET",
        "url": "=https://api.telegram.org/file/bot{{ $vars.BOT_TOKEN }}/{{ $json.result.file_path }}",
        "options": {"response": {"response": {"responseFormat": "file", "outputPropertyName": "data"}}}
      },
      "onError": "continueErrorOutput"
    },
    # 8. Upload Attachment to OneDrive
    {
      "id": "n08", "name": "Upload Attachment",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [1320, 180],
      "parameters": {
        "method": "PUT",
        "url": ONEDRIVE_ATT_URL,
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "microsoftOneDriveOAuth2Api",
        "sendBody": True,
        "body": {"contentType": "binaryData", "inputDataFieldName": "data"},
        "options": {}
      },
      "credentials": {"microsoftOneDriveOAuth2Api": {"id": ONEDRIVE_CRED_ID, "name": "Microsoft Drive account"}},
      "onError": "continueErrorOutput"
    },
    # 9. Generate Title Tags (OpenAI) - receives from Upload Attachment OR Check Attachment false
    {
      "id": "n09", "name": "Generate Title Tags",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [1540, 300],
      "parameters": {
        "method": "POST",
        "url": "https://api.openai.com/v1/chat/completions",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "openAiApi",
        "sendBody": True,
        "body": {"contentType": "json", "content": openai_body},
        "options": {}
      },
      "credentials": {"openAiApi": {"id": OPENAI_CRED_ID, "name": "\ub274\uc2a4 \uc790\ub3d9\ud654 \ube0c\ub9ac\ud551 \uc6cc\ud06c\ud50c\ub85c\uc6b0"}},
      "onError": "continueErrorOutput"
    },
    # 10. Parse GPT Response + enrich with message data
    {
      "id": "n10", "name": "Parse GPT Response",
      "type": "n8n-nodes-base.code", "typeVersion": 2,
      "position": [1760, 300],
      "parameters": {"jsCode": PARSE_GPT_CODE}
    },
    # 11. Check URL (true=has URL, false=no URL)
    {
      "id": "n11", "name": "Check URL",
      "type": "n8n-nodes-base.if", "typeVersion": 2,
      "position": [1980, 300],
      "parameters": {
        "conditions": {
          "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 1},
          "conditions": [{"id": "c03", "leftValue": "={{ $json.has_url }}", "rightValue": True,
                          "operator": {"type": "boolean", "operation": "equals"}}],
          "combinator": "and"
        },
        "options": {}
      }
    },
    # 12. Fetch URL Preview
    {
      "id": "n12", "name": "Fetch URL Preview",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [2200, 180],
      "parameters": {
        "method": "GET",
        "url": "={{ $json.first_url }}",
        "options": {
          "timeout": 3000,
          "response": {"response": {"responseFormat": "text", "outputPropertyName": "data"}},
          "redirect": {"redirect": {"followRedirects": True, "maxRedirects": 3}}
        },
        "sendHeaders": True,
        "headerParameters": {"parameters": [{"name": "User-Agent", "value": "Mozilla/5.0"}]}
      },
      "onError": "continueErrorOutput"
    },
    # 13. Extract Preview (parse HTML)
    {
      "id": "n13", "name": "Extract Preview",
      "type": "n8n-nodes-base.code", "typeVersion": 2,
      "position": [2420, 180],
      "parameters": {"jsCode": EXTRACT_PREVIEW_CODE}
    },
    # 14. Build MD Content - receives from Extract Preview OR Check URL false
    {
      "id": "n14", "name": "Build MD Content",
      "type": "n8n-nodes-base.code", "typeVersion": 2,
      "position": [2640, 300],
      "parameters": {"jsCode": BUILD_MD_CODE}
    },
    # 15. Upload MD to OneDrive (Microsoft Graph API PUT)
    {
      "id": "n15", "name": "Upload MD to OneDrive",
      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
      "position": [2860, 300],
      "parameters": {
        "method": "PUT",
        "url": ONEDRIVE_MD_URL,
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "microsoftOneDriveOAuth2Api",
        "sendBody": True,
        "body": {"contentType": "raw", "rawContent": "={{ $json.md_content }}"},
        "sendHeaders": True,
        "headerParameters": {"parameters": [{"name": "Content-Type", "value": "text/markdown; charset=utf-8"}]},
        "options": {}
      },
      "credentials": {"microsoftOneDriveOAuth2Api": {"id": ONEDRIVE_CRED_ID, "name": "Microsoft Drive account"}}
    },
    # 16. Send Success
    {
      "id": "n16", "name": "Send Success",
      "type": "n8n-nodes-base.telegram", "typeVersion": 1.2,
      "position": [3080, 300],
      "parameters": {
        "chatId": "={{ $json.chat_id }}",
        "text": "=\uc800\uc7a5 \uc644\ub8cc\n{{ $json.file_name_md }}",
        "additionalFields": {}
      },
      "credentials": {"telegramApi": {"id": TELEGRAM_CRED_ID, "name": "\ud154\ub808\uadf8\ub7a8 \uc635\uc2dc\ub514\uc5b8 \uc800\uc7a5 \ubc07"}}
    }
  ],
  "connections": {
    "Telegram Trigger": {"main": [[{"node": "Prepare Message",    "type": "main", "index": 0}]]},
    "Prepare Message":  {"main": [[{"node": "Check Access",       "type": "main", "index": 0}]]},
    # Check Access: output 0 = true (allowed), output 1 = false (blocked)
    "Check Access": {"main": [
      [{"node": "Check Attachment",   "type": "main", "index": 0}],
      [{"node": "Send No Access",     "type": "main", "index": 0}]
    ]},
    # Check Attachment: output 0 = true (has file), output 1 = false (no file)
    # Both routes lead to Generate Title Tags
    "Check Attachment": {"main": [
      [{"node": "Get File Info",          "type": "main", "index": 0}],
      [{"node": "Generate Title Tags",    "type": "main", "index": 0}]
    ]},
    "Get File Info":    {"main": [[{"node": "Download File",       "type": "main", "index": 0}]]},
    "Download File":    {"main": [[{"node": "Upload Attachment",   "type": "main", "index": 0}]]},
    # Upload Attachment leads to Generate Title Tags (same as no-attachment path)
    "Upload Attachment": {"main": [[{"node": "Generate Title Tags","type": "main", "index": 0}]]},
    "Generate Title Tags": {"main": [[{"node": "Parse GPT Response","type": "main", "index": 0}]]},
    "Parse GPT Response":  {"main": [[{"node": "Check URL",        "type": "main", "index": 0}]]},
    # Check URL: output 0 = true (has URL), output 1 = false (no URL)
    # Both routes lead to Build MD Content
    "Check URL": {"main": [
      [{"node": "Fetch URL Preview",   "type": "main", "index": 0}],
      [{"node": "Build MD Content",    "type": "main", "index": 0}]
    ]},
    "Fetch URL Preview": {"main": [[{"node": "Extract Preview",    "type": "main", "index": 0}]]},
    # Extract Preview leads to Build MD Content (same as no-URL path)
    "Extract Preview":    {"main": [[{"node": "Build MD Content",  "type": "main", "index": 0}]]},
    "Build MD Content":   {"main": [[{"node": "Upload MD to OneDrive","type": "main", "index": 0}]]},
    "Upload MD to OneDrive": {"main": [[{"node": "Send Success",   "type": "main", "index": 0}]]}
  }
}

out = "C:/Users/PC/Desktop/test/projects/telegram-to-obsidian/workflows/telegram-to-obsidian.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, ensure_ascii=False, indent=2)
print(f"Done. Nodes: {len(workflow['nodes'])} -> {out}")
