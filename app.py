import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
configuration = Configuration(access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text

    system_prompt = """あなたは「AIことば相談BOT」です。
ユーザーが人間関係で困っている言葉の問題を相談してきます。
以下のケースに対応しですね。
【おすすめの文章】
---
（具体的なメッセージ例）
---
【一言アドバイス】〇〇

簡潔に、すぐ使える言葉を提案してください。"""

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    )

    reply_text = response.content[0].text

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(port=5001, debug=True)
