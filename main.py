import os
import asyncio
import base64
import hashlib
import html
import json
import re
import tempfile
import time
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
from typing import List
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

stock_list: list[dict] = []

KR_STOCKS = [
    {"name": "삼성전자", "code": "005930", "market": "KOSPI"},
    {"name": "SK하이닉스", "code": "000660", "market": "KOSPI"},
    {"name": "LG에너지솔루션", "code": "373220", "market": "KOSPI"},
    {"name": "삼성바이오로직스", "code": "207940", "market": "KOSPI"},
    {"name": "현대자동차", "code": "005380", "market": "KOSPI"},
    {"name": "기아", "code": "000270", "market": "KOSPI"},
    {"name": "셀트리온", "code": "068270", "market": "KOSPI"},
    {"name": "KB금융", "code": "105560", "market": "KOSPI"},
    {"name": "POSCO홀딩스", "code": "005490", "market": "KOSPI"},
    {"name": "신한지주", "code": "055550", "market": "KOSPI"},
    {"name": "NAVER", "code": "035420", "market": "KOSPI"},
    {"name": "삼성SDI", "code": "006400", "market": "KOSPI"},
    {"name": "LG화학", "code": "051910", "market": "KOSPI"},
    {"name": "현대모비스", "code": "012330", "market": "KOSPI"},
    {"name": "카카오", "code": "035720", "market": "KOSPI"},
    {"name": "삼성물산", "code": "028260", "market": "KOSPI"},
    {"name": "하나금융지주", "code": "086790", "market": "KOSPI"},
    {"name": "삼성생명", "code": "032830", "market": "KOSPI"},
    {"name": "LG전자", "code": "066570", "market": "KOSPI"},
    {"name": "SK이노베이션", "code": "096770", "market": "KOSPI"},
    {"name": "SK텔레콤", "code": "017670", "market": "KOSPI"},
    {"name": "한국전력공사", "code": "015760", "market": "KOSPI"},
    {"name": "SK", "code": "034730", "market": "KOSPI"},
    {"name": "HD현대중공업", "code": "329180", "market": "KOSPI"},
    {"name": "KT&G", "code": "033780", "market": "KOSPI"},
    {"name": "삼성화재", "code": "000810", "market": "KOSPI"},
    {"name": "우리금융지주", "code": "316140", "market": "KOSPI"},
    {"name": "한화에어로스페이스", "code": "012450", "market": "KOSPI"},
    {"name": "HD한국조선해양", "code": "009540", "market": "KOSPI"},
    {"name": "메리츠금융지주", "code": "138040", "market": "KOSPI"},
    {"name": "KT", "code": "030200", "market": "KOSPI"},
    {"name": "두산에너빌리티", "code": "034020", "market": "KOSPI"},
    {"name": "삼성전기", "code": "009150", "market": "KOSPI"},
    {"name": "한화오션", "code": "042660", "market": "KOSPI"},
    {"name": "LG", "code": "003550", "market": "KOSPI"},
    {"name": "SK스퀘어", "code": "402340", "market": "KOSPI"},
    {"name": "고려아연", "code": "010130", "market": "KOSPI"},
    {"name": "한미반도체", "code": "042700", "market": "KOSPI"},
    {"name": "카카오뱅크", "code": "323410", "market": "KOSPI"},
    {"name": "삼성에스디에스", "code": "018260", "market": "KOSPI"},
    {"name": "현대건설", "code": "000720", "market": "KOSPI"},
    {"name": "LG이노텍", "code": "011070", "market": "KOSPI"},
    {"name": "대한항공", "code": "003490", "market": "KOSPI"},
    {"name": "HMM", "code": "011200", "market": "KOSPI"},
    {"name": "롯데케미칼", "code": "011170", "market": "KOSPI"},
    {"name": "S-Oil", "code": "010950", "market": "KOSPI"},
    {"name": "한화솔루션", "code": "009830", "market": "KOSPI"},
    {"name": "아모레퍼시픽", "code": "090430", "market": "KOSPI"},
    {"name": "CJ제일제당", "code": "097950", "market": "KOSPI"},
    {"name": "포스코퓨처엠", "code": "003670", "market": "KOSPI"},
    {"name": "에코프로비엠", "code": "247540", "market": "KOSPI"},
    {"name": "한국가스공사", "code": "036460", "market": "KOSPI"},
    {"name": "현대제철", "code": "004020", "market": "KOSPI"},
    {"name": "NH투자증권", "code": "005940", "market": "KOSPI"},
    {"name": "미래에셋증권", "code": "006800", "market": "KOSPI"},
    {"name": "삼성증권", "code": "016360", "market": "KOSPI"},
    {"name": "한국타이어앤테크놀로지", "code": "161390", "market": "KOSPI"},
    {"name": "DB손해보험", "code": "005830", "market": "KOSPI"},
    {"name": "크래프톤", "code": "259960", "market": "KOSPI"},
    {"name": "엔씨소프트", "code": "036570", "market": "KOSPI"},
    {"name": "에코프로", "code": "086520", "market": "KOSDAQ"},
    {"name": "알테오젠", "code": "196170", "market": "KOSDAQ"},
    {"name": "HLB", "code": "028300", "market": "KOSDAQ"},
    {"name": "레인보우로보틱스", "code": "277810", "market": "KOSDAQ"},
    {"name": "셀트리온제약", "code": "068760", "market": "KOSDAQ"},
    {"name": "엘앤에프", "code": "066970", "market": "KOSDAQ"},
    {"name": "리노공업", "code": "058470", "market": "KOSDAQ"},
    {"name": "카카오게임즈", "code": "293490", "market": "KOSDAQ"},
    {"name": "펄어비스", "code": "263750", "market": "KOSDAQ"},
    {"name": "CJ ENM", "code": "035760", "market": "KOSDAQ"},
    {"name": "JYP Ent.", "code": "035900", "market": "KOSDAQ"},
    {"name": "HYBE", "code": "352820", "market": "KOSDAQ"},
    {"name": "SM", "code": "041510", "market": "KOSDAQ"},
    {"name": "위메이드", "code": "112040", "market": "KOSDAQ"},
    {"name": "덕산네오룩스", "code": "213420", "market": "KOSDAQ"},
    {"name": "씨젠", "code": "096530", "market": "KOSDAQ"},
    {"name": "클래시스", "code": "214150", "market": "KOSDAQ"},
    {"name": "에스엠씨지", "code": "048550", "market": "KOSDAQ"},
    {"name": "파라다이스", "code": "034230", "market": "KOSDAQ"},
    {"name": "솔브레인", "code": "357780", "market": "KOSDAQ"},
    {"name": "동진쎄미켐", "code": "005290", "market": "KOSDAQ"},
    {"name": "이오테크닉스", "code": "039030", "market": "KOSDAQ"},
    {"name": "주성엔지니어링", "code": "036930", "market": "KOSDAQ"},
    {"name": "티씨케이", "code": "064760", "market": "KOSDAQ"},
    {"name": "원익IPS", "code": "240810", "market": "KOSDAQ"},
    {"name": "피에스케이", "code": "319660", "market": "KOSDAQ"},
    {"name": "ISC", "code": "095340", "market": "KOSDAQ"},
    {"name": "하나마이크론", "code": "067310", "market": "KOSDAQ"},
    {"name": "넥스틴", "code": "348210", "market": "KOSDAQ"},
    {"name": "두산테스나", "code": "131970", "market": "KOSDAQ"},
]

US_STOCKS = [
    {"name": "Apple", "code": "AAPL", "market": "US"},
    {"name": "Microsoft", "code": "MSFT", "market": "US"},
    {"name": "Amazon", "code": "AMZN", "market": "US"},
    {"name": "Alphabet", "code": "GOOGL", "market": "US"},
    {"name": "Meta Platforms", "code": "META", "market": "US"},
    {"name": "Tesla", "code": "TSLA", "market": "US"},
    {"name": "NVIDIA", "code": "NVDA", "market": "US"},
    {"name": "AMD", "code": "AMD", "market": "US"},
    {"name": "Intel", "code": "INTC", "market": "US"},
    {"name": "Netflix", "code": "NFLX", "market": "US"},
    {"name": "Broadcom", "code": "AVGO", "market": "US"},
    {"name": "TSMC", "code": "TSM", "market": "US"},
    {"name": "ASML", "code": "ASML", "market": "US"},
    {"name": "Berkshire Hathaway", "code": "BRK.B", "market": "US"},
    {"name": "JPMorgan Chase", "code": "JPM", "market": "US"},
    {"name": "Visa", "code": "V", "market": "US"},
    {"name": "Johnson & Johnson", "code": "JNJ", "market": "US"},
    {"name": "Walmart", "code": "WMT", "market": "US"},
    {"name": "Mastercard", "code": "MA", "market": "US"},
    {"name": "Costco", "code": "COST", "market": "US"},
    {"name": "Palantir", "code": "PLTR", "market": "US"},
    {"name": "Arm Holdings", "code": "ARM", "market": "US"},
    {"name": "Micron", "code": "MU", "market": "US"},
    {"name": "Applied Materials", "code": "AMAT", "market": "US"},
    {"name": "Lam Research", "code": "LRCX", "market": "US"},
    {"name": "Qualcomm", "code": "QCOM", "market": "US"},
    {"name": "Texas Instruments", "code": "TXN", "market": "US"},
    {"name": "Salesforce", "code": "CRM", "market": "US"},
    {"name": "Adobe", "code": "ADBE", "market": "US"},
    {"name": "Oracle", "code": "ORCL", "market": "US"},
    {"name": "Cisco", "code": "CSCO", "market": "US"},
    {"name": "Uber", "code": "UBER", "market": "US"},
    {"name": "ServiceNow", "code": "NOW", "market": "US"},
    {"name": "IBM", "code": "IBM", "market": "US"},
    {"name": "Snowflake", "code": "SNOW", "market": "US"},
    {"name": "CrowdStrike", "code": "CRWD", "market": "US"},
    {"name": "Palo Alto Networks", "code": "PANW", "market": "US"},
    {"name": "Coinbase", "code": "COIN", "market": "US"},
    {"name": "MercadoLibre", "code": "MELI", "market": "US"},
    {"name": "Shopify", "code": "SHOP", "market": "US"},
]


