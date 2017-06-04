import os
import sys
import telepot
import requests
import re
import datetime
import calendar
import matplotlib.pyplot as plt
from time import sleep
from bs4 import BeautifulSoup
from settings import token, start_msg, stats_password


# Message handle funtion
def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    chat_id = msg['chat']['id']
    command_input = msg['text']

    # Check which command was submitted
    if command_input == '/start':
        bot.sendMessage(chat_id, start_msg)

    try:
        date = command_input.split()[1]
        command_input = command_input.split()[0]
    except:
        now = datetime.datetime.now()
        date = now.strftime("%d-%m-%Y")

    if command_input == '/duca':
        printLog("{0} - {1}".format(chat_id, command_input))
        date1 = convertDate(date)

        payload = {'mensa': 'DUCA', 'da': date1, 'a': date1}
        msg = getMenu(payload)
        if msg:
            bot.sendMessage(chat_id, '🗓️Mensa Duca - {0}\n\n{1}'.format(date,
                            msg[0]))
            bot.sendMessage(chat_id, msg[1])
        else:
            bot.sendMessage(chat_id, '🗓️Menu Mensa Duca - %s\n\n'
                                     'Non disponibile.\n\n'
                                     '⚠️Attenzione⚠️\n'
                                     'Sabato e domenica il ristorante il /duca'
                                     ' non è aperto, quindi, non troverete '
                                     'nessun menù.' % date)

    if command_input == '/tridente':
        printLog("{0} - {1}".format(chat_id, command_input))
        date1 = convertDate(date)

        payload = {'mensa': 'TRIDENTE', 'da': date1, 'a': date1}
        msg = getMenu(payload)

        if msg:
            bot.sendMessage(chat_id, '🗓️Mensa Tridente - {0}\n\n{1}'.format(
                            date, msg[0]))
            bot.sendMessage(chat_id, msg[1])
        else:
            bot.sendMessage(chat_id, '🗓️Menu Mensa Tridente - %s\n\n'
                                     'Non disponibile.' % date)

    if command_input == '/allergeni':
        printLog("{0} - {1}".format(chat_id, command_input))
        bot.sendMessage(chat_id,
                        'http://menu.ersurb.it/menum/Allergeni_legenda.png')

    if command_input == '/crediti':
        printLog("{0} - {1}".format(chat_id, command_input))
        bot.sendMessage(chat_id, "Developed by:\n"
                                 "https://github.com/Radeox\n"
                                 "https://github.com/Fast0n")

    if command_input == '/statistiche':
        try:
            f = open("log.txt", "r")

            # Get current month days
            now = datetime.datetime.now()
            days = calendar.monthrange(now.year, now.month)[1]

            # Create month array
            month_counters = []
            radius = []

            for i in range(days):
                month_counters.append(0)
                radius.append(1)

            # Read input file
            for line in f.readlines():
                date = line.split()[4]
                day, month, year = date.split('/')

                if int(year) == now.year and int(month) == now.month:
                    month_counters[int(day)] += 1

            # Clear plot
            plt.clf()

            # Add titles
            plt.title("Statistiche d'uso {0}/{1}".format(month, year))
            plt.xlabel('Giorni del mese')
            plt.ylabel('Utilizzi')

            # Set grid
            plt.grid()

            # Add plots
            plt.plot(month_counters, color='#0099ff', linewidth=2.5)
            plt.plot(month_counters, 'o', color='#0099ff')
            plt.fill(radius, month_counters)
            x = range(days)
            plt.fill_between(x, month_counters, 0, color='#99d6ff')

            # Save
            plt.savefig('plot.png')
            f = open('plot.png', 'rb')

            # Send to user
            bot.sendPhoto(chat_id, f)

            f.close()
        except FileNotFoundError:
            pass

    if command_input == '/stats':
        # Check stats password
        if date == stats_password:
            try:
                f = open("log.txt", "r")
                msg = 'Statistics on use:\n'

                for counter, line in enumerate(f.readlines(), start=1):
                    # Add counter
                    line = str(counter) + ') ' + line

                    # Check if this user is known
                    tmp = getUserName(line.split()[1])

                    # Replace with name if exists
                    if tmp is not '':
                        line = line.replace(line.split()[1], tmp)

                    # Finally get messagge
                    msg += line

                bot.sendMessage(chat_id, msg)
                f.close()
            except FileNotFoundError:
                pass

        else:
            bot.sendMessage(chat_id, "⚠️Password errata!⚠️")


# Get the menu from the ERSU page
def getMenu(payload):
    r = requests.post("http://menu.ersurb.it/menum/menu.asp", data=payload)

    empty = True
    status = False
    rvp = '☀️Pranzo:\n'
    rvc = '🌙Cena:\n'
    rv0 = '\n🍝Primi:\n'
    rv1 = '\n🍖Secondi:\n'
    rv2 = '\n🍟Contorno:\n'
    rv3 = '\n🍨Frutta/Dolce:\n'

    soup = BeautifulSoup(r.text, 'html.parser')

    for link in soup.find_all('a')[1:]:
        try:
            # Get ID
            app = link.get('onclick')
            idi = re.findall('(".*?")', app)[1].replace('"', '')

            # Get name
            name = str(re.findall('(">.*?<\/)', str(link)))

            # Remove useless chars
            name = name.replace('''['">''', '').replace(
                                "</']", '').replace('\\', '')

            # Check if launch/dinner
            if idi == '40' and not status:
                status = True
            elif idi == '10' and status:
                status = False
                rvp += rv0 + rv1 + rv2 + rv3
                rv0 = '\n🍝Primi:\n'
                rv1 = '\n🍖Secondi:\n'
                rv2 = '\n🍟Contorno:\n'
                rv3 = '\n🍨Frutta/Dolce:\n'

            # Check plate type
            if idi == '10':
                rv0 += ' • ' + name + '\n'
                empty = False
            elif idi == '20':
                rv1 += ' • ' + name + '\n'
                empty = False
            elif idi == '30':
                rv2 += ' • ' + name + '\n'
                empty = False
            elif idi == '40':
                rv3 += ' • ' + name + '\n'
                empty = False
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)
            pass

    rvc += rv0 + rv1 + rv2 + rv3

    if not empty:
        return [rvp, rvc]
    else:
        return


# Save some statistics on usage
def printLog(msg):
    try:
        f = open("log.txt", "a")

        now = datetime.datetime.now()
        date = now.strftime("%H:%M %d/%m/%Y")

        f.write("{0} {1}\n".format(msg, date))
        f.close()
    except:
        print("Error opening log file!")


# Replace known users in stats
def getUserName(chat_id):
    rv = ''

    try:
        f = open("users.txt")

        for line in f.readlines():
            if line.split()[0] == chat_id:
                rv = line.split()[1]

        f.close()
    except FileNotFoundError:
        pass

    return rv


# Simple function covert MM-DD-YYYY to DD-MM-YYYY
def convertDate(date):
    x, y, z = date.split('-')
    rv = y + '-' + x + '-' + z

    return rv


# Main
print("Starting UnimensaBot...")

# PID file
pid = str(os.getpid())
pidfile = "/tmp/unimensabot.pid"

# Check if PID exist
if os.path.isfile(pidfile):
    print("%s already exists, exiting!" % pidfile)
    sys.exit()

# Create PID file
f = open(pidfile, 'w')
f.write(pid)

# Start working
try:
    bot = telepot.Bot(token)
    bot.message_loop(handle)

    while 1:
        sleep(10)

finally:
    # Remove PID file on exit
    os.unlink(pidfile)
