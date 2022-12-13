import logging
import pickle
from unified import *
from prettytable import PrettyTable


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
    format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

ROLLNO, SEM, EXAM = range(3)

def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their rollno"""

    update.message.reply_text(
        "Hi! My name is REC Bot.\n"
        "I know unified portal is a crap\n"
        "I can fetch your marks in seconds\n\n"
        "Enter your roll number"
    )

    return ROLLNO


def get_rollno(update: Update, context: CallbackContext) -> int:
    """"Get the roll number and check if the roll number is valid then ask about semester"""

    userid = update.message.from_user.id
    user = update.message.from_user.first_name
    roll_no = update.message.text

    sry_message = "I never seen that rollno in unified portal"


    if roll_no not in student_record:
        update.message.reply_text(sry_message)

        return ConversationHandler.END

    user_id, user_name = student_record[roll_no]

    logger.info(f"{user_id} : {roll_no}({user_name})")

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
    table = PrettyTable(['Subject Name', 'Marks'])
    table = "\n"
    # table.align['Subject Name'] = 'l'
    # table.align['Marks'] = 'r'

    for mark in marks:
        # table.add_row([mark['subject'], mark['total']])
        table += f"{mark['subject']}: {mark['total']}\n"

    return table

def get_exam(update: Update, context: CallbackContext) -> int:
    """Get the exam if valid show the marks"""

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
    updater = Updater("")


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
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