def load_stocks():
    global stock_list
    items = []
    try:
        import FinanceDataReader as fdr
        for market_name in ("KOSPI", "KOSDAQ"):
            df = fdr.StockListing(market_name)
            for _, row in df.iterrows():
                change_ratio = row.get("ChagesRatio", 0)
                change_val = row.get("Changes", 0)
                close = row.get("Close", 0)
                items.append({
                    "name": row["Name"],
                    "code": row["Code"],
                    "market": market_name,
                    "change": float(change_ratio) if change_ratio == change_ratio else 0,
                    "changeVal": int(change_val) if change_val == change_val else 0,
                    "close": int(close) if close == close else 0,
                })
    except Exception:
        for s in KR_STOCKS:
            items.append({**s, "change": 0, "changeVal": 0, "close": 0})
    try:
        import FinanceDataReader as fdr
        for market_name in ("NYSE", "NASDAQ", "AMEX"):
            df = fdr.StockListing(market_name)
            for _, row in df.iterrows():
                items.append({
                    "name": row["Name"],
                    "code": row["Symbol"],
                    "market": market_name,
                    "change": 0,
                    "changeVal": 0,
                    "close": 0,
                })
    except Exception:
        for s in US_STOCKS:
            items.append({**s, "change": 0, "changeVal": 0, "close": 0})
    stock_list = items
    print(f"[stockavenue] Loaded {len(stock_list)} stocks (KR: {sum(1 for s in stock_list if s['market'] in ('KOSPI','KOSDAQ'))}, US: {sum(1 for s in stock_list if s['market'] in ('NYSE','NASDAQ','AMEX'))})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_stocks()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("index.html", media_type="text/html")


@app.get("/api/stocks")
async def get_stocks(q: str = ""):
    if not q:
        return []
    q_lower = q.lower()
    results = [
        s for s in stock_list
        if q_lower in s["name"].lower() or q_lower in s["code"].lower()
    ]
    return results[:20]


PERIOD_MAP = {
    "7d": {"days": 10, "yahoo": "5d", "interval": "1d"},
    "1mo": {"days": 45, "yahoo": "1mo", "interval": "1d"},
    "3mo": {"days": 100, "yahoo": "3mo", "interval": "1d"},
    "1y": {"days": 370, "yahoo": "1y", "interval": "1d"},
    "3y": {"days": 1100, "yahoo": "3y", "interval": "1wk"},
    "5y": {"days": 1850, "yahoo": "5y", "interval": "1wk"},
    "10y": {"days": 3700, "yahoo": "10y", "interval": "1mo"},
}


@app.get("/api/chart/{code}")
async def get_chart(code: str, market: str = "", period: str = "1mo"):
    cfg = PERIOD_MAP.get(period, PERIOD_MAP["1mo"])
    candles = []
    try:
        if market in ("KOSPI", "KOSDAQ"):
            import FinanceDataReader as fdr
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=cfg["days"])
            df = fdr.DataReader(code, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            for idx, row in df.iterrows():
                candles.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if "Volume" in row else 0,
                })
        else:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval={cfg['interval']}&range={cfg['yahoo']}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                result = data["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                q = result["indicators"]["quote"][0]
                opens = q.get("open", [])
                highs = q.get("high", [])
                lows = q.get("low", [])
                closes = q.get("close", [])
                volumes = q.get("volume", [])
                from datetime import datetime
                for i in range(len(closes)):
                    if closes[i] is None:
                        continue
                    candles.append({
                        "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d") if i < len(timestamps) else "",
                        "open": float(opens[i]) if opens[i] else float(closes[i]),
                        "high": float(highs[i]) if highs[i] else float(closes[i]),
                        "low": float(lows[i]) if lows[i] else float(closes[i]),
                        "close": float(closes[i]),
                        "volume": int(volumes[i]) if volumes[i] else 0,
                    })
    except Exception:
        pass
    prices = [c["close"] for c in candles]
    dates = [c["date"] for c in candles]
    return {"prices": prices, "dates": dates, "candles": candles}


@app.get("/api/quote/{code}")
async def get_quote(code: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1d&range=1d"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return {"change": 0, "changeVal": 0, "close": 0}
        data = resp.json()
        meta = data["chart"]["result"][0]["meta"]
        prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0)
        current = meta.get("regularMarketPrice", 0)
        if prev_close and current:
            change_val = round(current - prev_close, 2)
            change_pct = round((change_val / prev_close) * 100, 2)
            return {"change": change_pct, "changeVal": change_val, "close": current}
    except Exception:
        pass
    return {"change": 0, "changeVal": 0, "close": 0}


@app.get("/api/earnings/{code}")
async def get_earnings(code: str, market: str = "", name: str = ""):
    from datetime import datetime

    symbol = code
    if market == "KOSPI":
        symbol = f"{code}.KS"
    elif market == "KOSDAQ":
        symbol = f"{code}.KQ"

    result = {"past": [], "upcoming": None}

    # Try Yahoo Finance quoteSummary
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=calendarEvents,earningsHistory"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("quoteSummary", {}).get("result", [{}])[0]

            # Upcoming earnings date
            cal = summary.get("calendarEvents", {}).get("earnings", {})
            earnings_date_list = cal.get("earningsDate", [])
            if earnings_date_list:
                ts = earnings_date_list[0].get("raw", 0)
                if ts:
                    result["upcoming"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

            # Past earnings
            history = summary.get("earningsHistory", {}).get("history", [])
            for h in history[-4:]:
                quarter_raw = h.get("quarter", {}).get("fmt", "")
                date_raw = h.get("quarterDate", {}).get("fmt") or h.get("period", "")
                eps_actual = h.get("epsActual", {}).get("raw")
                eps_estimate = h.get("epsEstimate", {}).get("raw")
                surprise_pct = h.get("surprisePercent", {}).get("raw")
                entry = {
                    "quarter": quarter_raw,
                    "date": date_raw,
                    "epsActual": round(eps_actual, 2) if eps_actual is not None else None,
                    "epsEstimate": round(eps_estimate, 2) if eps_estimate is not None else None,
                    "surprise": round(surprise_pct, 2) if surprise_pct is not None else None,
                }
                result["past"].append(entry)
    except Exception:
        pass

    return result


@app.get("/api/news/{code}")
async def get_news(code: str, name: str = ""):
    is_kr = code.isdigit() and len(code) == 6
    query = (name or code).strip()

    if is_kr:
        rss_url = (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(query)}&hl=ko&gl=KR&ceid=KR:ko"
        )
    else:
        rss_url = (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(query + ' stock')}&hl=en-US&gl=US&ceid=US:en"
        )

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RSS fetch failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        raise HTTPException(status_code=502, detail=f"RSS parse failed: {e}")

    items = root.findall(".//item")[:5]
    if not items:
        return {"summary": "관련 뉴스를 찾지 못했습니다."}

    lines = []
    for it in items:
        title = html.escape((it.findtext("title") or "").strip())
        link = html.escape((it.findtext("link") or "").strip(), quote=True)
        pub = html.escape((it.findtext("pubDate") or "").strip())
        src_el = it.find("source")
        source = html.escape(src_el.text.strip()) if (src_el is not None and src_el.text) else ""
        meta = " · ".join(x for x in [source, pub] if x)
        lines.append(
            f'<div style="margin-bottom:8px;">'
            f'<a href="{link}" target="_blank" rel="noopener">{title}</a>'
            f'<br><small style="color:#888;">{meta}</small></div>'
        )

    return {"summary": "\n".join(lines)}


# --- Keyword Tracker ---

KEYWORD_FILE = os.path.join(os.path.dirname(__file__) or ".", "keyword_tracker.json")
KEYWORD_REFRESH_SECONDS = 3 * 60 * 60  # 3 hours
KEYWORD_MAX_ITEMS = 8
HANGUL_RE = re.compile(r"[가-힣]")


def load_keywords() -> dict:
    if not os.path.exists(KEYWORD_FILE):
        return {}
    try:
        with open(KEYWORD_FILE, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def save_keywords(data: dict) -> None:
    tmp = KEYWORD_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, KEYWORD_FILE)


def normalize_keyword(raw: str) -> str:
    return raw.strip().lstrip("#").strip()


def _pub_timestamp(pub: str) -> float:
    """RFC822 pubDate 문자열 -> 정렬용 epoch초. 누락/파싱 실패 시 맨 아래로(-inf)."""
    if not pub:
        return float("-inf")
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(pub)
    except (TypeError, ValueError):
        return float("-inf")
    return dt.timestamp() if dt else float("-inf")


async def search_google_news(keyword: str) -> list[dict]:
    is_kr = bool(HANGUL_RE.search(keyword))
    if is_kr:
        url = (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        )
    else:
        url = (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(keyword)}&hl=en-US&gl=US&ceid=US:en"
        )
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])
    root = ET.fromstring(resp.text)

    items: list[dict] = []
    for it in root.findall(".//item")[:KEYWORD_MAX_ITEMS]:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("source")
        source = src_el.text.strip() if (src_el is not None and src_el.text) else ""
        if not title or not link:
            continue
        items.append({"title": title, "link": link, "pub": pub, "source": source})
    # 최신 뉴스가 맨 위로 오도록 발행일(pubDate) 내림차순 정렬
    items.sort(key=lambda i: _pub_timestamp(i.get("pub", "")), reverse=True)
    return items


def items_hash(items: list[dict]) -> str:
    joined = "\n".join(sorted(i.get("link", "") for i in items))
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


