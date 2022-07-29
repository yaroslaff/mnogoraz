#!/usr/bin/env python3

import telebot
import os
import sqlite3
import argparse
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv('API_TOKEN'))

dbname = None

# Handle '/start' and '/help'
@bot.message_handler(commands=['regplace'])
def send_welcome(message):
    print(message.text)
    place = message.text.split(' ', maxsplit=1)[1]

    print("register place", place)
    u = message.from_user
    print(f"Got message from #{u.id} @{u.username} {u.first_name} {u.last_name}")

    with closing(sqlite3.connect(dbfile)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT INTO place (name, owner) VALUES (?, ?)",
            (place, u.id)
        )

    bot.send_message(message.chat.id, message.text)

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")



@bot.message_handler(commands=['help', 'start', 'place'])
def send_welcome(message):
    print(message)
    bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")




# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    u = message.from_user
    print(u)
    print(f"Got message from #{u.id} @{u.username} {u.first_name} {u.last_name}")

    bot.send_message(message.chat.id, message.text)


def get_args():
    def_dbfile = os.getenv('DBFILE', 'mnogo.db')

    parser = argparse.ArgumentParser()
    parser.add_argument('--init', default=False, action='store_true', help='Initialize database')
    parser.add_argument('-t', '--token', default=os.getenv('API_TOKEN'))
    parser.add_argument('-d', '--dbfile', default=def_dbfile)

    return parser.parse_args()

def dbinit():

    with closing(sqlite3.connect(dbfile)) as connection:
        print("connection:", connection)
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE place (id INTEGER PRIMARY KEY, name TEXT, desc TEXT, owner INTEGER)")
            cursor.execute("CREATE TABLE visit (id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, person INTEGER, FOREIGN KEY (place_id) REFERENCES place (id) ON DELETE CASCADE ON UPDATE NO ACTION)")        

def main():
    global dbfile
    
    args = get_args()

    dbfile = args.dbfile

    if args.init: 
        print("init db", args.dbfile)
        dbinit()
    else:
        bot.infinity_polling()

if __name__ == '__main__':
    main()

