import logging
import os
import pickle
from unified import *
from dotenv import load_dotenv
from keep_alive import keep_alive

# loadenv
load_dotenv()
from replit import db

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

TEST = True


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

FEEDBACK, ROLLNO, RESULT, REGISTER = range(4)

async def helper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """async default message"""

    await update.message.reply_text(
        "Hi! I am REC bot\n"
        "I know unified portal is a crap\n"
        "I can fetch your marks in seconds\n\n"
        "/marks - fetch internal mark\n"
        "/grades - fetch semester grades\n"
        "/attendance - fetch attendance\n"
        "/result - fetch recent result\n"
        "/add_rollno - link your rollno with bot\n\n"
        "/feedback - like to change me? give a feedback\n"
        "/about - about this project"
    )

    return None


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a about message"""


    await update.message.reply_text(
        "Filtering the cat marks in the unified portal is a nightmare\n"
        "so made this simple bot to save your time \n\n"
        "Here is the [github link](https://github.com/sunilxd/recbot)\n\n\n"
        "\\~\n"
        "telegram [DM](tg://user?id=1156186009)\n"
        "Insagram [sunilkumar](https://www.instagram.com/sunilkumar.0_o)\n"
        "GitHub [sunilxd](https://github.com/sunilxd)\n",
        parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )


async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    await context.bot.send_message(text=msg, chat_id=1156186009)



    await update.message.reply_text(
        "I send that to the developer\n"
        "Can't wait?\n"
        "You can give a pull request [here](https://github.com/sunilxd/recbot)",
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )

    return ConversationHandler.END


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask about the email"""

    msg = "College email please"

    await update.message.reply_text(msg)

    return  REGISTER


async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """with the email add the student"""

    email = update.message.text

    try:
        response = get_additional_role(email)
        person_id = response["PersonId"]

        info = get_personal_info(person_id)
        name, rollno = info["Name"], info["RollNumber"]
        char_remove = ['Mr..', 'Ms..', 'Mrs..', 'Dr..', 'MR.', 'Miss..', 'M/s.', 'Miss.']
        for c in char_remove:
            name = name.replace(c, '')
        name = name.lower().strip()

    except Exception as e:
        logger.error(e)

        await update.message.reply_text(
            "Seems you are not yet added in unified portal\n\n"
            "Try after sometime"
        )

        return ConversationHandler.END
    
    db["stu_data"][rollno] = (person_id, name, email)
    msg = "{} : {}\nAdded Successfully!".format(rollno, name)

    await update.message.reply_text(msg)

    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask about the roll number"""
    context.user_data["entry"] = update.message.text

    telegram_id = str(update.message.from_user.id)
    msg = "Roll number please"

    if telegram_id in db:

        reply_keyboard = [[roll_no] for roll_no in db[telegram_id]]
        reply_keyboard.append(['new'])


        await update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            ),
        )

    else:
        await update.message.reply_text(
            msg
        )

    return ROLLNO


def get_response(id, email, entry):

    if entry == "/marks":
        return get_internal_filter(id)
    
    elif entry == "/grades":
        return get_grades_filter(id)
    
    elif entry == "/attendance":
        return get_attendance_filter(email)
    
    else:
        return get_result_filter(email)


async def rollno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """"Get the roll number and check if the roll number is valid then ask about semester"""

    roll_no = update.message.text

    if roll_no == 'new':
        await update.message.reply_text(
            "yeah sure\nNew roll number please"
        )

        return ROLLNO

    telegram_id = str(update.message.from_user.id)
    user = update.message.from_user.full_name

    sry_message = "Roll number missing\nTry adding your number by /add_rollno"


    if roll_no not in db["stu_data"]:
        await update.message.reply_text(sry_message)

        return ConversationHandler.END

    unified_id, user_name, email = db["stu_data"][roll_no]
    entry = context.user_data["entry"]
    context.user_data["roll_no"] = roll_no
    context.user_data["name"] = user_name
    
    logger.info(f"{telegram_id}({user}) : {roll_no}({user_name})")

    try:
        response = get_response(unified_id, email, entry)

    except Exception as e:
        logger.error(e)

        await update.message.reply_text(
            "Hmmmm.... rajalakshmi.in is down\n\n"
            "Try after sometime"
        )

        return ConversationHandler.END
    
    # if first roll_no
    if telegram_id not in db:
        db[telegram_id] = {roll_no:1}

    # not first
    else:
        db[telegram_id][roll_no] = db[telegram_id].get(roll_no, 0) + 1


    context.user_data["data"] = response

    if isinstance(response, str):
        return await display_result(update, context)

    return await pick_result(update, context)


async def pick_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pick one result"""

    reply_keyboard = [[clickable] for clickable in sorted(context.user_data["data"])]

    await update.message.reply_text(
        "Pick one",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return RESULT


async def display_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the result"""

    data = "\n"+context.user_data["data"]+"\n{}: {}\n".format(context.user_data["roll_no"], context.user_data["name"])

    await update.message.reply_text(f"```{data}```", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=ReplyKeyboardRemove(),)
    return ConversationHandler.END


async def filter_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the semester check if it is valid then ask about Exam""" 

    user_msg = update.message.text

    if user_msg not in context.user_data["data"]:
        await update.message.reply_text(
            "That is not a valid pick\n"
            "Please Try again"
        )

        return ConversationHandler.END

    context.user_data["data"] = context.user_data["data"][user_msg]

    if isinstance(context.user_data["data"], str):
        return await display_result(update, context)

    return await pick_result(update, context)


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
            CommandHandler("marks", start),
            CommandHandler("grades", start),
            CommandHandler("attendance", start),
            CommandHandler("result", start),
            CommandHandler("feedback", feedback_start),
            CommandHandler("about", about),
            CommandHandler("add_rollno", register),
            MessageHandler(filters.TEXT, helper),
        ],
        states={
            FEEDBACK: [MessageHandler(filters.TEXT, feedback)],
            ROLLNO: [MessageHandler(filters.TEXT, rollno)],
            RESULT: [MessageHandler(filters.TEXT, filter_result)],
            REGISTER: [MessageHandler(filters.TEXT, add_student)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)


    # run
    application.run_polling()



if __name__ == "__main__":
    keep_alive()
    main()