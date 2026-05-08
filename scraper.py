import json
import random
import re
import time
from datetime import datetime

import requests


def fetch_venue_slots(venue_id="352", target_dates=None):
    """
    抓取場地時段資料。

    這個站點的時段表不是直接寫在 HTML 中，而是由頁面腳本透過
    `/_/x/xhrworkv3.php` 取得 JSON 後渲染，因此要先建立站內 session。
    回傳格式：{"slots": [{"date", "time", "status", "booker"}], "alerts": []}
    """
    page_url = f"https://vbs.sports.taipei/venues/?K={venue_id}"
    xhr_url = "https://vbs.sports.taipei/_/x/xhrworkv3.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": page_url,
        "Origin": "https://vbs.sports.taipei",
    }

    time.sleep(random.uniform(2, 5))

    try:
        session = requests.Session()
        page_response = session.get(page_url, headers=headers, timeout=20)
        page_response.raise_for_status()
        page_response.encoding = "utf-8"

        start_cfg, end_cfg = _extract_view_range(page_response.text)
        open_hour, close_hour = _extract_open_close_hours(page_response.text)
        months_to_fetch = _build_month_list(start_cfg, end_cfg, target_dates)

        slots = []
        alerts = []

        for year, month in months_to_fetch:
            payload = {
                "FUNC": "LoadSched",
                "SY": str(year),
                "SM": str(month),
                "RSD": f"{year}-{month}-1",
                "RED": f"{year}-{month}-30",
                "VenueSN": _extract_venue_sn(page_response.text, venue_id),
                "OrderNo": "",
                "ZRMode": "",
                "ZRTTimes": "",
                "AddOrderMode": "",
            }

            xhr_response = session.post(xhr_url, headers=headers, data=payload, timeout=20)
            xhr_response.raise_for_status()

            data = _safe_json_loads(xhr_response.text)
            if not data:
                alerts.append(f"⚠️ 無法解析 {year}-{month:02d} 的時段資料")
                continue

            slots.extend(_parse_schedule_json(data, year, month, target_dates, open_hour, close_hour))

        if not slots and not alerts:
            alerts.append("✅ 成功連接到網站，但沒有符合條件的時段資料。")

        return {"slots": slots, "alerts": alerts}

    except requests.exceptions.RequestException as e:
        return {"slots": [], "alerts": [f"🌐 網路請求失敗: {str(e)}"]}
    except Exception as e:
        return {"slots": [], "alerts": [f"💥 解析錯誤: {str(e)}"]}


def _extract_view_range(html_text):
    """從頁面中抓出可視月份範圍，抓不到時回傳當月與下月。"""
    match = re.search(
        r"PickupDateDateOriginal=\{DfSY:(\d+),DfSM:(\d+),DfSD:(\d+),DfEY:(\d+),DfEM:(\d+),DfED:(\d+)\}",
        html_text,
    )
    if match:
        start_year = int(match.group(1))
        start_month = int(match.group(2))
        end_year = int(match.group(4))
        end_month = int(match.group(5))
        return (start_year, start_month), (end_year, end_month)

    now = datetime.now()
    next_month = now.month + 1
    next_year = now.year
    if next_month > 12:
        next_month = 1
        next_year += 1
    return (now.year, now.month), (next_year, next_month)


def _extract_open_close_hours(html_text):
    """從頁面腳本中抓取營業時間，抓不到時預設為 08:00 到 22:00。"""
    match = re.search(r'"OpenTime":"(\d{2}):\d{2}:\d{2}".*?"CloseTime":"(\d{2}):\d{2}:\d{2}"', html_text, re.DOTALL)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 8, 22


def _build_month_list(start_cfg, end_cfg, target_dates):
    """建立要抓取的月份列表。若指定 target_dates，則只抓對應月份。"""
    if target_dates:
        months = set()
        for date_text in target_dates:
            parts = date_text.replace("-", "/").split("/")
            if len(parts) == 2:
                months.add((start_cfg[0], int(parts[0])))
        return sorted(months)

    months = []
    year, month = start_cfg
    end_year, end_month = end_cfg
    while (year, month) <= (end_year, end_month):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _extract_venue_sn(html_text, fallback_venue_id):
    """頁面腳本內的 VenueSN 可能不同於 K 值，優先使用頁面內設定。"""
    match = re.search(r"VenueSN:(\d+)", html_text)
    if match:
        return match.group(1)
    return fallback_venue_id


def _safe_json_loads(text):
    try:
        return json.loads(text.strip())
    except Exception:
        return None


def _parse_schedule_json(data, year, month, target_dates=None, open_hour=8, close_hour=22):
    """把 LoadSched 回傳的 JSON 轉為統一的 slots 格式。"""
    slots = []
    target_set = _normalize_target_dates(target_dates)
    day_map = data.get("RT", {}) if isinstance(data, dict) else {}

    for day_key, time_map in day_map.items():
        if not str(day_key).isdigit() or not isinstance(time_map, dict):
            continue

        slot_date = f"{month:02d}/{int(day_key):02d}"
        if target_set and slot_date not in target_set:
            continue

        for time_key, item in time_map.items():
            if not isinstance(item, dict):
                continue

            start_time = item.get("S") or f"{time_key[:2]}:00"
            end_time = item.get("E") or _next_hour(start_time)
            start_hour = _time_to_hour(start_time)
            if start_hour is None or start_hour < open_hour or start_hour >= close_hour:
                continue

            status = "booked" if str(item.get("D", "0")) == "1" else "available"
            
            # 整合預訂人 (M) 與活動名稱 (EVA 優先於 EV，因為 EV 可能是縮寫)
            m_name = (item.get("M") or "").strip()
            ev_name = (item.get("EVA") or item.get("EV") or "").strip()
            
            if m_name and ev_name and m_name != ev_name:
                booker = f"{m_name} - {ev_name}"
            else:
                booker = m_name or ev_name or ""

            slots.append(
                {
                    "date": slot_date,
                    "time": f"{start_time}-{end_time}",
                    "status": status,
                    "booker": booker,
                }
            )

    return slots


def _normalize_target_dates(target_dates):
    normalized = set()
    if not target_dates:
        return normalized

    for date_text in target_dates:
        parts = date_text.replace("-", "/").split("/")
        if len(parts) == 2:
            normalized.add(f"{int(parts[0]):02d}/{int(parts[1]):02d}")
    return normalized


def _next_hour(start_time):
    try:
        hour = int(start_time.split(":")[0])
        return f"{hour + 1:02d}:00"
    except Exception:
        return "N/A"


def _time_to_hour(time_text):
    try:
        return int(time_text.split(":")[0])
    except Exception:
        return None