import logging
import os
import pickle
from unified import *
from dotenv import load_dotenv

load_dotenv()

from telegram.constants import ParseMode
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

with open("stu_data.pkl", "rb") as f:
    student_record = pickle.load(f)

TEST = True
LOCAL = True


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

FEEDBACK, ROLLNO, SEM, EXAM = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """async default message"""

    await update.message.reply_text(
        "Hi! I am REC bot\n"
        "I know unified portal is a crap\n"
        "I can fetch your marks in seconds\n\n"
        "/mymark - to get your mark\n"
        "/othersmark - to get others mark\n"
        "/change - to change your rollno\n"
        "/feedback - like to change me? give a feedback\n"
        "/about - about this project"
    )

    return None

async def mymark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask about the roll number"""
    context.user_data["own"] = True

    if "roll" in context.user_data:
        return get_rollno(update, context)

    await update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO


async def othersmark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask about the roll number"""
    context.user_data["own"] = False

    await update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO

async def changeroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Change the async default roll number"""
    context.user_data["own"] = True

    if "roll" in context.user_data:
        del context.user_data["roll"]

    await update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a about message"""


    await update.message.reply_text(
        "Filtering the cat marks in the unified portal is a nightmare\n"
        "so made this simple bot to save your time \n\n"
        "Here is the [github link](https://github.com/sunilxd/recbot)\n\n\n"
        "\\~\n"
        "telegram [DM](tg://user?id=1156186009)\n"
        "Insagram [sunilkumar](https://www.instagram.com/sunilkumar.0_o)\n"
        "GitHub [sunilxd](https://github.com/sunilxd)",
        parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )


async def feedbackstart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ask for a feedback"""
    await update.message.reply_text(
        "Leave your feedback as a message"
    )

    return FEEDBACK

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """get the feedback and send to me"""
    msg = update.message.text
    logger.info(f"feedback - {msg}")

    # send feedback to sunil 1156186009
    msg = f"{update.message.from_user.id} - {update.message.from_user.full_name}\nfeedback\n{msg}"
    context.bot.send_message(text=msg, chat_id=1156186009)



    await update.message.reply_text(
        "I send that to the developer\n"
        "Can't wait?\n"
        "You can give a pull request [here](https://github.com/sunilxd/recbot)",
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )

    return ConversationHandler.END

async def get_rollno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """"Get the roll number and check if the roll number is valid then ask about semester"""

    userid = update.message.from_user.id
    user = update.message.from_user.full_name

    if context.user_data["own"] and ("roll" in context.user_data):
        roll_no = context.user_data["roll"]

    else:
        roll_no = update.message.text

    sry_message = "I never seen that rollno in unified portal"


    if roll_no not in student_record:
        await update.message.reply_text(sry_message)

        return ConversationHandler.END

    user_id, user_name = student_record[roll_no]

    if context.user_data["own"]:
        context.user_data["roll"] = roll_no

    
    logger.info(f"{userid}({user}) : {roll_no}({user_name})")
    print(f"{userid}({user}) : {roll_no}({user_name})")

    try:
        marks = get_internal_filter(user_id)

    except Exception as e:
        logger.error(e)

        await update.message.reply_text(
            "Hmmmm.... rajalakshmi.in is down\n\n"
            "Try after sometime")

        return ConversationHandler.END


    context.user_data["marks"] = marks

    reply_keyboard = [[semester] for semester in sorted(marks)]

    await update.message.reply_text(
        f"Got you {user_name}\n"
        "Pick the semester",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return SEM


async def get_semester(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the semester check if it is valid then ask about Exam"""

    exam = update.message.text

    if exam not in context.user_data["marks"]:
        await update.message.reply_text(
            "That is not a valid semester\n"
            "Please Try again"
        )

        return ConversationHandler.END

    context.user_data["marks"] = marks = context.user_data["marks"][exam]

    reply_keyboard = [[exam] for exam in sorted(marks)]

    await update.message.reply_text(
        "What marks do you want?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return EXAM


def beautify_marks(marks):
    table = "\n"

    for mark in marks:
        table += "{mark}: {total}\n".format(mark = mark["subject"], total = mark["total"])

    return table

async def get_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the exam; if valid show the marks"""

    exam = update.message.text

    if exam not in context.user_data["marks"]:
        await update.message.reply_text(
            "Sorry didn't see that exam name in database"
        )

        return ConversationHandler.END

    marks = context.user_data["marks"][exam]

    table = beautify_marks(marks)

    await update.message.reply_text(f"```{table}```", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=ReplyKeyboardRemove(),)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""

    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    """Run the bot"""
    token = os.getenv("TEST_TOKEN") if TEST else os.getenv("TOKEN")

    application = Application.builder().token(token).build()

    # conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("mymark", mymark),
            CommandHandler("othersmark", othersmark),
            CommandHandler("change", changeroll),
            CommandHandler("feedback", feedbackstart),
            CommandHandler("about", about),
            MessageHandler(filters.TEXT, start),
        ],
        states={
            FEEDBACK: [MessageHandler(filters.TEXT, feedback)],
            ROLLNO: [MessageHandler(filters.TEXT, get_rollno)],
            SEM: [MessageHandler(filters.TEXT, get_semester)],
            EXAM: [MessageHandler(filters.TEXT, get_exam)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)


    # run
    application.run_polling()



if __name__ == "__main__":
    main()