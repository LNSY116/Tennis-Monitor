import requests
import time
import random
import re
from bs4 import BeautifulSoup

def fetch_venue_slots(venue_id="352", target_dates=None):
    """
    單次抓取場地時段（基於真實 VBS 網頁結構解析）
    回傳格式：{"slots": [{"date", "time", "status", "booker"}], "alerts": []}
    """
    url = f"https://vbs.sports.taipei/venues/?K={venue_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://vbs.sports.taipei/"
    }

    # 🛡️ 低風險：隨機延遲 2~5 秒，模擬真人瀏覽
    time.sleep(random.uniform(2, 5))

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        slots = []
        alerts = []

        # 🔍 精準定位：所有 id 以 DataPickup. 開頭的 <td> 區塊
        cells = soup.select('td[id^="DataPickup."]')
        if not cells:
            alerts.append("⚠️ 找不到時段資料區塊，網頁結構可能已變更或需登入。")
            return {"slots": [], "alerts": alerts}

        # 📅 正規化 target_dates 格式為 MM/DD，避免比對失敗
        norm_target = []
        if target_dates:
            for d in target_dates:
                parts = d.replace('-', '/').split('/')
                if len(parts) == 2:
                    norm_target.append(f"{int(parts[0]):02d}/{int(parts[1]):02d}")

        for td in cells:
            td_id = td.get('id', '')
            # 🧩 解析 ID 格式：DataPickup.YYYY.M.D.H.1
            id_match = re.match(r'DataPickup\.(\d{4})\.(\d{1,2})\.(\d{1,2})\.(\d{1,2})\.\d+', td_id)
            if not id_match:
                continue

            year, month, day, hour = id_match.groups()
            slot_date = f"{int(month):02d}/{int(day):02d}"
            
            # 預設時間區間（依 ID 的小時推算）
            slot_time = f"{int(hour):02d}:00-{int(hour)+1:02d}:00"

            # 🎯 日期過濾
            if norm_target and slot_date not in norm_target:
                continue

            # 取得內部狀態 div
            div = td.find('div', class_='BookB')
            if not div:
                continue

            div_classes = div.get('class', [])
            # 清理文字（處理 <br> 與多餘空白）
            text = div.get_text(separator=' ', strip=True)

            status = 'unknown'
            booker = ''

            if 'UnBooked' in div_classes:
                status = 'available'
                # 嘗試從文字抓取精確時間（例：13:00 ~ 14:00）
                time_match = re.search(r'(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})', text)
                if time_match:
                    slot_time = f"{time_match.group(1)}-{time_match.group(2)}"
                    
            elif 'Booked' in div_classes:
                status = 'booked'
                booker = text  # 例：台灣網球協會訓練
                
            elif 'RangeOut' in div_classes:
                status = 'expired'
                booker = text  # 例：已過期 停止租借
            else:
                continue  # 忽略其他未知狀態

            slots.append({
                "date": slot_date,
                "time": slot_time,
                "status": status,
                "booker": booker
            })

        if not slots and not alerts:
            alerts.append("✅ 成功解析網頁，但沒有符合目標日期的時段。")

        return {"slots": slots, "alerts": alerts}

    except requests.exceptions.RequestException as e:
        return {"slots": [], "alerts": [f"🌐 網路請求失敗: {str(e)}"]}
    except Exception as e:
        return {"slots": [], "alerts": [f"💥 解析錯誤: {str(e)}"]}