import logging
import os
import pickle
from unified import *
from keep_alive import keep_alive

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

with open('stu_data.pkl', 'rb') as f:
    student_record = pickle.load(f)




# Enable logging
logging.basicConfig(level=logging.INFO,
    filename='info.log',
    format="%(asctime)s - %(levelname)s - %(message)s")

logging.basicConfig(level=logging.ERROR, 
    filename='error.log',
    format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

FEEDBACK, ROLLNO, SEM, EXAM = range(4)

def start(update: Update, context: CallbackContext) -> None:
    """Default message"""

    update.message.reply_text(
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

def mymark(update: Update, context: CallbackContext) -> int:
    """Ask about the roll number"""
    context.user_data['own'] = True

    if 'roll' in context.user_data:
        return get_rollno(update, context)

    update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO


def othersmark(update: Update, context: CallbackContext) -> int:
    """Ask about the roll number"""
    context.user_data['own'] = False

    update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO

def changeroll(update: Update, context: CallbackContext) -> int:
    """Change the default roll number"""
    context.user_data['own'] = True

    if 'roll' in context.user_data:
        del context.user_data['roll']

    update.message.reply_text(
        "Roll number please\n"
    )

    return ROLLNO


def about(update: Update, context: CallbackContext) -> int:
    """Send a about message"""


    update.message.reply_text(
        "Filtering the cat marks in the unified portal is a nightmare\n"
        "so made this simple bot to save your time \n\n"
        "Here is the [github link](https://github.com/sunilxd/recbot)\n\n\n"
        "\\~\n"
        "telegram [DM](tg://user?id=1156186009)\n"
        "Insagram [sunilkumar](https://www.instagram.com/sunilkumar.0_o)\n"
        "GitHub [sunilxd](https://github.com/sunilxd)",
        parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )


def feedbackstart(update: Update, context: CallbackContext) -> int:
    """ask for a feedback"""
    update.message.reply_text(
        "Leave your feedback as a message"
    )

    return FEEDBACK

def feedback(update: Update, context: CallbackContext) -> int:
    """get the feedback and send to me"""
    msg = update.message.text
    logger.info(f'feedback - {msg}')

    # send feedback to sunil 1156186009
    msg = f"{update.message.from_user.id} - {update.message.from_user.full_name}\nfeedback\n{msg}"
    context.bot.send_message(text=msg, chat_id=1156186009)



    update.message.reply_text(
        "I send that to the developer\n"
        "Can't wait?\n"
        "You can give a pull request [here](https://github.com/sunilxd/recbot)",
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )

    return ConversationHandler.END

def get_rollno(update: Update, context: CallbackContext) -> int:
    """"Get the roll number and check if the roll number is valid then ask about semester"""

    userid = update.message.from_user.id
    user = update.message.from_user.full_name

    if context.user_data['own'] and ('roll' in context.user_data):
        roll_no = context.user_data['roll']

    else:
        roll_no = update.message.text

    sry_message = "I never seen that rollno in unified portal"


    if roll_no not in student_record:
        update.message.reply_text(sry_message)

        return ConversationHandler.END

    user_id, user_name = student_record[roll_no]

    if context.user_data['own']:
        context.user_data['roll'] = roll_no

    
    logger.info(f"{userid}({user}) : {roll_no}({user_name})")
    print(f"{userid}({user}) : {roll_no}({user_name})")

    try:
        marks = get_internal_filter(user_id)

    except Exception as e:
        logger.error(e)

        update.message.reply_text(
            "Hmmmm.... rajalakshmi.in is down\n\n"
            "Try after sometime")

        return ConversationHandler.END


    context.user_data["marks"] = marks

    reply_keyboard = [[semester] for semester in sorted(marks)]

    update.message.reply_text(
        f"Got you {user_name}\n"
        "Pick the semester",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return SEM


def get_semester(update: Update, context: CallbackContext) -> int:
    """Get the semester check if it is valid then ask about Exam"""

    exam = update.message.text

    if exam not in context.user_data["marks"]:
        update.message.reply_text(
            "That is not a valid semester\n"
            "Please Try again"
        )

        return ConversationHandler.END

    context.user_data["marks"] = marks = context.user_data["marks"][exam]

    reply_keyboard = [[exam] for exam in sorted(marks)]

    update.message.reply_text(
        "What marks do you want?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return EXAM


def beautify_marks(marks):
    table = "\n"

    for mark in marks:
        table += f"{mark['subject']}: {mark['total']}\n"

    return table

def get_exam(update: Update, context: CallbackContext) -> int:
    """Get the exam; if valid show the marks"""

    exam = update.message.text

    if exam not in context.user_data["marks"]:
        update.message.reply_text(
            "Sorry didn't see that exam name in database"
        )

        return ConversationHandler.END

    marks = context.user_data["marks"][exam]

    table = beautify_marks(marks)

    update.message.reply_text(f"```{table}```", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=ReplyKeyboardRemove(),)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""

    update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    """Run the bot"""
    token = os.getenv('TOKEN')
    if token == None:
        token = pickle.load(open('token.pkl', 'rb'))


    ## running the flask to keep the repl running
    flask_thread = keep_alive()
    
    updater = Updater(token)


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("mymark", mymark),
            CommandHandler("othersmark", othersmark),
            CommandHandler("change", changeroll),
            CommandHandler("feedback", feedbackstart),
            CommandHandler("about", about),
            MessageHandler(Filters.text, start),
        ],
        states={
            FEEDBACK: [MessageHandler(Filters.text, feedback)],
            ROLLNO: [MessageHandler(Filters.text, get_rollno)],
            SEM: [MessageHandler(Filters.text, get_semester)],
            EXAM: [MessageHandler(Filters.text, get_exam)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)


    # run
    updater.start_polling()


    updater.idle()



if __name__ == "__main__":
    main()
