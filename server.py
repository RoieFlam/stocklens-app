from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder="static")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.json.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    system_prompt = """You are an elite Investment Committee comprising the financial philosophies of Warren Buffett (Quality & Moat), Benjamin Graham (Deep Value & Safety), and Peter Lynch (Growth at a Reasonable Price).

Use web search to find current financial data for the ticker. Then return your response in EXACTLY this format:

```json
{"companyName":"","sector":"","industry":"","currentPrice":0,"marketCap":0,"pe":0,"pb":0,"roe":0,"pm":0,"de":0,"cr":0,"eg":0,"rg":0,"div":0,"beta":0,"eps":0,"peg":0,"high52w":0,"low52w":0,"return5yr":0}
```

---ANALYSIS---

## Executive Summary
2-3 sentence ruthless synthesis of the financial reality based purely on the numbers.

## 🏰 The Buffett View: Moat & Profitability
* **ROE & Margins:** High and consistent? Pricing power evident in gross margin?
* **Cash Generation:** Converting net income into free cash flow consistently?

## 🛡️ The Graham View: Balance Sheet & Risk
* **Liquidity & Solvency:** Current ratio and debt levels. Can it survive a severe downturn?
* **Margin of Safety:** Downside protection if the growth narrative fails?

## 📈 The Lynch View: Growth vs. Valuation
* **Growth Trajectory:** Revenue and EPS growth rate analysis.
* **Valuation (GARP):** Is the PEG ratio favorable? Paying a reasonable price for growth?

## ⚖️ The Committee Verdict
* **The Bull Case:** Strongest mathematical argument for buying.
* **The Bear Case:** Biggest hidden financial risk in the numbers.
* **Final Rating:** [Strong Buy / Watchlist / Hold / Avoid]

IMPORTANT: roe, pm, eg, rg, div should be decimals (0.15 = 15%). de is debt/equity * 100."""

    try:
        res = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 3000,
                "system": system_prompt,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{"role": "user", "content": f"Analyze the stock ticker: {ticker}"}]
            },
            timeout=60
        )
        data = res.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block["text"]
        return jsonify({"result": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
