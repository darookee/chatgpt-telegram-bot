from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler
import openai
import logging
import os

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
openai_key = os.environ["OPENAI_API_KEY"]

# Set up the OpenAI API
openai.api_key = openai_key

chat_messages = {}

# Define the function that handles incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the message text and chat ID
    message_text = update.message.text
    chat_id = update.effective_chat.id
    chat_id_str = str(chat_id)

    logger.info(f"Received Message {message_text} in {chat_id}.")

    if chat_id_str not in chat_messages:
        chat_messages[chat_id_str] = [
            {"role": "system", "content": f"You are a member of a Telegram chatgroup. You receive messages and try to answer them. Please respond with a short one paragraph answer. You may include jokes. The message may be in German or English."}
        ]

    chat_messages[chat_id_str].append({"role": "user", "content": message_text})

    try:
        # Call the OpenAI API to generate a response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_messages[chat_id_str],
            max_tokens=420,
            n=1,
            stop=None,
            temperature=0.7,
        )

        # Log the number of tokens used
        logger.info(f"Tokens used for this request: {response.usage['total_tokens']}")

        # Get the generated response from the OpenAI API
        generated_text = response.choices[0].message['content'].strip()

        chat_messages[chat_id_str].append({"role": "assistant", "content": generated_text})

        logger.info(f"Generated response: {generated_text}")

        # Send the response back to the user
        await update.effective_message.reply_text(text=generated_text)

    except openai.error.RateLimitError as e:
        error = str(e)
        await update.effective_message.reply_text(text=error)


async def reset_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_id_str = str(chat_id)

    if chat_id_str in chat_messages:
        logger.info(f"Resetting history of chat {chat_id}")
        del chat_messages[chat_id_str]

        await update.effective_message.reply_text('History cleared.')

        return

    await update.effective_message.reply_text('There was no history to reset.')


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.lstrip('/image')

    try:
        logger.info(f"Trying to generate image for prompt: {prompt}")
        # Call the OpenAI API to generate a response
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512",
        )

        # Get the generated response from the OpenAI API
        generated_image_url = response.data[0].url.strip()

        logger.info(f"Generated image: {generated_image_url}")

        # Send the response back to the user
        await update.effective_message.reply_document(document=generated_image_url, caption=prompt)

    except (openai.error.RateLimitError, openai.error.InvalidRequestError) as e:
        error = str(e)
        await update.effective_message.reply_text(text=error)


async def reset_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.lstrip('/prompt')

    chat_id = update.effective_chat.id
    chat_id_str = str(chat_id)

    logger.info(f"Setting initial prompt of {chat_id} to {prompt}")
    chat_messages[chat_id_str] = [
        {"role": "system", "content": f"{prompt}"}
    ]

    await update.effective_message.reply_text(f"initial prompt set to {prompt}.")


if __name__ == '__main__':
    # Set up the Telegram bot to listen for messages
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    reset_handler = CommandHandler("reset", reset_messages)
    setprompt_handler = CommandHandler("prompt", reset_prompt)
    image_handler = CommandHandler("image", generate_image)

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(message_handler)
    application.add_handler(reset_handler)
    application.add_handler(setprompt_handler)
    application.add_handler(image_handler)
    application.run_polling()
