# 🎾 TennisCourtMonitor

臺北市公有網球場時段即時監控系統，整合 Telegram Bot 查詢、釋出空位自動推播，並支援 Gemini 自然語言日期解析。

---

## 🚀 快速開始

### 1. 配置環境變數
複製 `.env.example` 為 `.env` 並填入金鑰：
```bash
cp .env.example .env
```
主要參數：
- `TELEGRAM_BOT_TOKEN`：Telegram 機器人 Token (向 @BotFather 取得)
- `GOOGLE_API_KEY`：Google Gemini API Key
- `VENUE_ID`：場地代碼（預設 `352` 為彩虹網球場）

### 2. 啟動服務
- **自動化啟動**：
  - Windows：執行 `start.bat`
  - Linux / macOS：執行 `./start.sh`
- **手動指令啟動**：
  ```bash
  pip install -r requirements.txt
  python main.py
  ```

---

## 💬 使用方式

支援自然語言查詢或標準指令：

- **自然語言**：「查明天下午有沒有空位」、「下週六有位子通知我」、「5/20以後哪天有場地」
- **機器人指令**：
  - `/check 5/20`：查詢指定日期的空位狀態
  - `/monitor 5/25`：訂閱空位釋出通知
  - `/list`：查看目前監控中的日期清單
  - `/stop`：取消所有監控訂閱

---

## 📁 專案結構

```text
Tennis-Monitor/
├── start.bat          # Windows 自動化啟動腳本
├── start.sh           # Linux / macOS 啟動腳本
├── main.py            # 主程式進入點
├── requirements.txt   # 相依套件
├── .env.example       # 設定檔範本
├── src/               # 核心邏輯 (bot, scraper, ai_helper, config)
├── tools/             # 檢驗工具 (verify_system, check_models)
└── docs/              # 技術文件與歷程記錄
```

---

## 📄 License

[MIT License](LICENSE)
