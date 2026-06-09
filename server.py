from flask import Flask, request, jsonify, send_from_directory
import os
import json
import urllib.request

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
    if not ANTHROPIC_KEY:
        return jsonify({"error": "No API key configured"}), 500

    system_prompt = """You are an elite Investment Committee comprising Warren Buffett, Benjamin Graham, and Peter Lynch. Analyze the stock ticker using your knowledge and return your response in EXACTLY this format:

```json
{"companyName":"","sector":"","industry":"","currentPrice":0,"marketCap":0,"pe":0,"pb":0,"roe":0,"pm":0,"de":0,"cr":0,"eg":0,"rg":0,"div":0,"beta":0,"eps":0,"peg":0,"high52w":0,"low52w":0,"return5yr":0}
```

---ANALYSIS---

## Executive Summary
2-3 sentence ruthless synthesis.

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

IMPORTANT: roe, pm, eg, rg, div are decimals (0.15=15%). de is debt/equity x100."""

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 3000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": "Analyze the stock ticker: " + ticker}]
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
