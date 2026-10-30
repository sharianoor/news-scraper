from flask import Flask, request, jsonify

from scraper import scrape_news
from summarizer import summarize_text


app = Flask(__name__)

REGISTRATION_NUMBER = "FA23-BDS-036"
NEWS_SOURCE = "TechCrunch"


@app.route("/get", methods=["GET"])
def get_news():

    keyword = request.args.get(
        "keyword",
        "",
        type=str
    ).strip()

    if not keyword:
        return jsonify({
            "error": "Please provide a keyword."
        }), 400

    try:
        result = scrape_news(keyword)

        summary = summarize_text(
            result["text"],
            max_sentences=3
        )

        response = {
            "registration": REGISTRATION_NUMBER,
            "newssource": NEWS_SOURCE,
            "keyword": keyword,
            "url": result["url"],
            "summary": summary
        }

        return jsonify(response), 200

    except Exception as error:
        app.logger.exception(
            "Failed to retrieve or summarize news."
        )

        return jsonify({
            "error": "Unable to retrieve news for this keyword.",
            "details": str(error),
            "registration": REGISTRATION_NUMBER
        }), 500


@app.route("/", methods=["GET"])
def home():

    return (
        "<h1>TechCrunch News Scraper API</h1>"
        "<p>Registration: FA23-BDS-036</p>"
        "<p>Use /get?keyword=artificial+intelligence "
        "to retrieve a news summary.</p>"
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=7000,
        debug=False
    )