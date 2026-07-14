import re
import requests
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

AFFILIATE_TAG = "blacksidtech-21"

AMAZON_DOMAINS = [
    "amazon.com", "amazon.co.uk", "amazon.ca", "amazon.com.au",
    "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.co.jp",
    "amazon.in", "amzn.to", "amzn.com", "amzn.in"
]


def is_amazon_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        return any(domain == d or domain.endswith("." + d) for d in AMAZON_DOMAINS)
    except Exception:
        return False


def expand_short_url(url: str) -> str:
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception:
        return url


def inject_affiliate_tag(url: str, tag: str) -> str:
    parsed_check = urlparse(url)
    domain = parsed_check.netloc.lower().replace("www.", "")
    if "amzn.to" in domain or "amzn.com" in domain or "amzn.in" in domain:
        url = expand_short_url(url)

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    query_params["tag"] = [tag]

    new_query = urlencode({k: v[0] for k, v in query_params.items()})
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        ""
    ))
    return new_url


def extract_first_url(text: str):
    pattern = re.compile(r'https?://[^\s]+')
    match = pattern.search(text)
    return match.group(0) if match else None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json()
    raw = data.get("url", "").strip()

    url = extract_first_url(raw)
    if not url:
        return jsonify({"error": "No URL found"}), 400

    if not is_amazon_url(url):
        return jsonify({"error": "Not a valid Amazon link"}), 400

    affiliate_url = inject_affiliate_tag(url, AFFILIATE_TAG)
    return jsonify({"affiliate_url": affiliate_url})


if __name__ == "__main__":
    app.run(debug=False)
