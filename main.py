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
* 你是一位『香港 DSE 中文科名師』，專門協助高中生解讀文言文並應對考試。
* 你的職責是將艱澀的古代文獻轉化為易於理解的學習素材，並針對香港中學文憑考試（DSE）的評核要求提供指導。
請閱讀以下文言文並提供教學內容：
標題：{target_article['title']}
原文：{target_article['content']}

行為規範：

1) 教學內容結構：
   a) 語譯：提供準確且平實的現代漢語對譯，確保學生能理解原文大意。
   b) 重點注釋：挑選兩個對理解全篇至關重要的字詞，解釋其意思、詞性或古今異義。
   c) DSE 學習點：分析文言虛詞或實詞的運用，或探討文章與 DSE 十二篇範文、中國傳統文化（如儒家、道家思想）的連結。

2) 輸出要求：
   a) 採用簡潔易讀的排版，善用列點與標題。
   b) 嚴禁進行任何形式的自我介紹或開場白，直接輸出教學內容。
   c) 資訊密度要高，語氣專業且精煉。

語氣與特質：

* 專業、資深、精簡且目標明確。
* 像一位補習名師，用最短的時間傳遞最有價值的考試資訊。

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

# 6. 整理格式並發送至 Discord (確保包含發送動作)
description_text = f"**【原文】**\n> {target_article['content']}\n\n**【名師解析】**\n{ai_content}"

# 安全機制：確保字數不會超過 Embed 的 4096 字元極限
if len(description_text) > 4000:
    description_text = description_text[:4000] + "\n\n...（字數過長，部分內容已省略）"

discord_message = {
    "embeds": [
        {
            "title": f"📚 今日文言文：《{target_article['title']}》",
            "description": description_text,
            "color": 5814783 
        }
    ]
}

# ⭐ 重要：就是少了下面這一行，才導致 NameError！
res = requests.post(DISCORD_WEBHOOK_URL, json=discord_message)

# 7. 如果發送成功，將文章標記為已使用並存檔
if res.status_code in [200, 204]:
    print("✅ 成功發送至 Discord！")
    articles[target_index]['used'] = True
    with open('articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
else:
    print(f"❌ Discord 發送失敗：{res.status_code} - {res.text}")
