import json
import os
import requests

# 1. 從環境變數讀取金鑰
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 2. 讀取本地的 JSON 題庫
with open('articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

# 3. 尋找第一篇「未發送」的文章
target_article = None
target_index = -1
for i, article in enumerate(articles):
    if not article.get('used', False):
        target_article = article
        target_index = i
        break

if not target_article:
    print("🎉 所有文章已發送完畢，請補充題庫！")
    exit()

# 4. 組合 Prompt
prompt = f"""
你是一位香港 DSE 中文科名師。請閱讀以下文言文並提供教學內容：
標題：{target_article['title']}
原文：{target_article['content']}

請提供：
1. 簡單語譯。
2. 針對高中生標記 3 個重點注釋（請解釋字詞意思）。
3. 標出 1-2 個 DSE 學習點（例如常見文言虛詞/實詞，或這篇文章的思想與 DSE 指定篇章、中國傳統文化的關聯）。
請以簡潔易讀的排版輸出，不要加多餘的自我介紹。
"""

print(f"正在呼叫 MiniMax AI 處理：《{target_article['title']}》...")

# 5. 設定 MiniMax API 請求
minimax_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Authorization": f"Bearer {MINIMAX_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "abab6.5s-chat", # 使用 abab6.5s-chat 模型，性價比高且速度快
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

# 發送請求給 MiniMax
try:
    response = requests.post(minimax_url, headers=headers, json=payload)
    response.raise_for_status() # 檢查是否有 HTTP 錯誤
    ai_content = response.json()['choices'][0]['message']['content']
except Exception as e:
    print(f"❌ MiniMax API 呼叫失敗：{e}")
    if 'response' in locals():
        print(f"錯誤詳情：{response.text}")
    exit(1)

# 6. 整理格式並發送至 Discord
discord_message = {
    "content": f"## 📚 今日文言文：《{target_article['title']}》\n\n**【原文】**\n> {target_article['content']}\n\n**【名師解析】**\n{ai_content}"
}

res = requests.post(DISCORD_WEBHOOK_URL, json=discord_message)

# 7. 如果發送成功，將文章標記為已使用並存檔
if res.status_code in [200, 204]:
    print("✅ 成功發送至 Discord！")
    articles[target_index]['used'] = True
    with open('articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
else:
    print(f"❌ Discord 發送失敗：{res.status_code} - {res.text}")
