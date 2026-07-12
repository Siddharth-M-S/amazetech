import re
import requests
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8922428006:AAGfh886pt8NdRi5wtJtKvFF-0me0TlZosc"
AFFILIATE_TAG = "blacksidtech-21"

AMAZON_DOMAINS = [
    "amazon.com", "amazon.co.uk", "amazon.ca", "amazon.com.au",
    "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.co.jp",
    "amazon.in", "amzn.to", "amzn.com"
]


def is_amazon_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        return any(domain == d or domain.endswith("." + d) for d in AMAZON_DOMAINS)
    except Exception:
        return False


def expand_short_url(url: str) -> str:
    """Expand shortened URLs like amzn.to"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception:
        return url


def inject_affiliate_tag(url: str, tag: str) -> str:
    """Inject affiliate tag into Amazon URL"""
    # Expand short URLs first
    parsed_check = urlparse(url)
    domain = parsed_check.netloc.lower().replace("www.", "")
    if "amzn.to" in domain or "amzn.com" in domain:
        url = expand_short_url(url)

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)

    # Replace or add the tag
    query_params["tag"] = [tag]

    # Rebuild the query string (keep lists flat)
    new_query = urlencode({k: v[0] for k, v in query_params.items()})

    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        ""  # remove fragment
    ))
    return new_url


def extract_urls(text: str) -> list:
    url_pattern = re.compile(r'https?://[^\s]+')
    return url_pattern.findall(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Send me any Amazon product link and I'll give you the affiliate link.\n\n"
        "Just paste the link and I'll handle the rest!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    urls = extract_urls(text)

    amazon_urls = [u for u in urls if is_amazon_url(u)]

    if not amazon_urls:
        await update.message.reply_text(
            "Please send a valid Amazon product link.\nExample: https://www.amazon.com/dp/B08N5WRWNW"
        )
        return

    results = []
    for url in amazon_urls:
        affiliate_url = inject_affiliate_tag(url, AFFILIATE_TAG)
        results.append(affiliate_url)

    reply = "\n\n".join(results)
    await update.message.reply_text(f"Your affiliate link:\n\n{reply}")


def main():
    print("Bot is starting...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
