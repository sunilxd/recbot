from dotenv import load_dotenv
import os
from matplotlib.pyplot import table
import telebot
from telebot import types
from database import *

load_dotenv()
API_KEY = os.getenv('API_KEY')
PIN = os.getenv('PIN')
bot = telebot.TeleBot(API_KEY)

chat_manager = {}

help_message = """If you're new, please see the [manual](https://happi.sunilkumar70.repl.co/).

You can control me by sending these commands:

*Student*
/join - enroll yourself (only for AIML)
/timetable - for today timetable
/leave - tell your teacher your are going to be absent today

*Teacher*
/mark - send marks of the students
/leave - get list of students who are absent

*Others*
/cancel - cancel the operation
/help - to know about the commands
"""

@bot.message_handler(func=lambda m: True)
def tinson(message):
    sender_id = message.chat.id
    msg = message.text
    # main commands
    if msg=='/join':
        table = data_to_dic()
        if sender_id in table:
            chat_manager[sender_id] = {'msg':'join_roll'}
            bot.send_message(sender_id, 'You already joined\nroll no {roll}\nname {name}\nTo modify type your roll no\nuse /cancel to dismiss'.\
                format(roll = table[sender_id]['roll'], name = table[sender_id]['name']))
        else:
            chat_manager[sender_id] = {'msg':'join_pin'}
            bot.send_message(sender_id, 'Alright, Enter a pin to continue\n(only for AIML student)')
    elif msg=='/timetable':
        bot.send_message(sender_id, 'Soon here you can see the timetable')
    elif msg=='/leave':
        bot.send_message(sender_id, 'soon will be updated')
    elif msg=='/mark':
        table = data_to_dic()
        i = int(get_data('Data', 'f1')[0][0])
        mar = [ele[0] for ele in get_data('Mark', f'C2:C{i}')]
        chat_ids = list(table.keys())
        for ele in table:
            bot.send_message(ele, mar[chat_ids.index(ele)])
        bot.send_message(sender_id, 'Done')
    elif msg=='/cancel':
        chat_manager[sender_id] = {'msg':'None'}
        bot.send_message(sender_id, 'operation canceled')
    elif msg=='/start' or msg=='/help':
        bot.send_message(sender_id, help_message, parse_mode='Markdown')

    # all join operations
    elif sender_id in chat_manager and chat_manager[sender_id]['msg']=='join_pin':
        if int(msg)==int(PIN):
            chat_manager[sender_id]['msg'] = 'join_roll'
            bot.send_message(sender_id, 'Verified!\nwhat is your roll number?')
        else:
            chat_manager[sender_id] = {'msg':'None'}
            bot.send_message(sender_id, 'sorry wrong pin')
    elif sender_id in chat_manager and chat_manager[sender_id]['msg']=='join_roll':
        chat_manager[sender_id]['msg'] = 'join_name'
        chat_manager[sender_id]['roll'] = msg
        bot.send_message(sender_id, 'what is your name?')
    elif sender_id in chat_manager and chat_manager[sender_id]['msg']=='join_name':
        table = data_to_dic()
        chat_manager[sender_id]['msg'] = 'None'
        table[sender_id] = {'name':msg, 'roll':chat_manager[sender_id]['roll']}
        dic_to_data(table)
        bot.send_message(sender_id, 'Your details added')
    
    # send help command
    else:
        bot.send_message(sender_id, help_message)

bot.infinity_polling()