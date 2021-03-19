from datetime import datetime

import telebot
import requests
import time
import threading

token = 'token'
bot = telebot.TeleBot(token=token)


ACTIVE_USERS = []


def how_many_confirmations(wallet):
    try:
        link = f'https://www.blockchain.com/btc/address/{wallet}'
        point = '</span></div><div><span class="sc-1rs1xpb-0 ktfYhX sc-1mclc94-0'
        r = requests.get(link).text
        transaction_info = r[r.index(point):r.index(point) + 139]
        if 'Unconfirmed' in transaction_info:
            return 0
        else:
            return int(transaction_info[transaction_info.index('Confirmation') - 2])
    except ValueError:
        return f"'{wallet}' – неверный кошелек или отсутствуют активные транзакции. Попробуйте другой."
    except Exception as e:
        with open('Errors.txt', 'a') as errorList:
            errorList.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]: {str(e)}\n')


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Введите btc-кошелек')


@bot.message_handler(commands=['ShowMeActiveUsers'])
def show_active_users(message):
    if message.from_user.id == 279876772:
        print({str(i): ACTIVE_USERS.count(i) for i in set(ACTIVE_USERS)})


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Введите btc-кошелек')

    userdata = f'{message.from_user.username}, id {message.from_user.id}'
    with open('Users.txt', 'r') as userList:
        if userdata not in userList.read():
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'New user: {message.from_user.first_name} {message.from_user.last_name}')
            with open('Users.txt', 'a') as userList1:
                userList1.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                                f'@{message.from_user.username}, id {message.from_user.id}, '
                                f'{message.from_user.first_name} {message.from_user.last_name}\n')


@bot.message_handler(content_types=['text'])
def send_text(message):

    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
          f'New Message (from {message.from_user.first_name} {message.from_user.last_name})')
    with open('Logs.txt', 'a') as userList:
        userList.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                       f'[@{message.from_user.username}, id {message.from_user.id}, '
                       f'{message.from_user.first_name} {message.from_user.last_name}]: '
                       f'{message.text} \n')

    confirmations = how_many_confirmations(message.text)

    if type(confirmations) != int:
        bot.send_message(message.chat.id, how_many_confirmations(message.text))
    else:
        if confirmations > 1:
            bot.send_message(message.chat.id, f'У последней транзакции на кошельке'
                                              f' {message.text} уже есть 2 подтверждения!')
        if 0 <= confirmations <= 1:
            ACTIVE_USERS.append(message.from_user.id)
            if ACTIVE_USERS.count(message.from_user.id) > 3:
                bot.send_message(message.chat.id, 'Следить можно не более чем за тремя '
                                                  'кошельками одновременно')
                ACTIVE_USERS.remove(message.from_user.id)
            else:
                if confirmations == 0:
                    bot.send_message(message.chat.id, f'Принял! Сейчас у последней транзакции на кошельке'
                                                      f' {message.text} ни одного подтверждения. '
                                                      'Я уведомлю, как только их будет два.')
                if confirmations == 1:
                    bot.send_message(message.chat.id, 'Принял! Сейчас у последней транзакции на кошельке'
                                                      f' {message.text} одно подтверждение. '
                                                      'Я уведомлю, как только их будет два.')
                time.sleep(10)

                def confirmations_monitoring():
                    while True:
                        try:
                            if how_many_confirmations(message.text) > 1:
                                bot.send_message(message.chat.id, f'Два подтверждения! (кошелёк {message.text})')
                                ACTIVE_USERS.remove(message.from_user.id)
                                break
                            time.sleep(30)
                        except TypeError:
                            pass

                t = threading.Thread(target=confirmations_monitoring)
                t.start()


bot.polling(none_stop=True)