async def refresh_keyword(keyword: str, store: dict) -> dict:
    entry = store.get(keyword, {})
    prev_hash = entry.get("result_hash", "")
    prev_links = {i.get("link") for i in entry.get("items", [])}
    try:
        items = await search_google_news(keyword)
    except HTTPException as e:
        entry["last_error"] = f"{e.status_code}: {str(e.detail)[:200]}"
        entry["last_fetched_at"] = int(time.time())
        store[keyword] = entry
        return entry
    except Exception as e:
        entry["last_error"] = str(e)[:300]
        entry["last_fetched_at"] = int(time.time())
        store[keyword] = entry
        return entry

    new_hash = items_hash(items)
    changed = new_hash != prev_hash and prev_hash != ""
    for i in items:
        i["is_new"] = i.get("link") not in prev_links if prev_hash else False

    now = int(time.time())
    entry["items"] = items
    entry["result_hash"] = new_hash
    entry["last_fetched_at"] = now
    entry["changed"] = changed
    entry["first_fetch"] = prev_hash == ""
    if changed:
        entry["last_changed_at"] = now
    entry.pop("last_error", None)
    store[keyword] = entry
    return entry


@app.get("/api/keywords")
async def list_keywords():
    store = load_keywords()
    now = int(time.time())
    dirty = False
    for kw, entry in list(store.items()):
        if now - entry.get("last_fetched_at", 0) >= KEYWORD_REFRESH_SECONDS:
            await refresh_keyword(kw, store)
            dirty = True
    if dirty:
        save_keywords(store)
    return {
        "keywords": [
            {"keyword": kw, **store[kw]} for kw in store
        ]
    }


@app.post("/api/keywords")
async def add_keyword(payload: dict):
    keyword = normalize_keyword(payload.get("keyword", ""))
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword 비어있음")
    if len(keyword) > 60:
        raise HTTPException(status_code=400, detail="keyword 60자 초과")
    store = load_keywords()
    if keyword in store:
        raise HTTPException(status_code=409, detail="이미 등록된 키워드")
    await refresh_keyword(keyword, store)
    save_keywords(store)
    return {"keyword": keyword, **store[keyword]}


@app.post("/api/keywords/{keyword}/refresh")
async def force_refresh_keyword(keyword: str):
    keyword = normalize_keyword(keyword)
    store = load_keywords()
    if keyword not in store:
        raise HTTPException(status_code=404, detail="등록되지 않은 키워드")
    await refresh_keyword(keyword, store)
    save_keywords(store)
    return {"keyword": keyword, **store[keyword]}


@app.delete("/api/keywords/{keyword}")
async def delete_keyword(keyword: str):
    keyword = normalize_keyword(keyword)
    store = load_keywords()
    if keyword not in store:
        raise HTTPException(status_code=404, detail="등록되지 않은 키워드")
    del store[keyword]
    save_keywords(store)
    return {"ok": True}


# --- Watchlist ---

WATCHLIST_FILE = os.path.join(os.path.dirname(__file__) or ".", "watchlist.json")


def load_watchlist() -> dict:
    if not os.path.exists(WATCHLIST_FILE):
        return {"categories": []}
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {"categories": []}


def save_watchlist(data: dict) -> None:
    tmp = WATCHLIST_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, WATCHLIST_FILE)


@app.get("/api/watchlist")
async def get_watchlist():
    return load_watchlist()


@app.put("/api/watchlist")
async def put_watchlist(payload: dict):
    cats = payload.get("categories", [])
    if not isinstance(cats, list):
        raise HTTPException(status_code=400, detail="categories는 리스트여야 합니다.")
    # 영속 필드(카테고리명 + 종목 식별자)만 저장 — 가격/차트/뉴스 등 런타임 데이터는 제외
    clean = []
    for c in cats:
        if not isinstance(c, dict):
            continue
        stocks = []
        for s in (c.get("stocks") or []):
            if isinstance(s, dict) and s.get("code"):
                stocks.append({
                    "code": s.get("code"),
                    "market": s.get("market", ""),
                    "name": s.get("name", ""),
                })
        clean.append({"name": str(c.get("name", "")), "stocks": stocks})
    save_watchlist({"categories": clean})
    return {"ok": True, "count": len(clean)}


# --- Screener (US) ---

SCREENER_CACHE_FILE = os.path.join(os.path.dirname(__file__) or ".", "screener_cache.json")
SCREENER_TOP_N = 30
SCREENER_HEADLINE_CONCURRENCY = 5


def load_screener_cache() -> dict:
    if not os.path.exists(SCREENER_CACHE_FILE):
        return {}
    try:
        with open(SCREENER_CACHE_FILE, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def save_screener_cache(data: dict) -> None:
    tmp = SCREENER_CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, SCREENER_CACHE_FILE)


FINVIZ_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FINVIZ_BASE = "https://finviz.com/screener.ashx"
FINVIZ_ROW_RE = re.compile(
    r'<tr class="styled-row[^"]*"[^>]*valign="top"[^>]*>([\s\S]+?)</tr>'
)
FINVIZ_TD_RE = re.compile(r'<td[^>]*>([\s\S]+?)</td>')
FINVIZ_TAG_RE = re.compile(r'<[^>]+>')


