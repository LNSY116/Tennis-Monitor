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

### 1. 複製專案

```bash
git clone https://github.com/LNSY116/Tennis-Monitor.git
cd Tennis-Monitor
```

### 2. 安裝相依套件

建議使用虛擬環境：

```bash
python -m venv venv
# Windows 啟用虛擬環境:
venv\Scripts\activate
# Linux/macOS 啟用虛擬環境:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. 設定環境變數

複製環境變數範本並填入你的金鑰：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```env
# Telegram Bot 配置 (向 @BotFather 取得)
TELEGRAM_BOT_TOKEN=你的_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=你的_CHAT_ID

# Google Gemini API 配置 (向 Google AI Studio 取得)
GOOGLE_API_KEY=你的_GEMINI_API_KEY

# 場地配置 (預設 352 為彩虹網球場)
VENUE_ID=352
VENUE_BASE_URL=https://vbs.sports.taipei/venues/?K=352

# 請求與監控設定
REQUEST_DELAY_MIN=2
REQUEST_DELAY_MAX=5
REQUEST_TIMEOUT=15
MONITOR_INTERVAL=120
```

### 4. 系統驗證

在啟動前執行內建的診斷腳本，驗證環境變數、模組依賴與 API 連線：

```bash
python verify_system.py
```

### 5. 啟動機器人

```bash
python bot.py
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

## 📁 專案結構

```text
Tennis-Monitor/
├── bot.py             # Telegram Bot 主程式與指令處理
├── scraper.py         # 臺北市體育局場地 XHR 爬蟲引擎
├── ai_helper.py       # Google Gemini 意圖推理與自然語言回覆模組
├── config.py          # 設定檔載入與環境變數校驗
├── check_models.py    # Gemini API 可用模型診斷工具
├── verify_system.py   # 系統自我檢驗端到端測試腳本
├── requirements.txt   # 專案相依套件清單
├── .env.example       # 環境變數設定範本
├── docs/              # 開發歷程與技術診斷報告
└── README.md          # 專案說明文件
```

---

## 🛠️ 開發工具與診斷

- **查詢可用的 Gemini 模型**：
  ```bash
  python check_models.py
  ```
- **系統完整檢測**：
  ```bash
  python verify_system.py
  ```

---

## 📄 開源授權

本專案採用 [MIT License](LICENSE) 授權條款開源。
僅供程式開發學習與研究使用，請遵守目標網站使用規範，勿用於高頻惡意請求。
