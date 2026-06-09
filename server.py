from flask import Flask, request, jsonify, send_from_directory
import os
import json
import urllib.request

app = Flask(__name__, static_folder="static")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FMP_KEY = os.environ.get("FMP_API_KEY", "")


def fmp_get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def fetch_stock_data(ticker):
    base = "https://financialmodelingprep.com/api/v3"
    profile = fmp_get(f"{base}/quote/{ticker}?apikey={FMP_KEY}")
    ratios = fmp_get(f"{base}/ratios/{ticker}?limit=1&apikey={FMP_KEY}")
    growth = fmp_get(f"{base}/financial-growth/{ticker}?limit=1&apikey={FMP_KEY}")
    history = fmp_get(f"{base}/historical-price-full/{ticker}?serietype=line&apikey={FMP_KEY}")

    p = profile[0] if isinstance(profile, list) and profile else {}
    r = ratios[0] if isinstance(ratios, list) and ratios else {}
    g = growth[0] if isinstance(growth, list) and growth else {}

    return5yr = 0
    if isinstance(history, dict) and "historical" in history:
        prices = history["historical"]
        if len(prices) >= 2:
            newest = prices[0]["close"]
            oldest = prices[-1]["close"]
            return5yr = round((newest - oldest) / oldest * 100, 1)

    return {
        "companyName": p.get("name", ticker),
        "sector": p.get("exchange", "N/A"),
        "industry": "N/A",
        "currentPrice": p.get("price", 0),
        "marketCap": p.get("marketCap", 0),
        "high52w": p.get("yearHigh", 0),
        "low52w": p.get("yearLow", 0),
        "beta": p.get("beta", 0),
        "eps": p.get("eps", 0),
        "pe": p.get("pe", 0),
        "pb": r.get("priceToBookRatioTTM", 0),
        "roe": r.get("returnOnEquityTTM", 0),
        "pm": r.get("netProfitMarginTTM", 0),
        "de": r.get("debtEquityRatioTTM", 0),
        "cr": r.get("currentRatioTTM", 0),
        "div": r.get("dividendYielTTM", 0),
        "peg": r.get("priceEarningsToGrowthRatioTTM", 0),
        "eg": g.get("epsgrowth", 0),
        "rg": g.get("revenueGrowth", 0),
        "return5yr": return5yr,
    }


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.json.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    if not ANTHROPIC_KEY:
        return jsonify({"error": "No Anthropic API key configured"}), 500

    stock = {}
    if FMP_KEY:
        stock = fetch_stock_data(ticker)

    system_prompt = """You are an elite Investment Committee comprising Warren Buffett, Benjamin Graham, and Peter Lynch.
You will be given live financial data for a stock. Analyze it and return your response in EXACTLY this format:

```json
{"companyName":"","sector":"","industry":"","currentPrice":0,"marketCap":0,"pe":0,"pb":0,"roe":0,"pm":0,"de":0,"cr":0,"eg":0,"rg":0,"div":0,"beta":0,"eps":0,"peg":0,"high52w":0,"low52w":0,"return5yr":0}
```

---ANALYSIS---

## Executive Summary
2-3 sentence ruthless synthesis based on the numbers provided.

## 🏰 The Buffett View: Moat & Profitability
* **ROE & Margins:** High and consistent? Pricing power?
* **Cash Generation:** Converting income to free cash flow?

## 🛡️ The Graham View: Balance Sheet & Risk
* **Liquidity & Solvency:** Current ratio and debt. Downturn survival?
* **Margin of Safety:** Downside protection if growth narrative fails?

## 📈 The Lynch View: Growth vs. Valuation
* **Growth Trajectory:** Revenue and EPS growth rate.
* **Valuation (GARP):** Is PEG ratio favorable?

## ⚖️ The Committee Verdict
* **The Bull Case:** Strongest argument for buying.
* **The Bear Case:** Biggest hidden risk.
* **Final Rating:** [Strong Buy / Watchlist / Hold / Avoid]

IMPORTANT: Use the exact numbers provided. roe, pm, eg, rg, div are decimals (0.15=15%). de is debt/equity x100."""

    user_message = f"Analyze {ticker} using this live financial data:\n\n{json.dumps(stock, indent=2)}\n\nFill the JSON block with these exact values, then write the full Investment Committee analysis."

    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 3000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode())

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        if not text:
            return jsonify({"error": "Empty response from API"}), 500

        return jsonify({"result": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
