from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import sys

app = Flask(__name__, static_folder="static")

# Fail fast if API key is missing
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
if not ANTHROPIC_KEY:
    print("WARNING: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.json.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
        
    if not ANTHROPIC_KEY:
        return jsonify({"error": "Server configuration error: Missing API Key"}), 500

    # NOTE: Claude cannot actually search the web here. Consider fetching 
    # data from a financial API and injecting it into this prompt.
    system_prompt = """You are an elite Investment Committee comprising the financial philosophies of Warren Buffett (Quality & Moat), Benjamin Graham (Deep Value & Safety), and Peter Lynch (Growth at a Reasonable Price).

Return your response in EXACTLY this format:

```json
{"companyName":"","sector":"","industry":"","currentPrice":0,"marketCap":0,"pe":0,"pb":0,"roe":0,"pm":0,"de":0,"cr":0,"eg":0,"rg":0,"div":0,"beta":0,"eps":0,"peg":0,"high52w":0,"low52w":0,"return5yr":0}
