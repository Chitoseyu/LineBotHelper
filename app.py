from flask import Flask, request, abort, jsonify, render_template

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os
import traceback
import requests

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

# Channel Access Token
configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 返回 LINE Bot 狀態
@app.route("/api/status", methods=["GET"])
def api_status():
    error_type = request.args.get("error")
    if error_type == "database":
        return jsonify({"status": "資料庫錯誤"}), 500
    elif error_type == "api":
        return jsonify({"status": "外部 API 錯誤"}), 503
    else:
        return jsonify({"status": "運行中"})

#  LINE Bot 狀態顯示網頁
@app.route("/")
def index():
    try:
        response = requests.get(f"{API_BASE_URL}/api/status")
        response.raise_for_status()
        status = response.json()["status"]
        return render_template("/view/index.html", status=status)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching status from API: {e}")
        return "無法從 API 取得狀態", 500 
    except (KeyError, ValueError) as e:
        app.logger.error(f"Error parsing API response: {e}")
        return "API 回應格式錯誤", 500
    

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)