def parse_finviz_change(s: str):
    s = s.strip().replace("%", "").replace(",", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_finviz_price(s: str):
    s = s.strip().replace("$", "").replace(",", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


async def scrape_finviz_page(client: httpx.AsyncClient, params: dict) -> list[dict]:
    """Fetch one Finviz screener page (≤20 rows) and parse. Returns list of row dicts."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{FINVIZ_BASE}?{qs}"
    r = await client.get(
        url,
        headers={"User-Agent": FINVIZ_UA, "Referer": "https://finviz.com/"},
        follow_redirects=True,
    )
    if r.status_code != 200:
        return []
    html_text = r.text
    rows = []
    for m in FINVIZ_ROW_RE.finditer(html_text):
        row_html = m.group(1)
        tds = FINVIZ_TD_RE.findall(row_html)
        if len(tds) < 10:
            continue
        cells = [FINVIZ_TAG_RE.sub("", td).strip() for td in tds]
        # Standard v=111 column order:
        # 0:#  1:Ticker  2:Company  3:Sector  4:Industry  5:Country  6:MarketCap  7:P/E  8:Price  9:Change  10:Volume
        rows.append({
            "symbol": cells[1],
            "name": cells[2],
            "sector": cells[3],
            "industry": cells[4],
            "country": cells[5],
            "market_cap": cells[6],
            "close": parse_finviz_price(cells[8]),
            "change_pct": parse_finviz_change(cells[9]),
        })
    return rows


async def fetch_finviz_sorted(client: httpx.AsyncClient, order: str, n: int) -> list[dict]:
    """Fetch up to n rows from Finviz sorted by change column.
    order='-change' for top gainers, order='change' for top losers.
    Uses cap_largeover ($10B+) filter. Pages are 20 rows each."""
    rows: list[dict] = []
    r = 1
    while len(rows) < n:
        params = {"v": "111", "f": "cap_largeover", "o": order, "r": str(r)}
        page = await scrape_finviz_page(client, params)
        if not page:
            break
        rows.extend(page)
        if len(page) < 20:
            break
        r += 20
    valid = [x for x in rows if x.get("symbol")]
    return valid[:n]


async def fetch_top_headline(client: httpx.AsyncClient, name: str) -> dict:
    """Top Google News RSS item for a US stock name. {} on failure."""
    query = (name or "").strip()
    if not query:
        return {}
    url = (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(query + ' stock')}&hl=en-US&gl=US&ceid=US:en"
    )
    try:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return {}
        root = ET.fromstring(r.text)
        first = root.find(".//item")
        if first is None:
            return {}
        return {
            "title": (first.findtext("title") or "").strip(),
            "link": (first.findtext("link") or "").strip(),
        }
    except Exception:
        return {}


async def translate_headlines_ko(headlines: list[str]) -> list[str]:
    """Batch-translate English headlines to Korean. Returns same-length list. Falls back to originals on any failure."""
    if not GEMINI_API_KEY or not headlines:
        return list(headlines)
    numbered = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
    prompt = (
        "아래 영문 주식 뉴스 헤드라인들을 자연스럽고 간결한 한국어로 번역하세요.\n"
        "회사명/티커는 그대로 둡니다. 입력 순서를 그대로 유지하고, JSON 배열로만 응답하세요 (다른 텍스트 금지).\n\n"
        f"입력:\n{numbered}\n\n"
        "출력 형식: [\"번역1\", \"번역2\", ...]"
    )
    text, err = await call_gemini(
        parts=[{"text": prompt}],
        system="당신은 금융 뉴스 번역가입니다. 'Q2 Earnings Beat'은 '2분기 실적 호조', 'price target raised'는 '목표주가 상향' 같이 자연스러운 한국어 표현을 씁니다.",
        max_tokens=4000,
    )
    if err or not text:
        return list(headlines)
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.startswith("```"))
        text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) == len(headlines):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return list(headlines)


async def build_us_screener() -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Source: Finviz screener with cap_largeover ($10B+) filter, sorted by change%
        gainers, losers = await asyncio.gather(
            fetch_finviz_sorted(client, "-change", SCREENER_TOP_N),
            fetch_finviz_sorted(client, "change", SCREENER_TOP_N),
        )

        # Pre-market detection: all changes zero means session hasn't started yet
        all_zero = all((r.get("change_pct") or 0) == 0 for r in gainers + losers)

        # During regular trading, keep only actual gainers (>0) and losers (<0).
        # During pre-market (all_zero), keep all rows since change col resets to 0 — the
        # frontend will show a banner in that case.
        if not all_zero:
            gainers = [r for r in gainers if (r.get("change_pct") or 0) > 0]
            losers = [r for r in losers if (r.get("change_pct") or 0) < 0]

        # Enrich each row with top Google News RSS headline. change_pct comes from Finviz's
        # "Change" column directly (0 during pre-market — the frontend shows a banner).
        sem_news = asyncio.Semaphore(SCREENER_HEADLINE_CONCURRENCY)

        async def enrich(row):
            async with sem_news:
                row["headline"] = await fetch_top_headline(client, row["name"])
            return row

        await asyncio.gather(*[enrich(r) for r in gainers + losers])

    # Batch-translate all 60 headlines in one Gemini call (fallback to original on missing key)
    all_rows = gainers + losers
    raw_titles = [(r.get("headline") or {}).get("title", "") for r in all_rows]
    translated = await translate_headlines_ko(raw_titles)
    for row, ko in zip(all_rows, translated):
        if row.get("headline") and row["headline"].get("title"):
            row["headline"]["title_ko"] = ko

    return {
        "date": time.strftime("%Y-%m-%d"),
        "generated_at": int(time.time()),
        "source": "finviz",
        "filter": "cap_largeover",  # $10B+
        "pre_market": all_zero,
        "gainers": gainers,
        "losers": losers,
    }


@app.get("/api/screener/us")
async def get_us_screener(refresh: bool = False):
    cache = load_screener_cache()
    today = time.strftime("%Y-%m-%d")
    cached = cache.get("us")
    if not refresh and cached and cached.get("date") == today:
        return {**cached, "cached": True}
    result = await build_us_screener()
    cache["us"] = result
    save_screener_cache(cache)
    return {**result, "cached": False}


# --- Trade Data (US Census International Trade API) ---
# 데이터 소스: https://api.census.gov/data/timeseries/intltrade/{imports,exports}/hs
# 키 발급(무료): https://api.census.gov/data/key_signup.html  -> .env 에 CENSUS_API_KEY=...
# 전국가 합계: get= 에 CTY_CODE 를 넣지 않으면 전(全)국가/구·DF 합산 단일행이 월별로 반환됨(공식 User Guide).

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", "")
CENSUS_URLS = {
    "imports": "https://api.census.gov/data/timeseries/intltrade/imports/hs",
    "exports": "https://api.census.gov/data/timeseries/intltrade/exports/hs",
}
# flow 별 변수명: (HS코드 변수, 월 금액 변수, 월 수량1 변수)
CENSUS_VARS = {
    "imports": ("I_COMMODITY", "GEN_VAL_MO", "GEN_QY1_MO"),
    "exports": ("E_COMMODITY", "ALL_VAL_MO", "QTY_1_MO"),
}
TRADE_CACHE_FILE = os.path.join(os.path.dirname(__file__) or ".", "trade_cache.json")
TRADE_CACHE_TTL = 6 * 60 * 60      # 6시간
TRADE_MONTHS = 15                  # 최신월 YoY(=12개월 전 대비) 계산을 위해 충분한 길이

# 추적 품목: HS6 코드 -> 한글 품목명 + 관련 상장기업(티커).
# ※ 품목→관련기업 매핑은 자동 소스가 없어 직접 큐레이션한 시드 데이터입니다(확장 가능).
TRADE_ITEMS = [
    {"hs": "852351", "level": "HS6", "name_ko": "비휘발성 반도체 저장매체(SSD·플래시)",
     "companies": [{"ticker": "005930", "name": "삼성전자"}, {"ticker": "000660", "name": "SK하이닉스"}]},
    {"hs": "854232", "level": "HS6", "name_ko": "메모리 반도체(D램·낸드 등)",
     "companies": [{"ticker": "005930", "name": "삼성전자"}, {"ticker": "000660", "name": "SK하이닉스"}]},
    {"hs": "854231", "level": "HS6", "name_ko": "프로세서·컨트롤러 IC",
     "companies": [{"ticker": "005930", "name": "삼성전자"}]},
    {"hs": "850760", "level": "HS6", "name_ko": "리튬이온 축전지",
     "companies": [{"ticker": "373220", "name": "LG에너지솔루션"}, {"ticker": "006400", "name": "삼성SDI"}, {"ticker": "096770", "name": "SK이노베이션"}]},
    {"hs": "870380", "level": "HS6", "name_ko": "전기차(배터리 전기 승용차)",
     "companies": [{"ticker": "005380", "name": "현대차"}, {"ticker": "000270", "name": "기아"}]},
]


def load_trade_cache() -> dict:
    if not os.path.exists(TRADE_CACHE_FILE):
        return {}
    try:
        with open(TRADE_CACHE_FILE, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def save_trade_cache(data: dict) -> None:
    tmp = TRADE_CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, TRADE_CACHE_FILE)


def _trade_start_month() -> str:
    """TRADE_MONTHS 개월 전의 'YYYY-MM' (Census time=from+ 용)."""
    from datetime import datetime
    now = datetime.now()
    total = (now.year * 12 + (now.month - 1)) - TRADE_MONTHS
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


async def fetch_census_series(flow: str, hs: str, level: str) -> list[dict]:
    """특정 HS 품목의 월별 전(全)국가 합계 시계열을 Census에서 가져온다.
    CTY_CODE 를 요청하지 않으므로 국가/구/DF 가 합산된 월별 단일행이 반환됨."""
    if not CENSUS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="CENSUS_API_KEY가 .env에 없습니다. https://api.census.gov/data/key_signup.html 에서 무료 발급 후 .env에 'CENSUS_API_KEY=...' 추가하세요.",
        )
    code_var, val_var, qty_var = CENSUS_VARS[flow]
    url = (
        f"{CENSUS_URLS[flow]}?get={val_var},{qty_var},UNIT_QY1"
        f"&{code_var}={hs}&COMM_LVL={level}"
        f"&time=from+{_trade_start_month()}"
        f"&key={CENSUS_API_KEY}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, follow_redirects=True)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Census API {r.status_code}: {r.text[:200]}")
    try:
        data = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"Census 응답 파싱 실패: {r.text[:200]}")
    if not isinstance(data, list) or len(data) < 2:
        return []
    idx = {name: i for i, name in enumerate(data[0])}
    if "time" not in idx or val_var not in idx:
        return []
    # 같은 달에 여러 행이 와도 안전하게 합산(전국가 합계 시 보통 월 1행)
    agg: dict = {}
    for row in data[1:]:
        period = row[idx["time"]]
        a = agg.setdefault(period, {"value": None, "qty": None, "unit": ""})
        v = _to_float(row[idx[val_var]])
        q = _to_float(row[idx[qty_var]]) if qty_var in idx else None
        if v is not None:
            a["value"] = (a["value"] or 0.0) + v
        if q is not None:
            a["qty"] = (a["qty"] or 0.0) + q
        if "UNIT_QY1" in idx and not a["unit"]:
            a["unit"] = row[idx["UNIT_QY1"]]
    return [{"period": p, **agg[p]} for p in sorted(agg)]


def compute_trade_metrics(series: list[dict]) -> list[dict]:
    """월별 YoY%(12개월 전 대비), MoM%(직전월 대비), 단가(=금액/수량) 계산."""
    by_period = {s["period"]: s for s in series}
    out = []
    for i, s in enumerate(series):
        val = s["value"]
        prev = series[i - 1]["value"] if i >= 1 else None
        y, m = s["period"].split("-")
        yoy_base = by_period.get(f"{int(y) - 1}-{m}", {}).get("value")
        out.append({
            "period": s["period"],
            "value_usd": val,
            "value_musd": (val / 1e6) if val is not None else None,
            "qty": s["qty"],
            "unit": s["unit"],
            "unit_price": (val / s["qty"]) if (val is not None and s["qty"]) else None,
            "mom": ((val - prev) / prev * 100.0) if (val is not None and prev) else None,
            "yoy": ((val - yoy_base) / yoy_base * 100.0) if (val is not None and yoy_base) else None,
        })
    return out


async def build_trade_item(item: dict, flow: str) -> dict:
    # 개별 품목 실패가 전체 응답을 깨뜨리지 않도록 흡수(전체 키 누락은 build_trade_data에서 일괄 처리)
    error = None
    try:
        metrics = compute_trade_metrics(await fetch_census_series(flow, item["hs"], item["level"]))
    except HTTPException as e:
        metrics, error = [], str(e.detail)[:200]
    except Exception as e:
        metrics, error = [], str(e)[:200]
    return {
        "hs": item["hs"],
        "level": item["level"],
        "name_ko": item["name_ko"],
        "companies": item["companies"],
        "flow": flow,
        "series": metrics,
        "latest": metrics[-1] if metrics else None,
        "error": error,
    }


async def build_trade_data(flow: str) -> dict:
    # 키 자체가 없으면 품목별 에러 5개 대신 명확한 안내를 한 번에 반환
    if not CENSUS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="CENSUS_API_KEY가 .env에 없습니다. https://api.census.gov/data/key_signup.html 에서 무료 발급 후 .env에 'CENSUS_API_KEY=...' 추가하세요.",
        )
    items = await asyncio.gather(*[build_trade_item(it, flow) for it in TRADE_ITEMS])
    return {
        "flow": flow,
        "country": "미국",
        "source": "US Census International Trade API",
        "generated_at": int(time.time()),
        "items": list(items),
    }


@app.get("/api/trade/{flow}")
async def get_trade(flow: str, refresh: bool = False):
    if flow not in CENSUS_URLS:
        raise HTTPException(status_code=400, detail="flow는 imports 또는 exports 여야 합니다.")
    cache = load_trade_cache()
    now = int(time.time())
    cached = cache.get(flow)
    if not refresh and cached and (now - cached.get("generated_at", 0) < TRADE_CACHE_TTL):
        return {**cached, "cached": True}
    result = await build_trade_data(flow)
    cache[flow] = result
    save_trade_cache(cache)
    return {**result, "cached": False}


# --- Trade momentum screener (전체 HS 품목 중 MoM·YoY 급증 Top N) ---

TRADE_ITEM_MAP = {it["hs"]: it for it in TRADE_ITEMS}   # HS6 -> 한글명/관련기업 enrich
SCREENER_MIN_VALUE_USD = 10_000_000   # 소액 품목 % 폭주 방지: 최신월 1천만 달러 이상만 후보
SCREENER_MOM_MIN = 20.0
SCREENER_YOY_MIN = 20.0
SCREENER_TOP_N = 20


def _current_month() -> str:
    from datetime import datetime
    now = datetime.now()
    return f"{now.year:04d}-{now.month:02d}"


def _shift_month(ym: str, delta: int) -> str:
    """'YYYY-MM' 를 delta 개월 이동."""
    y, m = ym.split("-")
    total = int(y) * 12 + (int(m) - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


async def fetch_census_all_hs(flow: str, month: str) -> dict:
    """한 달치 전체 HS6 집계 -> {hs: {'value': float, 'name_en': str}} (CTY_CODE 미지정=전국가 합계)."""
    code_var, val_var, _ = CENSUS_VARS[flow]
    sdesc_var = code_var + "_SDESC"
    url = (
        f"{CENSUS_URLS[flow]}?get={code_var},{sdesc_var},{val_var}"
        f"&COMM_LVL=HS6&time={month}&key={CENSUS_API_KEY}"
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url, follow_redirects=True)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Census API {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not isinstance(data, list) or len(data) < 2:
        return {}
    idx = {n: i for i, n in enumerate(data[0])}
    out: dict = {}
    for row in data[1:]:
        hs = row[idx[code_var]]
        v = _to_float(row[idx[val_var]])
        if v is None:
            continue
        cur = out.setdefault(hs, {"value": 0.0, "name_en": row[idx[sdesc_var]] if sdesc_var in idx else ""})
        cur["value"] += v
    return out


async def _latest_trade_month(flow: str) -> str:
    """가장 최근 사용 가능한 월(YYYY-MM). 최근 6개월 총액 범위에서 max(time)."""
    val_var = CENSUS_VARS[flow][1]
    url = f"{CENSUS_URLS[flow]}?get={val_var}&time=from+{_shift_month(_current_month(), -6)}&key={CENSUS_API_KEY}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, follow_redirects=True)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Census API {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not isinstance(data, list) or len(data) < 2:
        return _shift_month(_current_month(), -2)
    idx = {n: i for i, n in enumerate(data[0])}
    months = [row[idx["time"]] for row in data[1:] if "time" in idx]
    return max(months) if months else _shift_month(_current_month(), -2)


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_TRANSLATE_MODEL = "claude-haiku-4-5-20251001"


async def translate_terms_ko(terms: list[str]) -> list[str]:
    """영문 HS 품목명을 한국어로 번역(ANTHROPIC_API_KEY 사용). 동일 길이 리스트, 실패/키없음 시 원문 유지."""
    if not ANTHROPIC_API_KEY or not terms:
        return list(terms)
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(terms))
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_TRANSLATE_MODEL,
                    "max_tokens": 2000,
                    "system": "당신은 미국 무역통계(HS코드) 품목 설명을 한국어로 옮기는 전문 번역가입니다. 약어(ADP=자동자료처리, NESOI=따로 분류 안 된 것 등)는 자연스럽게 풀고 간결한 품목명으로 번역합니다. 다른 텍스트 없이, 입력 순서를 유지한 한국어 번역만 담은 JSON 배열로 응답하세요.",
                    "messages": [{"role": "user", "content": numbered}],
                },
            )
        if r.status_code != 200:
            return list(terms)
        text = ((r.json().get("content") or [{}])[0].get("text") or "").strip()
    except Exception:
        return list(terms)
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.startswith("```")).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) == len(terms):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return list(terms)


async def build_trade_screener(flow: str) -> dict:
    if not CENSUS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="CENSUS_API_KEY가 .env에 없습니다. https://api.census.gov/data/key_signup.html 에서 무료 발급 후 .env에 'CENSUS_API_KEY=...' 추가하세요.",
        )
    latest = await _latest_trade_month(flow)
    prev_m, yago_m = _shift_month(latest, -1), _shift_month(latest, -12)
    cur_map, prev_map, yago_map = await asyncio.gather(
        fetch_census_all_hs(flow, latest),
        fetch_census_all_hs(flow, prev_m),
        fetch_census_all_hs(flow, yago_m),
    )
    items = []
    for hs, info in cur_map.items():
        val = info["value"]
        if val < SCREENER_MIN_VALUE_USD:
            continue
        p = prev_map.get(hs, {}).get("value")
        ya = yago_map.get(hs, {}).get("value")
        if not p or not ya:          # 직전월/전년동월 데이터 없거나 0이면 제외
            continue
        mom = (val - p) / p * 100.0
        yoy = (val - ya) / ya * 100.0
        if mom < SCREENER_MOM_MIN or yoy < SCREENER_YOY_MIN:
            continue
        enrich = TRADE_ITEM_MAP.get(hs)
        items.append({
            "hs": hs,
            "name_en": info["name_en"],
            "name_ko": enrich["name_ko"] if enrich else None,
            "companies": enrich["companies"] if enrich else [],
            "period": latest,
            "value_musd": val / 1e6,
            "mom": mom,
            "yoy": yoy,
        })
    items.sort(key=lambda x: x["value_musd"], reverse=True)   # 금액 상위순
    items = items[:SCREENER_TOP_N]
    # 큐레이션 한글명이 없는 품목은 영문명을 한국어로 자동 번역(Top N에 대해서만 1회 배치)
    need = [i for i, it in enumerate(items) if not it["name_ko"]]
    if need:
        ko = await translate_terms_ko([items[i]["name_en"] for i in need])
        for k, i in enumerate(need):
            if k < len(ko) and ko[k]:
                items[i]["name_ko"] = ko[k]
    return {
        "flow": flow,
        "country": "미국",
        "month": latest,
        "criteria": f"MoM≥+{int(SCREENER_MOM_MIN)}% & YoY≥+{int(SCREENER_YOY_MIN)}% · 최신월 ${int(SCREENER_MIN_VALUE_USD / 1e6)}M+ · 금액 상위 {SCREENER_TOP_N}",
        "source": "US Census International Trade API",
        "generated_at": int(time.time()),
        "count": len(items),
        "items": items,
    }


# --- Korea Customs (관세청) trade screener — data.go.kr Itemtrade (한국 수출/수입) ---
# 데이터 소스: http://apis.data.go.kr/1220000/Itemtrade/getItemtradeList (데이터셋 15101609)
# hsSgn 생략 시 해당월 전체 10자리 HSK 품목(약 9.6천개)이 단일 응답으로 옴. 총계 행(hsCode='-')은 제외.

KCS_API_KEY = os.getenv("KCS_API_KEY", "")
KCS_URL = "http://apis.data.go.kr/1220000/Itemtrade/getItemtradeList"
KCS_FLOWS = {"kr-exports": "수출", "kr-imports": "수입"}
KCS_MIN_VALUE_USD = 5_000_000   # 소액 품목 % 폭주 방지 (한국은 단일국 기준이라 미국보다 낮게)


def _no_key_kcs():
    raise HTTPException(
        status_code=503,
        detail="KCS_API_KEY가 .env에 없습니다. https://www.data.go.kr/data/15101609/openapi.do 에서 활용신청 후 .env에 'KCS_API_KEY=...' 추가하세요.",
    )


async def fetch_kcs_month(month: str) -> dict:
    """한 달치 전체 HSK(10자리) 실적 -> {hsCode: {name, exp, expWgt, imp, impWgt}}. month='YYYYMM'."""
    if not KCS_API_KEY:
        _no_key_kcs()
    url = f"{KCS_URL}?serviceKey={KCS_API_KEY}&strtYymm={month}&endYymm={month}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"관세청 API {r.status_code}: {r.text[:200]}")
    try:
        root = ET.fromstring(r.text)
    except Exception:
        raise HTTPException(status_code=502, detail=f"관세청 XML 파싱 실패: {r.text[:200]}")
    out: dict = {}
    for item in root.findall(".//item"):
        hs = (item.findtext("hsCode") or "").strip()
        if not hs or hs == "-":          # 총계 행 제외
            continue
        out[hs] = {
            "name": (item.findtext("statKor") or "").strip(),
            "exp": _to_float(item.findtext("expDlr")),
            "expWgt": _to_float(item.findtext("expWgt")),
            "imp": _to_float(item.findtext("impDlr")),
            "impWgt": _to_float(item.findtext("impWgt")),
        }
    return out


async def _kcs_latest_month() -> str:
    """가장 최근 가용월 'YYYYMM'. 신차(8703801000)의 최근 범위에서 max(year)."""
    if not KCS_API_KEY:
        _no_key_kcs()
    start = _shift_month(_current_month(), -6).replace("-", "")
    end = _current_month().replace("-", "")
    url = f"{KCS_URL}?serviceKey={KCS_API_KEY}&strtYymm={start}&endYymm={end}&hsSgn=8703801000"
    months = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
        if r.status_code == 200:
            for it in ET.fromstring(r.text).findall(".//item"):
                y = (it.findtext("year") or "").strip()   # 'YYYY.MM'
                if "." in y:
                    months.append(y.replace(".", ""))
    except Exception:
        pass
    return max(months) if months else _shift_month(_current_month(), -2).replace("-", "")


async def build_kcs_screener(flow: str) -> dict:
    field, wfield = ("exp", "expWgt") if flow == "kr-exports" else ("imp", "impWgt")
    latest = await _kcs_latest_month()                       # YYYYMM
    latest_dash = f"{latest[:4]}-{latest[4:]}"
    prev_m = _shift_month(latest_dash, -1).replace("-", "")
    yago_m = _shift_month(latest_dash, -12).replace("-", "")
    cur_map, prev_map, yago_map = await asyncio.gather(
        fetch_kcs_month(latest), fetch_kcs_month(prev_m), fetch_kcs_month(yago_m),
    )

    def agg6(month_map):
        # 10자리 HSK -> 6자리로 합산. 대표 품목명은 '기타'가 아닌 최대 자식 우선.
        out = {}
        for hs, info in month_map.items():
            h6 = hs[:6]
            a = out.setdefault(h6, {"exp": 0.0, "imp": 0.0, "expWgt": 0.0, "impWgt": 0.0, "_best": (-1.0, ""), "_named": (-1.0, "")})
            for k in ("exp", "imp", "expWgt", "impWgt"):
                v = info.get(k)
                if v:
                    a[k] += v
            fv = info.get(field) or 0.0
            nm = info.get("name") or ""
            if fv > a["_best"][0]:
                a["_best"] = (fv, nm)
            if nm and nm != "기타" and fv > a["_named"][0]:
                a["_named"] = (fv, nm)
        return out

    cur6, prev6, yago6 = agg6(cur_map), agg6(prev_map), agg6(yago_map)
    items = []
    for h6, info in cur6.items():
        val = info[field]
        if val < KCS_MIN_VALUE_USD:
            continue
        p = (prev6.get(h6) or {}).get(field)
        ya = (yago6.get(h6) or {}).get(field)
        if not p or not ya:
            continue
        mom = (val - p) / p * 100.0
        yoy = (val - ya) / ya * 100.0
        if mom < SCREENER_MOM_MIN or yoy < SCREENER_YOY_MIN:
            continue
        wgt = info[wfield]
        enrich = TRADE_ITEM_MAP.get(h6)                      # 6자리로 관련기업 매핑
        name = (enrich["name_ko"] if enrich else None) or (info["_named"][1] or info["_best"][1] or None)
        items.append({
            "hs": h6,
            "name_en": None,
            "name_ko": name,
            "companies": enrich["companies"] if enrich else [],
            "period": latest_dash,
            "value_musd": val / 1e6,
            "unit_price": (val / wgt) if (wgt and wgt > 0) else None,
            "mom": mom,
            "yoy": yoy,
        })
    items.sort(key=lambda x: x["value_musd"], reverse=True)
    items = items[:SCREENER_TOP_N]
    return {
        "flow": flow,
        "country": "한국",
        "month": latest_dash,
        "criteria": f"MoM≥+{int(SCREENER_MOM_MIN)}% & YoY≥+{int(SCREENER_YOY_MIN)}% · 최신월 ${int(KCS_MIN_VALUE_USD / 1e6)}M+ · {KCS_FLOWS[flow]} 금액 상위 {SCREENER_TOP_N} (HS 6자리 집계)",
        "source": "관세청 수출입무역통계 (data.go.kr)",
        "generated_at": int(time.time()),
        "count": len(items),
        "items": items,
    }


async def fetch_kcs_series(flow: str, hs: str) -> list:
    """차트용 단일 HSK 품목의 월별 시계열."""
    if not KCS_API_KEY:
        _no_key_kcs()
    val_tag, wgt_tag = ("expDlr", "expWgt") if flow == "kr-exports" else ("impDlr", "impWgt")
    # 관세청은 조회기간 1년 이내 제약 → 최근 12개월 창으로 제한
    start = _shift_month(_current_month(), -11).replace("-", "")
    end = _current_month().replace("-", "")
    url = f"{KCS_URL}?serviceKey={KCS_API_KEY}&strtYymm={start}&endYymm={end}&hsSgn={hs}"
    async with httpx.AsyncClient(timeout=40.0) as client:
        r = await client.get(url)
    if r.status_code != 200:
        return []
    try:
        root = ET.fromstring(r.text)
    except Exception:
        return []
    # 6자리 코드 조회 시 월별로 여러 10자리 자식이 오므로 월별 합산
    agg = {}
    for it in root.findall(".//item"):
        y = (it.findtext("year") or "").strip()
        hc = (it.findtext("hsCode") or "").strip()
        if "." not in y or hc == "-":    # 총계 행 제외
            continue
        period = y.replace(".", "-")
        a = agg.setdefault(period, {"value": 0.0, "qty": 0.0, "hasv": False})
        v = _to_float(it.findtext(val_tag))
        q = _to_float(it.findtext(wgt_tag))
        if v is not None:
            a["value"] += v
            a["hasv"] = True
        if q is not None:
            a["qty"] += q
    rows = [{"period": p, "value": agg[p]["value"] if agg[p]["hasv"] else None, "qty": agg[p]["qty"], "unit": "kg"}
            for p in sorted(agg)]
    return compute_trade_metrics(rows)


@app.get("/api/trade/screener/{flow}")
async def get_trade_screener(flow: str, refresh: bool = False):
    if flow in CENSUS_URLS:
        builder = build_trade_screener
    elif flow in KCS_FLOWS:
        builder = build_kcs_screener
    else:
        raise HTTPException(status_code=400, detail="flow는 imports/exports/kr-exports/kr-imports 중 하나여야 합니다.")
    cache = load_trade_cache()
    now = int(time.time())
    ck = f"screener:{flow}"
    cached = cache.get(ck)
    if not refresh and cached and (now - cached.get("generated_at", 0) < TRADE_CACHE_TTL):
        return {**cached, "cached": True}
    result = await builder(flow)
    cache[ck] = result
    save_trade_cache(cache)
    return {**result, "cached": False}


@app.get("/api/trade/series/{flow}/{hs}")
async def get_trade_series(flow: str, hs: str):
    """차트용 단일 품목의 월별 시계열."""
    cache = load_trade_cache()
    now = int(time.time())
    ck = f"series:{flow}:{hs}"
    cached = cache.get(ck)
    if cached and (now - cached.get("generated_at", 0) < TRADE_CACHE_TTL):
        return {**cached, "cached": True}
    if flow in CENSUS_URLS:
        series = compute_trade_metrics(await fetch_census_series(flow, hs, "HS6"))
        enrich = TRADE_ITEM_MAP.get(hs)
    elif flow in KCS_FLOWS:
        series = await fetch_kcs_series(flow, hs)
        enrich = TRADE_ITEM_MAP.get(hs[:6])
    else:
        raise HTTPException(status_code=400, detail="flow가 올바르지 않습니다.")
    result = {
        "flow": flow,
        "hs": hs,
        "name_ko": enrich["name_ko"] if enrich else None,
        "series": series,
        "generated_at": now,
    }
    cache[ck] = result
    save_trade_cache(cache)
    return {**result, "cached": False}


# --- Paper Maker ---

UPLOAD_DIR = os.path.join(os.path.dirname(__file__) or ".", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PAGES_PER_CHUNK = 10


@app.post("/api/papermaker/upload")
async def papermaker_upload(files: List[UploadFile] = File(...)):
    saved = []
    for f in files:
        content = await f.read()
        path = os.path.join(UPLOAD_DIR, f.filename)
        with open(path, "wb") as fp:
            fp.write(content)
        saved.append({"name": f.filename, "size": len(content), "path": path})
    return {"files": saved}


def split_pdf_to_chunks(pdf_path: str) -> list[str]:
    """Split a PDF into chunks of PAGES_PER_CHUNK pages. Returns list of chunk file paths."""
    from PyPDF2 import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    if total_pages <= PAGES_PER_CHUNK:
        return [pdf_path]

    chunk_paths = []
    for start in range(0, total_pages, PAGES_PER_CHUNK):
        end = min(start + PAGES_PER_CHUNK, total_pages)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        chunk_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_p{start+1}-{end}.pdf"
        chunk_path = os.path.join(UPLOAD_DIR, chunk_name)
        with open(chunk_path, "wb") as fp:
            writer.write(fp)
        chunk_paths.append(chunk_path)

    return chunk_paths


async def call_gemini(parts, system="", max_tokens=4000):
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2,
        },
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"content-type": "application/json"},
            json=payload,
        )
    if resp.status_code != 200:
        return None, f"Gemini API 에러 ({resp.status_code}): {resp.text[:300]}"
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return None, f"Gemini 응답 빈 candidates: {str(data)[:300]}"
    resp_parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(p.get("text", "") for p in resp_parts if p.get("text"))
    if not text:
        finish = candidates[0].get("finishReason", "")
        return None, f"Gemini 빈 텍스트 응답 (finishReason={finish})"
    return text, None


async def extract_chunk_data(chunk_path: str, chunk_label: str, company_name: str, company_code: str):
    """Send a single PDF chunk to Gemini and extract all financial data verbatim."""
    with open(chunk_path, "rb") as fp:
        pdf_bytes = fp.read()

    content_blocks = [
        {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": base64.b64encode(pdf_bytes).decode(),
            },
        },
        {
            "text": f"""위 문서는 {company_name}({company_code})에 관한 공시/리포트의 일부({chunk_label})입니다.

이 페이지에 있는 모든 재무 수치와 텍스트 정보를 빠짐없이 그대로 옮겨 적으세요.

## 추출 규칙 (반드시 준수):
- 숫자는 문서에 적힌 그대로 옮기세요. 계산하거나 추정하지 마세요.
- 단위도 문서에 적힌 그대로 명시하세요 (백만원, 억원 등).
- 표가 있으면 행/열 구조를 그대로 텍스트로 재현하세요.
- 빈 칸이면 빈 칸이라고 표시하세요.
- 이 페이지에 해당 정보가 없으면 "해당 없음"이라고만 쓰세요.

## 추출 대상:
1. 손익계산서 (매출액, 매출원가, 매출총이익, 판관비, 영업이익, 당기순이익, 지배주주순이익)
2. 비용의 성격별 분류 (원재료비, 인건비, 감가상각비 등)
3. 재무상태표 주요 항목
4. 투자의견, 목표주가, 사업 분석 텍스트
5. 기타 수치 데이터 (세그먼트별 매출, 수주잔고, 가이던스 등)""",
        },
    ]

    result, err = await call_gemini(
        parts=content_blocks,
        system="당신은 문서 데이터 전사(transcription) 전문가입니다. 문서에 적힌 숫자와 텍스트를 한 글자도 빠뜨리지 않고 정확히 옮겨 적는 것이 당신의 유일한 임무입니다. 절대로 추정하거나 계산하지 마세요. 문서에 없는 내용을 만들어내지 마세요.",
        max_tokens=8000,
    )
    return result if not err else None


async def extract_non_pdf_data(fpath: str, fname: str, company_name: str, company_code: str):
    """Handle non-PDF files (images, spreadsheets, text)."""
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    content_blocks = []

    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        with open(fpath, "rb") as fp:
            img_bytes = fp.read()
        media_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
        content_blocks.append({
            "inline_data": {"mime_type": media_map.get(ext, "image/png"), "data": base64.b64encode(img_bytes).decode()},
        })
    elif ext in ("xlsx", "xls", "csv"):
        text = extract_spreadsheet_text(fpath, ext)
        content_blocks.append({"text": f"[파일: {fname}]\n{text}"})
    else:
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                text = fp.read()[:80000]
            content_blocks.append({"text": f"[파일: {fname}]\n{text}"})
        except Exception:
            return None

    content_blocks.append({
        "text": f"""위 파일({fname})은 {company_name}({company_code})에 관한 자료입니다.
모든 재무 수치와 텍스트를 문서에 적힌 그대로 빠짐없이 옮겨 적으세요.
숫자를 계산하거나 추정하지 마세요. 원문 그대로 전사하세요.""",
    })

    result, err = await call_gemini(
        parts=content_blocks,
        system="당신은 문서 데이터 전사 전문가입니다. 문서에 적힌 내용을 정확히 옮기는 것이 임무입니다.",
        max_tokens=8000,
    )
    return result if not err else None


CONCURRENCY_LIMIT = 3


@app.post("/api/papermaker/generate")
async def papermaker_generate(
    company_name: str = Form(...),
    company_code: str = Form(""),
    user_prompt: str = Form(""),
    filenames: str = Form(""),
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")

    file_list = [f.strip() for f in filenames.split(",") if f.strip()]

    valid_files = []
    for fname in file_list:
        fpath = os.path.join(UPLOAD_DIR, fname)
        if os.path.exists(fpath):
            valid_files.append((fpath, fname))

    if not valid_files:
        return {"error": "유효한 파일이 없습니다."}

    # Build all tasks (PDF chunks + non-PDF files)
    tasks_info = []
    temp_chunks = []
    for fpath, fname in valid_files:
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if ext == "pdf":
            chunk_paths = split_pdf_to_chunks(fpath)
            for i, chunk_path in enumerate(chunk_paths):
                label = f"{fname} (p.{i*PAGES_PER_CHUNK+1}-{min((i+1)*PAGES_PER_CHUNK, 9999)})"
                tasks_info.append(("pdf", chunk_path, label))
                if chunk_path != fpath:
                    temp_chunks.append(chunk_path)
        else:
            tasks_info.append(("other", fpath, fname))

    total = len(tasks_info)
    progress = {"done": 0}

    async def stream():
        sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

        yield f"data: {json.dumps({'type': 'progress', 'total': total, 'done': 0, 'msg': f'총 {total}개 청크 추출 시작...'})}\n\n"

        async def run_task(info):
            kind, path, label = info
            async with sem:
                if kind == "pdf":
                    result = await extract_chunk_data(path, label, company_name, company_code)
                else:
                    result = await extract_non_pdf_data(path, label, company_name, company_code)
                progress["done"] += 1
                return (label, result)

        gathered = await asyncio.gather(*[run_task(t) for t in tasks_info], return_exceptions=True)

        for cp in temp_chunks:
            try:
                os.remove(cp)
            except Exception:
                pass

        extractions = []
        for item in gathered:
            if isinstance(item, Exception):
                continue
            label, result = item
            if result and "해당 없음" not in result[:20]:
                extractions.append(f"=== {label} ===\n{result}")

        yield f"data: {json.dumps({'type': 'progress', 'total': total, 'done': total, 'msg': f'{len(extractions)}/{total} 청크 추출 완료. 종합 분석 중...'})}\n\n"

        if not extractions:
            yield f"data: {json.dumps({'type': 'error', 'error': '파일에서 데이터를 추출하지 못했습니다.'})}\n\n"
            return

        # === Step 2: Consolidate ===
        combined = "\n\n".join(extractions)
        if len(combined) > 180000:
            combined = combined[:180000]

        final_system = f"""당신은 투자 리서치 분석가입니다. 아래는 {company_name}({company_code})에 관한 문서에서 페이지별로 전사한 원본 데이터입니다.

## 핵심 규칙:
- 전사 데이터에 있는 숫자만 사용. 없는 숫자는 절대 추정/생성하지 말 것.
- 같은 항목이 여러 번 등장하면 가장 상세한 출처의 수치 사용.
- 단위 변환: 백만원 → 억원 (÷100), 십억원 → 억원 (×10), 조원 → 억원 (×10000)
- GPM(%) = (매출액-매출원가)/매출액×100, 소수점 첫째자리까지
- OPM(%) = 영업이익/매출액×100, 소수점 첫째자리까지
- 모든 %는 소수점 첫째자리까지 표기 (예: 23.4%)
- 데이터가 없는 항목은 반드시 null

## 출력 형식 (JSON만 출력, 설명 없이):
```json
{{
  "valuation": {{
    "quarterly": [
      {{"period": "1Q23", "revenue": 숫자, "cogs": 숫자, "gpm": 숫자, "sga": 숫자, "op": 숫자, "opm": 숫자, "net_income": 숫자, "controlling_income": 숫자}}
    ],
    "annual": [
      {{"period": "2023", "revenue": 숫자, "cogs": 숫자, "gpm": 숫자, "sga": 숫자, "op": 숫자, "opm": 숫자, "net_income": 숫자, "controlling_income": 숫자}}
    ],
    "cost_breakdown_quarterly": [
      {{"period": "1Q23", "raw_materials": 숫자, "labor": 숫자, "depreciation": 숫자, "others": 숫자}}
    ],
    "cost_breakdown_annual": [
      {{"period": "2023", "raw_materials": 숫자, "labor": 숫자, "depreciation": 숫자, "others": 숫자}}
    ]
  }},
  "report": {{
    "overview": {{
      "bm_summary": "회사 BM을 30자 이내로 설명",
      "segment_mix": [{{"name": "사업부명", "ratio": 숫자}}],
      "region_mix": [{{"name": "지역명", "ratio": 숫자}}],
      "mix_quarter": "가장 최근 분기명 (예: 4Q25)"
    }},
    "past_annual": [
      {{"year": "23'", "revenue": 숫자, "op": 숫자, "opm": 숫자}},
      {{"year": "24'", "revenue": 숫자, "op": 숫자, "opm": 숫자}},
      {{"year": "25'", "revenue": 숫자, "op": 숫자, "opm": 숫자}}
    ],
    "latest_quarter": {{
      "current": {{"period": "4Q25", "revenue": 숫자, "op": 숫자, "opm": 숫자}},
      "prev_quarter": {{"period": "3Q25", "revenue": 숫자, "op": 숫자, "opm": 숫자}},
      "yoy_quarter": {{"period": "4Q24", "revenue": 숫자, "op": 숫자, "opm": 숫자}}
    }},
    "segments": [
      {{
        "name": "사업부명",
        "revenue_ratio": 숫자,
        "overview": "30자 이내 개요",
        "quarterly_revenue": [
          {{"year": "23'", "q1": 숫자, "q2": 숫자, "q3": 숫자, "q4": 숫자, "annual": 숫자}},
          {{"year": "24'", "q1": 숫자, "q2": 숫자, "q3": 숫자, "q4": 숫자, "annual": 숫자}},
          {{"year": "25'", "q1": 숫자, "q2": 숫자, "q3": 숫자, "q4": 숫자, "annual": 숫자}}
        ],
        "key_changes": "연간실적에서의 매출 및 영업이익 주요변동 및 특이사항",
        "outlook": "해당 사업부 전망에 대해 자세히 설명"
      }}
    ],
    "profitability": "사업부별 GPM, OPM, 전사 타겟마진 등",
    "cost_structure": {{
      "note": "회사 고유/특이한 비용구조 (50자 이내, 없으면 null)",
      "by_nature": "인건비 xx.x% + 감가상각비 xx.x% + 원재료비 xx.x% + 기타 xx.x%",
      "by_variability": "변동비 xx.x% + 고정비 xx.x%"
    }},
    "outlook": {{
      "next_quarter": "다음 분기 실적 예상 (매출/영업이익 규모, 근거)",
      "annual_2026e": "2026E 전망 (YoY 매출/영업이익 성장률, 근거)"
    }}
  }}
}}
```

## 주의사항:
- segments는 문서에서 확인되는 모든 사업부를 각각 작성
- quarterly_revenue의 각 연도에 1Q~4Q 분기별 매출액과 연간 매출액 기입
- past_annual은 가장 최근 3개년
- latest_quarter의 current는 가장 최근 분기, prev_quarter는 직전 분기, yoy_quarter는 전년 동기
- 비용구조의 by_nature는 전체 비용 100% 기준 성격별 비중
- 모든 금액은 억원 단위"""

        if user_prompt:
            final_system += f"\n\n추가 지시사항: {user_prompt}"

        full_text, err = await call_gemini(
            parts=[{"text": f"아래 전사 데이터를 종합하여 구조화된 JSON을 생성해주세요. 전사 데이터에 없는 수치는 절대 만들어내지 마세요.\n\n{combined}"}],
            system=final_system,
            max_tokens=16000,
        )

        if err:
            yield f"data: {json.dumps({'type': 'error', 'error': err})}\n\n"
            return

        try:
            json_start = full_text.find("{")
            json_end = full_text.rfind("}") + 1
            parsed = json.loads(full_text[json_start:json_end])
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'error': 'JSON 파싱 실패', 'raw': full_text[:2000]})}\n\n"
            return

        excel_path = generate_excel(parsed, company_name, company_code)
        filename = os.path.basename(excel_path)
        yield f"data: {json.dumps({'type': 'done', 'filename': filename, 'download': f'/api/papermaker/download/{filename}'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/papermaker/download/{filename}")
async def papermaker_download(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def extract_pdf_text(path: str) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:50]:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
                for table in page.extract_tables():
                    for row in table:
                        text_parts.append("\t".join(str(c) if c else "" for c in row))
        return "\n".join(text_parts)[:40000]
    except Exception as e:
        return f"[PDF 텍스트 추출 실패: {e}]"


def extract_spreadsheet_text(path: str, ext: str) -> str:
    try:
        if ext == "csv":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()[:30000]
        else:
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True, data_only=True)
            lines = []
            for sheet in wb.sheetnames[:3]:
                ws = wb[sheet]
                lines.append(f"--- Sheet: {sheet} ---")
                for row in ws.iter_rows(max_row=200, values_only=True):
                    lines.append("\t".join(str(c) if c is not None else "" for c in row))
            return "\n".join(lines)[:30000]
    except Exception as e:
        return f"[파일 읽기 실패: {e}]"


def generate_excel(data: dict, company_name: str, company_code: str) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    # Shared styles
    title_font = Font(name="맑은 고딕", bold=True, size=14, color="C8102E")
    header_font = Font(name="맑은 고딕", bold=True, size=11)
    header_fill = PatternFill(start_color="003087", end_color="003087", fill_type="solid")
    header_font_white = Font(name="맑은 고딕", bold=True, size=11, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    pct_fmt = '0.0'
    num_fmt = '#,##0'
    normal_font = Font(name="맑은 고딕", size=10)
    bold_font = Font(name="맑은 고딕", bold=True, size=10)
    star_font = Font(name="맑은 고딕", bold=True, size=11, color="003087")
    star_fill = PatternFill(start_color="E8EDF5", end_color="E8EDF5", fill_type="solid")
    mid_font = Font(name="맑은 고딕", bold=True, size=10, color="333333")

    def write_val_row(ws, row, values, is_pct_cols=None):
        if is_pct_cols is None:
            is_pct_cols = set()
        for col, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=v)
            cell.border = thin_border
            cell.font = normal_font
            if col > 1 and v is not None and isinstance(v, (int, float)):
                cell.number_format = pct_fmt if col in is_pct_cols else num_fmt
                cell.alignment = Alignment(horizontal="right")

    # ==================== Sheet 1: Valuation ====================
    ws1 = wb.active
    ws1.title = "Valuation"

    ws1["A1"] = f"{company_name} ({company_code}) - Valuation"
    ws1["A1"].font = title_font

    valuation = data.get("valuation", {})

    # --- 분기 실적 ---
    row = 3
    ws1.cell(row=row, column=1, value="분기 실적 (억원)").font = header_font
    row += 1
    headers = ["구분", "매출액", "매출원가", "GPM(%)", "판관비", "영업이익", "OPM(%)", "당기순이익", "지배순이익"]
    pct_cols = {4, 7}
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=row, column=col, value=h)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    for q in valuation.get("quarterly", []):
        row += 1
        vals = [q.get("period", ""), q.get("revenue"), q.get("cogs"), q.get("gpm"),
                q.get("sga"), q.get("op"), q.get("opm"), q.get("net_income"), q.get("controlling_income")]
        write_val_row(ws1, row, vals, pct_cols)

    # --- 연간 실적 ---
    row += 2
    ws1.cell(row=row, column=1, value="연간 실적 (억원)").font = header_font
    row += 1
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=row, column=col, value=h)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    for a in valuation.get("annual", []):
        row += 1
        vals = [a.get("period", ""), a.get("revenue"), a.get("cogs"), a.get("gpm"),
                a.get("sga"), a.get("op"), a.get("opm"), a.get("net_income"), a.get("controlling_income")]
        write_val_row(ws1, row, vals, pct_cols)

    # --- 비용의 성격별 분류 ---
    row += 2
    ws1.cell(row=row, column=1, value="비용의 성격별 분류 (억원)").font = header_font
    row += 1
    cost_headers = ["구분", "원재료비", "인건비", "감가상각비", "기타"]
    for col, h in enumerate(cost_headers, 1):
        cell = ws1.cell(row=row, column=col, value=h)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    all_cost = valuation.get("cost_breakdown_quarterly", []) + valuation.get("cost_breakdown_annual", [])
    for cb in all_cost:
        row += 1
        vals = [cb.get("period", ""), cb.get("raw_materials"), cb.get("labor"), cb.get("depreciation"), cb.get("others")]
        write_val_row(ws1, row, vals)

    for col in range(1, 10):
        ws1.column_dimensions[get_column_letter(col)].width = 15

    # ==================== Sheet 2: 양식 ====================
    ws2 = wb.create_sheet("양식")
    report = data.get("report", {})

    ws2["A1"] = f"{company_name} ({company_code})"
    ws2["A1"].font = title_font
    ws2.column_dimensions["A"].width = 18
    ws2.column_dimensions["B"].width = 70

    def star_row(ws, r, text):
        """대분류 (*) 헤더"""
        cell = ws.cell(row=r, column=1, value=f"*{text}")
        cell.font = star_font
        cell.fill = star_fill
        cell.border = thin_border
        ws.cell(row=r, column=2).fill = star_fill
        ws.cell(row=r, column=2).border = thin_border
        return r + 1

    def mid_row(ws, r, text):
        """중분류 (1), 2)...) 헤더"""
        cell = ws.cell(row=r, column=1, value=text)
        cell.font = mid_font
        cell.border = thin_border
        ws.cell(row=r, column=2).border = thin_border
        return r + 1

    def data_row(ws, r, label, value):
        """일반 데이터 행"""
        cell_a = ws.cell(row=r, column=1, value=label)
        cell_a.font = normal_font
        cell_a.border = thin_border
        cell_b = ws.cell(row=r, column=2, value=value)
        cell_b.font = normal_font
        cell_b.border = thin_border
        cell_b.alignment = Alignment(wrap_text=True, vertical="top")
        return r + 1

    row = 3

    # --- *개요 ---
    overview = report.get("overview", {})
    row = star_row(ws2, row, "개요")
    row = data_row(ws2, row, "BM", overview.get("bm_summary", ""))

    mix_q = overview.get("mix_quarter", "")
    seg_mix = overview.get("segment_mix", [])
    if seg_mix:
        mix_str = ", ".join(f"{s.get('name','')} {s.get('ratio',0):.1f}%" for s in seg_mix)
        row = data_row(ws2, row, f"사업별 매출비중 ({mix_q})", mix_str)
    reg_mix = overview.get("region_mix", [])
    if reg_mix:
        mix_str = ", ".join(f"{s.get('name','')} {s.get('ratio',0):.1f}%" for s in reg_mix)
        row = data_row(ws2, row, f"지역별 매출비중 ({mix_q})", mix_str)
    row += 1

    # --- *과거연간실적 ---
    row = star_row(ws2, row, "과거연간실적")
    for pa in report.get("past_annual", []):
        yr = pa.get("year", "")
        rev = pa.get("revenue")
        op = pa.get("op")
        opm = pa.get("opm")
        rev_s = f"{rev:,.0f}" if rev is not None else "-"
        op_s = f"{op:,.0f}" if op is not None else "-"
        opm_s = f"{opm:.1f}%" if opm is not None else "-"
        row = data_row(ws2, row, yr, f"매출액 {rev_s} / 영업이익 {op_s} / OPM {opm_s}")
    row += 1

    # --- *최근 분기 ---
    lq = report.get("latest_quarter", {})
    cur = lq.get("current", {})
    cur_period = cur.get("period", "최근분기")
    row = star_row(ws2, row, cur_period)

    def fmt_quarter(q):
        rev = q.get("revenue")
        op = q.get("op")
        opm = q.get("opm")
        rev_s = f"{rev:,.0f}" if rev is not None else "-"
        op_s = f"{op:,.0f}" if op is not None else "-"
        opm_s = f"{opm:.1f}%" if opm is not None else "-"
        return f"매출액 {rev_s} / 영업이익 {op_s} / OPM {opm_s}"

    row = data_row(ws2, row, cur_period, fmt_quarter(cur))
    prev_q = lq.get("prev_quarter", {})
    yoy_q = lq.get("yoy_quarter", {})
    comp_parts = []
    if prev_q.get("period"):
        comp_parts.append(f"{prev_q['period']} {fmt_quarter(prev_q)}")
    if yoy_q.get("period"):
        comp_parts.append(f"{yoy_q['period']} {fmt_quarter(yoy_q)}")
    if comp_parts:
        row = data_row(ws2, row, "(비교)", ", ".join(comp_parts))
    row += 1

    # --- *사업부별 ---
    for seg in report.get("segments", []):
        seg_name = seg.get("name", "사업부")
        seg_ratio = seg.get("revenue_ratio")
        ratio_str = f" ({seg_ratio:.1f}%)" if seg_ratio is not None else ""
        row = star_row(ws2, row, f"{seg_name}{ratio_str}")

        row = mid_row(ws2, row, "1) 개요 및 실적")
        row = data_row(ws2, row, "개요", seg.get("overview", ""))

        for qr in seg.get("quarterly_revenue", []):
            yr = qr.get("year", "")
            q1 = qr.get("q1")
            q2 = qr.get("q2")
            q3 = qr.get("q3")
            q4 = qr.get("q4")
            ann = qr.get("annual")
            parts = []
            for q_val in [q1, q2, q3, q4]:
                parts.append(f"{q_val:,.0f}" if q_val is not None else "-")
            ann_s = f"{ann:,.0f}" if ann is not None else "-"
            row = data_row(ws2, row, yr, f"{', '.join(parts)}  (연) {ann_s}")

        kc = seg.get("key_changes", "")
        if kc:
            row = data_row(ws2, row, "주요변동", kc)

        row = mid_row(ws2, row, "2) 전망")
        row = data_row(ws2, row, "", seg.get("outlook", ""))
        row += 1

    # --- *수익성 ---
    row = star_row(ws2, row, "수익성")
    row = data_row(ws2, row, "", report.get("profitability", ""))
    row += 1

    # --- *비용구조 ---
    cost_st = report.get("cost_structure", {})
    row = star_row(ws2, row, "비용구조")
    note = cost_st.get("note")
    if note:
        row = data_row(ws2, row, "특이사항", note)
    by_nature = cost_st.get("by_nature", "")
    if by_nature:
        row = data_row(ws2, row, "성격별", f"전체 비용 100% = {by_nature}")
    by_var = cost_st.get("by_variability", "")
    if by_var:
        row = data_row(ws2, row, "변동/고정", f"전체 비용 100% = {by_var}")
    row += 1

    # --- *실적 전망 및 가이던스 ---
    outlook = report.get("outlook", {})
    row = star_row(ws2, row, "실적 전망 및 가이던스")
    row = mid_row(ws2, row, "1) 다음 분기 예상")
    row = data_row(ws2, row, "", outlook.get("next_quarter", ""))
    row = mid_row(ws2, row, "2) 2026E")
    row = data_row(ws2, row, "", outlook.get("annual_2026e", ""))

    # Save
    filename = f"{company_name}_{company_code}_research.xlsx"
    filepath = os.path.join(UPLOAD_DIR, filename)
    wb.save(filepath)
    return filepath
