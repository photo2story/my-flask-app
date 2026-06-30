# app.py
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

_YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
_YAHOO_UA = "Mozilla/5.0 (compatible; beatSnP/1.0)"

_default_origins = (
    "https://www.beatsnp.com,"
    "https://beatsnp.com,"
    "http://localhost:3000,"
    "http://localhost:5000,"
    "http://localhost:8080,"
    "http://localhost:5173,"
    "http://127.0.0.1:5000"
)
_origins_env = os.getenv("ALLOWED_ORIGINS", _default_origins).strip()
if _origins_env == "*":
    CORS(app)
else:
    _origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
    CORS(app, origins=_origins)


def _close_from_history(stock):
    """fast_info가 0/None일 때 최근 종가 fallback."""
    hist = stock.history(period="2d")
    if hist.empty:
        return None
    return float(hist["Close"].iloc[-1])


def _quote_from_symbol(symbol):
    stock = yf.Ticker(symbol)
    info = stock.fast_info

    price = float(info.get("last_price") or 0)
    previous_close = float(info.get("previous_close") or 0)

    if price == 0:
        fallback = _close_from_history(stock)
        if fallback is not None and fallback > 0:
            price = fallback

    change = 0.0
    if previous_close:
        change = ((price - previous_close) / previous_close) * 100

    return price, previous_close, change


@app.route("/")
def home():
    return {"status": "ok", "service": "BeatSnP Price API"}


@app.route("/api/stock/<ticker>/price")
def get_price(ticker):
    try:
        price, previous_close, change = _quote_from_symbol(ticker)

        return jsonify({
            "ticker": ticker.upper(),
            "price": price,
            "previousClose": previous_close,
            "change": change,
            "timestamp": int(datetime.now().timestamp() * 1000),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/prices")
def get_prices():
    tickers = request.args.get("tickers", "")
    symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    result = {}
    for symbol in symbols:
        try:
            price, previous_close, change = _quote_from_symbol(symbol)
            result[symbol] = {
                "price": price,
                "previousClose": previous_close,
                "change": change,
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
        except Exception as e:
            result[symbol] = {"error": str(e)}

    return jsonify(result)


def _proxy_yahoo_chart(ticker, range_="2y", interval="1d"):
    resp = requests.get(
        f"{_YAHOO_CHART_URL}/{ticker}",
        params={"range": range_, "interval": interval},
        headers={"User-Agent": _YAHOO_UA},
        timeout=15,
    )
    if resp.status_code != 200:
        return jsonify(
            {
                "error": "Yahoo chart failed",
                "status": resp.status_code,
            }
        ), 502
    return jsonify(resp.json())


@app.route("/api/stock/<ticker>/history")
def get_history(ticker):
    """Yahoo Finance Chart 프록시 — 웹은 항상 Render를 통해 히스토리 조회."""
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return jsonify({"error": "ticker is required"}), 400

    range_ = (request.args.get("range") or "2y").strip()
    interval = (request.args.get("interval") or "1d").strip()

    try:
        return _proxy_yahoo_chart(symbol, range_=range_, interval=interval)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except ValueError as e:
        return jsonify({"error": f"Invalid Yahoo response: {e}"}), 502


@app.route("/api/finance/search")
def finance_search():
    """Yahoo Finance Search 프록시 — Flutter Web CORS 우회."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"error": "q is required", "quotes": []}), 400

    try:
        limit = int(request.args.get("limit") or 10)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 25))

    try:
        resp = requests.get(
            _YAHOO_SEARCH_URL,
            params={
                "q": q,
                "quotesCount": limit + 4,
                "newsCount": 0,
            },
            headers={"User-Agent": _YAHOO_UA},
            timeout=12,
        )
        if resp.status_code != 200:
            return jsonify(
                {
                    "error": "Yahoo search failed",
                    "status": resp.status_code,
                    "quotes": [],
                }
            ), 502
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e), "quotes": []}), 502
    except ValueError as e:
        return jsonify({"error": f"Invalid Yahoo response: {e}", "quotes": []}), 502


@app.route("/api/finance/chart")
def finance_chart():
    """Yahoo Finance Chart 프록시 — 기존 클라이언트 호환 경로."""
    ticker = (request.args.get("ticker") or "").strip().upper()
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    range_ = (request.args.get("range") or "2y").strip()
    interval = (request.args.get("interval") or "1d").strip()

    try:
        return _proxy_yahoo_chart(ticker, range_=range_, interval=interval)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except ValueError as e:
        return jsonify({"error": f"Invalid Yahoo response: {e}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
