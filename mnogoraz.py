#!/usr/bin/env python3

import telebot
import os
import sqlite3
import argparse
import shlex
from contextlib import closing
from dotenv import load_dotenv
import datetime


load_dotenv()
bot = telebot.TeleBot(os.getenv('API_TOKEN'))

dbname = None

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    s = ''
    u = message.from_user
    chatid = message.chat.id

    args = shlex.split(message.text)
    cmd = args[1] if len(args)>1 else None
    print(f"ADMIN {args}")
    


    if cmd == 'everyn':
        everyn = int(args[2])

        with closing(sqlite3.connect(dbfile)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("UPDATE place SET everyn=? WHERE owner=?", (everyn, u.id))
            connection.commit()

    elif cmd == 'regplace':
        place = args[2]
        with closing(sqlite3.connect(dbfile)) as connection:
            with closing(connection.cursor()) as cursor:
                n = cursor.execute("SELECT COUNT(1) FROM place WHERE owner=?", (u.id, )).fetchone()[0]

                if n>0:
                    bot.send_message(chatid, f"Cannot register new place, you already have {n}")
                    return

                cursor.execute("INSERT INTO place (name, owner, everyn) VALUES (?, ?, ?)",
                (place, u.id, 100)
            )
            connection.commit()
        bot.send_message(chatid, f"Registered place {place}")

    elif cmd == 'place':
        with closing(sqlite3.connect(dbfile)) as connection:
            with closing(connection.cursor()) as cursor:
                r = cursor.execute("SELECT name, desc, everyn FROM place WHERE owner=?", (u.id,)).fetchone()
                if r is None:
                    bot.send_message(chatid, "You have no place")
                    return

                s = f'''
Name: {r[0]}
Desc: {r[1]}
EveryN: {r[2]}
'''
        bot.send_message(chatid, s)

    elif cmd == 'go':
        person = args[2]
        with closing(sqlite3.connect(dbfile)) as connection:
            with closing(connection.cursor()) as cursor:
                placeid, everyn = cursor.execute("SELECT id, everyn FROM place WHERE owner=?", (u.id, )).fetchone()
                r = cursor.execute("INSERT INTO visit (place_id, person, ts) VALUES (?, ?, ?)", (placeid, person, datetime.datetime.now()))
                nvisits = cursor.execute("SELECT COUNT(1) FROM visit WHERE place_id=? AND person=?", (placeid, person )).fetchone()[0]
                bot.send_message(chatid, f"Visit recorded. This is visit {nvisits}")
                if nvisits % everyn == 0:
                    bot.send_message(chatid, "This is BONUS visit!")

            connection.commit()

    elif cmd == 'info':
        person = args[2]
        with closing(sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)) as connection:
            with closing(connection.cursor()) as cursor:
                placeid = cursor.execute("SELECT id FROM place WHERE owner=?", (u.id, )).fetchone()[0]
                visits = cursor.execute("SELECT ts FROM visit WHERE place_id=?", (placeid, )).fetchall()
                for v in visits:
                    s+= f'{v[0].strftime("%Y-%m-%d %H:%M")}\n'
        bot.send_message(chatid, s)


    else:
        bot.send_message(chatid, f'''
/admin subcommands:
  /admin regplace PLACE - register new place
  /admin place - show info about place
  /admin everyn N - report every Nth visit 
  /admin go PERSON - record customer visit
  /admin info PERSON - show info about customer
''')



@bot.message_handler(commands=['g'])
def cmd_g(message):
    try:
        place = message.text.split(' ', maxsplit=1)[1]
    except (ValueError, IndexError) as e:
        bot.send_message(message.chat.id, 'Use: /g CUSTOMER\nExample:\n/g 79131234567')
        return
    



@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.send_message(message.chat.id, """\
/help - 
/regplace PLACE
/dump
""")




@bot.message_handler(commands=['super'])
def cmd_super(message):

    s = ''

    try:
        args = shlex.split(message.text)
    except (ValueError, IndexError) as e:
        bot.send_message(message.chat.id, 'Use: /super CMD [ARGS]\nExample:\n')
        return

    cmd = args[1]

    if cmd == 'dump':
        with closing(sqlite3.connect(dbfile)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT * FROM place")
                s = '\n'.join( str(x) for x in cursor.fetchall())
        bot.send_message(message.chat.id, s)
    
    if cmd in [ 'del', 'delete' ]:
        if args[2] == 'place':
            placeid = int(args[3])
            print("del place", placeid)
            with closing(sqlite3.connect(dbfile)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute("DELETE FROM place WHERE id=?", (placeid,))
                connection.commit()

    else:
        s = '''
/super dump        
/super del place N
'''
        bot.send_message(message.chat.id, s)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
#@bot.message_handler(func=lambda message: True)
#def echo_message(message):
#    u = message.from_user
#    print(u)
#    print(f"Got message from #{u.id} @{u.username} {u.first_name} {u.last_name}")
#
#    bot.send_message(message.chat.id, message.text)


def get_args():
    def_dbfile = os.getenv('DBFILE', 'mnogo.db')

    parser = argparse.ArgumentParser()
    parser.add_argument('--init', default=False, action='store_true', help='Initialize database')
    parser.add_argument('-t', '--token', default=os.getenv('API_TOKEN'))
    parser.add_argument('-d', '--dbfile', default=def_dbfile)

    return parser.parse_args()

def dbinit():

    with closing(sqlite3.connect(dbfile)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE place (id INTEGER PRIMARY KEY, name TEXT, desc TEXT, everyn INT, owner INTEGER)")
            cursor.execute("CREATE TABLE visit (id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, person TEXT, ts timestamp, FOREIGN KEY (place_id) REFERENCES place (id) ON DELETE CASCADE ON UPDATE NO ACTION)")        
        connection.commit()
    print("initialized")

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

