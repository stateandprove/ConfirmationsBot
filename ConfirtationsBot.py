from datetime import datetime

import time
import threading

import telebot
import requests


token = <TOKEN>
bot = telebot.TeleBot(token=token)


ACTIVE_USERS = []


def get_transaction_hash(wallet):
    """
    Parses the response from blockchain.com and returns
    a hash of the last transaction in a wallet
    """

    try:
        link = f'https://www.blockchain.com/btc/address/{wallet}'
        point = 'class="sc-1r996ns-0 fLwyDF sc-1tbyx6t-1 kCGMTY iklhnl-0 eEewhk"'
        r = requests.get(link).text
        txhash = r[r.find(point)+76:r.find(point)+140]
        return txhash
    except Exception:
        pass


def how_many_confirmations(transaction_hash):
    """
    Parses the response from blockchain.com and returns a number
    of confirmations of a transaction with the certain hash
    """

    try:
        link = f'https://www.blockchain.com/btc/tx/{transaction_hash}'
        point = '</span></div><div><span class="sc-1rs1xpb-0 ktfYhX sc-1mclc94-0'
        r = requests.get(link).text
        transaction_info = r[r.index(point):r.index(point) + 139]
        if 'Unconfirmed' in transaction_info:
            return 0
        else:
            return int(transaction_info[transaction_info.index('Confirmation') - 2])
    except ValueError:
        return "NULL"
    except Exception:
        pass


@bot.message_handler(commands=['ShowMeActiveUsers'])
def show_active_users(message):
    """
    Admin command for displaying active users
    """
    if message.from_user.id == <ADMIN_ID>:
        print({str(i): ACTIVE_USERS.count(i) for i in set(ACTIVE_USERS)})


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ 
    Handling the /start command 
    """
    bot.send_message(message.chat.id, 'Введите btc-кошелек и количество подтверждений, по достижении которого '
                                      'выслать уведомление, через запятую в формате "wallet, confirm_num"')

    # Implementing user logging
    userdata = f'{message.from_user.username}, id {message.from_user.id}'
    with open('Users.txt', 'r') as userList:
        if userdata not in userList.read():
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} New user: '
                  f'{message.from_user.first_name} {message.from_user.last_name}')
            with open('Users.txt', 'a') as userList1:
                userList1.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                                f'@{message.from_user.username}, id {message.from_user.id}, '
                                f'{message.from_user.first_name} {message.from_user.last_name}\n')


@bot.message_handler(commands=['help'])
def send_help(message):
    """ Handling the /help command """
    bot.send_message(message.chat.id, 'Введите btc-кошелек и количество подтверждений, по достижении которого '
                                      'выслать уведомление, через запятую в формате "wallet, confirm_num"')


@bot.message_handler(content_types=['text'])
def main_function(message):
    """
    Main messages handler
    """

    # Implementing messages logging
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} New Message '
          f'(from {message.from_user.first_name} {message.from_user.last_name})')
    with open('Logs.txt', 'a') as msgLog:
        msgLog.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                     f'[@{message.from_user.username}, id {message.from_user.id}, '
                     f'{message.from_user.first_name} {message.from_user.last_name}]: '
                     f'{message.text}\n')

    msg_text = message.text.split(", ")
    wallet_num = msg_text[0]
    tx_hash = get_transaction_hash(wallet_num)
    time.sleep(0.2)
    confirmations = how_many_confirmations(tx_hash)

    if len(msg_text) != 2:
        bot.send_message(message.chat.id, "Неверный формат ввода")
    elif not msg_text[1].isdigit():
        bot.send_message(message.chat.id, "Количество подтверждений должно быть целым числом от 1 до 5")
    elif not 1 <= int(msg_text[1]) <= 5:
        bot.send_message(message.chat.id, "Количество подтверждений должно быть целым числом от 1 до 5")
    elif type(confirmations) != int:
        bot.send_message(message.chat.id, "Неверный кошелек или отсутствуют активные транзакции. Попробуйте снова.")
    elif confirmations >= int(msg_text[1]):
        bot.send_message(message.chat.id, f'У последней транзакции на кошельке'
                                          f' {wallet_num} подтверждений больше, чем {msg_text[1]}')
    else:

        ACTIVE_USERS.append(message.from_user.id)

        if ACTIVE_USERS.count(message.from_user.id) > 3:
            bot.send_message(message.chat.id, 'Следить можно не более чем за тремя '
                                              'кошельками одновременно')
            ACTIVE_USERS.remove(message.from_user.id)
        else:
            bot.send_message(message.chat.id, f'Принял!\nКошелёк: {wallet_num}\n'
                                              f'Хэш последней транзации: {tx_hash} \n'
                                              f'Подтверждений сейчас: {confirmations} \n'
                                              f'Я уведомлю, как только будет {msg_text[1]}.')
            time.sleep(5)

            def confirmations_monitoring():
                while True:
                    """
                    Implementing confirmations monitoring.
                    
                    This function executes how_many_confirmations(tx_hash)
                    every 15 seconds until it returns the number of 
                    confirmations higher than required.
                    """

                    try:
                        if how_many_confirmations(tx_hash) >= int(msg_text[1]):
                            bot.send_message(message.chat.id, f'Подтверждений сейчас: {msg_text[1]} '
                                                              f'(хэш {tx_hash[0:5]}...{tx_hash[-5:len(tx_hash)]})')
                            ACTIVE_USERS.remove(message.from_user.id)
                            break
                        time.sleep(15)
                    except TypeError:
                        pass

            t = threading.Thread(target=confirmations_monitoring)
            t.start()


bot.polling(none_stop=True)
