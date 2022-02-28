from dotenv import load_dotenv
import os
import telebot
from telebot import types
from database import *
import pickle

load_dotenv()
API_KEY = os.getenv('API_KEY')
PIN = os.getenv('PIN')
bot = telebot.TeleBot(API_KEY)

chat_manager = {}
table = data_to_dic()
timetable = pickle.load(open('timetable.pickle', 'rb'))
days = ['tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

def get_timetable(day):
    global timetable
    per = timetable[day]
    tim = timetable[timetable['tim'][day]]
    te = ''
    for i in range(len(per)):
        te += tim[i]+'\n'
        te += timetable['map'][timetable[day][i]]+'\n\n'
    return te

def get_marks(column):
    i = int(get_data('Data', 'f1')[0][0])
    mar = [ele[0] for ele in get_data('Mark', f'{column}2:{column}{i}')]
    return mar

help_message = """If you're new, please see the [manual](https://happi.sunilkumar70.repl.co/).

*You can control me by sending these commands:*

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
    global table
    sender_id = message.chat.id
    msg = message.text
    # main commands
    if msg=='/join':
        if sender_id in table:
            chat_manager[sender_id] = {'msg':'join_roll'}
            bot.send_message(sender_id, 'You already joined\nroll no {roll}\nname {name}\nTo modify type your roll no\nuse /cancel to dismiss'.\
                format(roll = table[sender_id]['roll'], name = table[sender_id]['name']))
        else:
            chat_manager[sender_id] = {'msg':'join_pin'}
            bot.send_message(sender_id, 'Alright, Enter a pin to continue\n(only for AIML student)')
    elif msg=='/timetable':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        itembtna = types.KeyboardButton('Tuesday')
        itembtnv = types.KeyboardButton('Wednesday')
        itembtnc = types.KeyboardButton('Thursday')
        itembtnd = types.KeyboardButton('Friday')
        itembtne = types.KeyboardButton('Saturday')
        markup.row(itembtna, itembtnv)
        markup.row(itembtnc, itembtnd, itembtne)
        bot.send_message(sender_id, "Choose one day:", reply_markup=markup)
    elif msg=='/leave':
        if sender_id in table and table[sender_id]['role']:
            lis = ['{} {}'.format(table[ele]['roll'], table[ele]['name']) for ele in table if table[ele]['leave']==1]
            te = 'List:\n'+'\n'.join(lis)
            te = 'No absentes' if te=='List:\n' else te
            bot.send_message(sender_id, te)
        elif sender_id in table:
            if table[sender_id]['leave']==1:
                table[sender_id]['leave'] = 0
                te = 'Marked as present'
            else:
                table[sender_id]['leave'] = 1
                te = 'Marked as absent'
            dic_to_data(table)
            bot.send_message(sender_id, te) 
        else:
            bot.send_message(sender_id, 'You are not authorized\nPlease use /join to add your details')
    elif msg=='/mark':
        if table[sender_id]['role']:
            chat_manager[sender_id] = {'msg':'mark_column'}
            bot.send_message(sender_id, 'Enter the column which contain marks:')
        else:
            bot.send_message('This feature is only for teachers(beta)')

    elif msg=='/refresh' and table[sender_id]['role']:
        table = data_to_dic()
        bot.send_message(sender_id, 'table refreshed')
    elif msg=='/reset' and table[sender_id]['role']:
        i = int(get_data('Data', 'f1')[0][0])
        data = [[0] for j in range(i-1)]
        update_data_to(data, 'Data', 'e2')
        bot.send_message(sender_id, 'Reset done.')
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
        chat_manager[sender_id]['msg'] = 'None'
        table[sender_id] = {'name':msg, 'roll':chat_manager[sender_id]['roll'], 'role':False, 'leave':0}
        dic_to_data(table)
        bot.send_message(sender_id, 'Your details added')
    
    # mark operation
    elif sender_id in chat_manager and chat_manager[sender_id]['msg']=='mark_column':
        chat_manager[sender_id]['msg'] = 'mark_text'
        chat_manager[sender_id]['col'] = msg
        bot.send_message(sender_id, 'Exam name?')
    elif sender_id in chat_manager and chat_manager[sender_id]['msg']=='mark_text':
        table = data_to_dic()
        chat_manager[sender_id]['msg'] = 'None'
        mar = get_marks(chat_manager[sender_id]['col'])
        chat_ids = list(table.keys())
        for ele in table:
            if not (table[ele]['role']):
                bot.send_message(ele, f'{msg}\n{mar[chat_ids.index(ele)]}')
        bot.send_message(sender_id, 'Done')
    
    # time talbe function
    elif msg.lower() in days:
        te = get_timetable(msg.lower()[:3])
        bot.send_message(sender_id, te)

    # unknown command
    elif msg.lower().startswith('/'):
        bot.send_message(sender_id, 'Unrecognized command. Say what?')

    # send help command
    else:
        bot.send_message(sender_id, help_message, parse_mode='Markdown')

bot.infinity_polling()