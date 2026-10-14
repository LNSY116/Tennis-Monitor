# 🎾 TennisCourtMonitor (網球場時段智慧監控小助手)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot%20API-blue?logo=telegram)](https://core.telegram.org/bots/api)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini%20API-orange?logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基於 **Python + Telegram Bot + Google Gemini AI** 的臺北市公有網球場時段即時監控與智慧推播系統。

支援自然語言查詢、定時背景排程、精準狀態比對與釋出空位即時通知。

---

## ✨ 核心特色

- ⚡ **即時動態爬蟲**：直接解析官方 `LoadSched` XHR API，精準獲取每個場地的即時預約狀態與預訂人/活動名稱。
- 🤖 **Gemini AI 雙向驅動**：
  - **意圖與時間推理**：支援模糊口語（如「下週六」、「這兩天」、「5/20 以後」），自動推理並展開為精確日期清單。
  - **智慧格式化**：能根據使用者要求（如「只要看下午的空位」）動態客製化回覆內容。
- 🛡️ **高韌性 Fallback 機制**：
  - 具備本地正則表達式備援；即使 AI API 遇額度限制或連線問題，核心查詢與監控功能仍 100% 正常運作。
  - Telegram 訊息安全降級機制，防範 Markdown 解析異常導致的崩潰。
- 🔔 **背景定時監控**：整合 Telegram `JobQueue`，背景每 2 分鐘自動輪詢，發現新釋出的空位即時推送通知。
- 💻 **跨平台相容**：特別針對 Windows 環境優化 UTF-8 主控台輸出，避免 Emoji 編碼崩潰。

---

## 🏗️ 系統架構

```mermaid
flowchart TD
    User([使用者 Telegram]) <--> Bot[Telegram Bot (bot.py)]
    
    subgraph 核心邏輯
        Bot <--> AI[AI 模組 (ai_helper.py)\n- 意圖識別\n- 自然語言解析]
        Bot <--> Scraper[爬蟲模組 (scraper.py)\n- 官方 XHR 請求\n- 時段比對]
        JobQueue[定時排程 JobQueue\n- 每 2 分鐘背景檢查] --> Bot
    end

    AI <--> GeminiAPI[(Google Gemini API)]
    Scraper <--> SportsAPI[(臺北市體育局場地系統)]
```

---

## 🚀 快速開始

### ⚡ 方案 A：非工程人員 30 秒一鍵啟動（推薦）

如果你不熟悉指令列，只要簡單兩步：

1. **填寫金鑰**：
   將專案目錄下的 `.env.example` 複製一份並重新命名為 `.env`，使用記事本開啟並填入你的 `TELEGRAM_BOT_TOKEN` 與 `GOOGLE_API_KEY`。
2. **雙擊啟動**：
   - **Windows 使用者**：直接連按兩下專案根目錄的 **`start.bat`**。
   - **macOS / Linux 使用者**：執行 `./start.sh`。

> 💡 `start.bat` 會自動檢查 Python、自動建立虛擬環境、自動安裝所需套件，並一鍵啟動機器人，完全免手動敲指令！

---

### 💻 方案 B：工程人員手動指令啟動

```bash
# 1. 複製專案
git clone https://github.com/LNSY116/Tennis-Monitor.git
cd Tennis-Monitor

# 2. 建立並啟用虛擬環境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 設定環境變數 (.env)
cp .env.example .env
# 請編輯 .env 填入金鑰

# 5. 系統一鍵診斷 (選用)
python tools/verify_system.py

# 6. 啟動主程式
python main.py
```

---

## 💬 使用方式

你可以直接用自然語言與機器人交談，或使用標準斜線指令：

### 自然語言範例
- `幫我查明天下午有沒有空位`
- `下週六如果有人退訂請通知我`
- `5/20以後哪天有場地？`

### 斜線指令

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| `/check <日期>` | 即時查詢指定日期的空位狀態 | `/check 5/20` 或 `/check 0518-20` |
| `/monitor <日期>` | 訂閱空位通知，有空位釋出時自動推播 | `/monitor 5/25` |
| `/list` | 查看當前監控中的日期清單 | `/list` |
| `/stop` | 取消所有監控訂閱 | `/stop` |
| `/help` | 顯示使用指南與功能清單 | `/help` |

---

## 📁 簡潔專案架構

```text
Tennis-Monitor/
├── start.bat          # 🖱️ Windows 非工程人員雙擊一鍵安裝啟動腳本
├── start.sh           # 🖱️ Linux / macOS 一鍵啟動腳本
├── main.py            # 🚀 專案唯一主程式入口
├── requirements.txt   # 相依套件清單
├── .env.example       # 環境變數設定範本
├── README.md          # 專案完整說明文件
├── LICENSE            # MIT 開源授權合約
│
├── src/               # 📦 核心業務模組
│   ├── bot.py         # Telegram Bot 核心與自然語言處理
│   ├── scraper.py     # 臺北市體育局場地 XHR 爬蟲引擎
│   ├── ai_helper.py   # Gemini AI 意圖分析與對話格式化
│   └── config.py      # 環境設定與參數驗證
│
├── tools/             # 🛠️ 輔助與診斷工具
│   ├── verify_system.py # 系統自我端到端驗證工具
│   └── check_models.py  # Gemini API 可用模型清單查詢工具
│
└── docs/              # 📚 歷史開發與排錯診斷報告
```

---

## 🛠️ 開發工具與診斷

- **查詢可用的 Gemini 模型**：
  ```bash
  python tools/check_models.py
  ```
- **系統完整檢測**：
  ```bash
  python tools/verify_system.py
  ```

---

## 📄 開源授權

本專案採用 [MIT License](LICENSE) 授權條款開源。
僅供程式開發學習與研究使用，請遵守目標網站使用規範，勿用於高頻惡意請求。
