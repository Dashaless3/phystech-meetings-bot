import socket
import os
import requests.exceptions
import urllib3.exceptions
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api import VkUpload

helplist = [
    'Команды:',
    '!рег - создать физтех.никнейм для анонимного общения (без регистрации не получится)',
    '!ник - посмотреть свой текущий физтех.никнейм',
    '!удалить - удалить физтех.никнейм',
    '!помощь - прочитать список команд',
    '!ивент - регистрация на ивент',
    '',
    'Чтобы отправить сообщение человеку с физтех.никнеймом alias, используйте такой синтаксис:',
    ': alias',
    'Текст сообщения',
    '',
    'Сообщение от человека с физтех.никнеймом alias будет выглядеть так:',
    'alias :',
    'Текст сообщения',
    '',
    'Внимание! Вложения (такие, как картинки, видео, музыка и т.п.) и пересланные сообщения не отправляются адресату.'
    ]
HELP = '\n'.join(helplist)
REGISTRATION = 'registration.txt'
NICKNAMES = 'nicknames.txt'
DELETION = 'deletion.txt'

vk_session = vk_api.VkApi(token="your_token")


def format(text):
    dict = {"&lt;" : "\<", "&rt;" : "\>", "&amp" : "\&", "&quot;" : "\""}
    for i in dict.keys():
        text = text.replace(i, dict[i])
    return text

def send_msg(user_id, text, attachments=None, keyboard=None):
    text = format(text)
    post = {
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }
    if attachments is not None:
        post['attachment'] = ','.join(attachments)
    if keyboard is not None:
        post["keyboard"] = keyboard.get_keyboard()
    return vk_session.method("messages.send", post)


def check(user_id, action):
    stage = 0
    if action == "del":
        f = open(DELETION, "r")
        for line in f.readlines():
            if int(line.strip('\n')) == user_id:
                stage = 1
        f.close()
    elif action == "reg":
        f = open(REGISTRATION, "r")
        stage = 0
        for line in f.readlines():
            if int(line.split()[0]) == user_id:
                stage = int(' '.join(line.split()[1:]).strip('\n'))
        f.close()
    else:
        raise ValueError("No such file")
    return stage


def unique(nickname):
    f = open(NICKNAMES, "r")
    flag = 1
    for line in f.readlines():
        if ' '.join(line.split()[1:]).strip('\n') == nickname:
            flag = 0
    f.close()
    return flag


session_api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
upload = VkUpload(vk_session)

while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:  # сообщение отправлено пользователем в чат с ботом
                msg = event.text
                user_id = event.user_id
                try:
                    if msg[0] == "!":
                        # на всякий случай убираем из списка удаляющихся, если он там есть
                        with open(DELETION, "r") as del_:
                            lines = del_.readlines()
                        with open(DELETION, "w") as del_:
                            for line in lines:
                                if int(line.strip('\n')) != user_id:
                                    del_.write(line)
                        # из списка регистрирующихся тоже (stage == 1, не 2)
                        with open(REGISTRATION, "r") as reg:
                            lines = reg.readlines()
                        with open(REGISTRATION, "w") as reg:
                            for line in lines:
                                if int(line.split()[0]) != user_id:
                                    reg.write(line)
                                elif int(line.split()[0]) == user_id and int(' '.join(line.split()[1:])) == 2:
                                    reg.write(line)
                        if msg == "!помощь":  # пользователь запрашивает инструкцию
                            send_msg(user_id, HELP)
                        elif msg == "!ивент":
                            nicks = open(NICKNAMES, "r")
                            nick = 0
                            flag = 0
                            for line in nicks.readlines():
                                if int(line.split()[0]) == user_id:
                                    flag = 1
                                    nick = ' '.join(line.split()[1:])
                            nicks.close()
                            if not flag:
                                send_msg(user_id, "Пожалуйста, сперва зарегистрируйтесь командой !рег")
                            else:
                                send_msg(606984967, "Ивент vk.com/id" + str(user_id) + ' ' + nick)
                                send_msg(user_id, "Вы зарегистрированы на ивент!")
                        elif msg == "!рег":  # пользователь хочет зарегистрироваться (неожиданно)
                            reg = open(REGISTRATION, "r")
                            stage = 0
                            for line in reg.readlines():
                                if int(line.split()[0]) == user_id:
                                    stage = int(' '.join(line.split()[1:]).strip(
                                        '\n'))  # этап регистрации: 1 - ввел команду, но не никнейм, 2 - уже ввел никнейм
                            reg.close()
                            if stage == 2:
                                send_msg(user_id,
                                         "Вы уже зарегистрированы. Чтобы поменять физтех.никнейм, сперва удалите старый командой "
                                         "!удалить")
                            if stage == 0:  # еще не было регистрации
                                reg = open(REGISTRATION, "a")
                                reg.write(str(user_id) + ' 1\n')
                                send_msg(user_id, "Введите желаемый физтех.никнейм")
                                reg.close()
                        elif msg == "!удалить":  # пользователь хочет удалить никнейм
                            nicks = open(NICKNAMES, "r")
                            stage = 0
                            for line in nicks.readlines():
                                if int(line.split()[0]) == user_id:
                                    stage = 1
                            if stage:
                                del_ = open(DELETION, "w+")
                                stage = 0
                                for line in del_.readlines():
                                    if int(line.strip('\n')) == user_id:
                                        stage = 1
                                if not stage:
                                    del_.write(str(user_id) + '\n')
                                del_.close()
                                keyboard = VkKeyboard(inline=True)
                                keyboard.add_button(label="Да")
                                keyboard.add_button(label="Нет")
                                send_msg(user_id, "Вы уверены?", keyboard=keyboard)
                            else:
                                send_msg(user_id, "Вы еще не зарегистрированы - невозможно удалить физтех.никнейм! Для того, чтобы зарегистрироваться, напишите !рег")

                        elif msg == '!ник':  # пользователь хочет посмотреть свой никнейм
                            f = open(NICKNAMES, "r")
                            flag = 0
                            nick = 0
                            for line in f.readlines():
                                if int(line.split()[0]) == user_id:
                                    flag = 1
                                    nick = ' '.join(line.split()[1:])
                            if flag:
                                send_msg(user_id, "Ваш физтех.никнейм: " + nick)
                            else:
                                send_msg(user_id, "Вы еще не зарегистрированы. Для того, чтобы зарегистрироваться, напишите !рег")
                            f.close()
                        else:
                            send_msg(user_id, "Неопознанная команда. Для получения списка команд напишите !помощь")
                    elif msg[0] == ":":
                        print(msg)
                        try:
                            rec_nick = msg.split('\n')[0].split()[1]
                            rec_id = 0
                            sen_nick = None
                            with open(NICKNAMES, "r") as nicks:
                                for line in nicks.readlines():
                                    if line.strip('\n').split()[1] == rec_nick:
                                        rec_id = line.split()[0]
                                    if int(line.split()[0]) == user_id:
                                        sen_nick = line.strip('\n').split()[1]
                            if sen_nick is None:
                                send_msg(user_id, "Чтобы отправлять сообщения, пожалуйста, зарегистрируйтесь командой !рег")
                            else:
                                if rec_id == 0:
                                    send_msg(user_id, "Человек с таким физтех.никнеймом не найден")
                                else:
                                    if msg.find('\n') == -1:
                                        msg_to_send = sen_nick + ' :\n'
                                    else:
                                        msg_to_send = sen_nick + ' :\n' + msg[msg.find('\n') + 1:]
                                    att = event.attachments
                                    att_to_send = []
                                    att_list = list(att.values())
                                    for i in range(0, len(att_list), 2):
                                        att_to_send.append(att_list[i] + '-' + att_list[i + 1])
                                    print(att_to_send)
                                    send_msg(rec_id, msg_to_send, att_to_send)
                        except IndexError:
                            send_msg(user_id, "Вы забыли указать физтех.никнейм получателя")
                    else:  # не команда
                        if msg == "Да":  # пизда; что значит "да"? проверяем все возможные случаи
                            # это может быть попытка удалиться
                            stage = check(user_id, "del")
                            if stage:  # тогда он и правда удаляется
                                # сначала убираем челика из списка удаляющихся
                                with open(DELETION, "r") as del_:
                                    lines = del_.readlines()
                                with open(DELETION, "w") as del_:
                                    for line in lines:
                                        if int(line.strip('\n')) != user_id:
                                            del_.write(line)
                                # потом убираем ник челика
                                with open(NICKNAMES, "r") as nicks:
                                    lines = nicks.readlines()
                                with open(NICKNAMES, "w") as nicks:
                                    for line in lines:
                                        if int(line.split()[0]) != user_id:
                                            nicks.write(line)
                                # также убираем инфу в файле регистрации
                                with open(REGISTRATION, "r") as reg:
                                    lines = reg.readlines()
                                with open(REGISTRATION, "w") as reg:
                                    for line in lines:
                                        if int(line.split()[0]) != user_id:
                                            reg.write(line)
                                send_msg(user_id, "Физтех.никнейм удален")
                            else:  # не удаляется; мб вводит никнейм?
                                stage = check(user_id, "reg")
                                if stage == 1:  # реально регается
                                    flag = unique("Да")
                                    if flag:
                                        nicks = open(NICKNAMES, "a")
                                        nicks.write(str(user_id) + ' Да\n')
                                        nicks.close()
                                        with open(REGISTRATION, "r") as reg:
                                            lines = reg.readlines()
                                        with open(REGISTRATION, "w") as reg:
                                            for line in lines:
                                                if int(line.split()[0]) != user_id:
                                                    reg.write(line)
                                            reg.write(str(user_id) + ' 2\n')
                                        send_msg(user_id, "Отлично, вы зарегистрированы")
                                    else:
                                        send_msg(user_id, "Данный физтех.никнейм занят, пожалуйста, выберите другой")
                                else:  # и не регается, и не удаляется
                                    send_msg(user_id,
                                             "Ваше сообщение не было доставлено. Чтобы узнать список доступных команд, напишите !помощь")
                        elif msg == "Нет":  # тоже проверяем все возможные случаи
                            # это может быть отмена попытки удалиться
                            stage = check(user_id, "del")
                            if stage:  # и правда
                                # убираем челика из списка удаляющихся
                                with open(DELETION, "r") as del_:
                                    lines = del_.readlines()
                                with open(DELETION, "w") as del_:
                                    for line in lines:
                                        if int(line.strip('\n')) != user_id:
                                            del_.write(line)
                                send_msg(user_id, "Удаление отменено")
                            else:  # мб вводит никнейм?
                                stage = check(user_id, "reg")
                                if stage == 1:  # реально регается
                                    flag = unique("Нет")
                                    if flag:
                                        nicks = open(NICKNAMES, "a")
                                        nicks.write(str(user_id) + ' Нет\n')
                                        nicks.close()
                                        with open(REGISTRATION, "r") as reg:
                                            lines = reg.readlines()
                                        with open(REGISTRATION, "w") as reg:
                                            for line in lines:
                                                if int(line.split()[0]) != user_id:
                                                    reg.write(line)
                                            reg.write(str(user_id) + ' 2\n')
                                        send_msg(user_id, "Отлично, вы зарегистрированы")
                                    else:
                                        send_msg(user_id, "Данный физтех.никнейм занят, пожалуйста, выберите другой")
                                else:  # и не регается, и не удаляется
                                    send_msg(user_id,
                                             "Неопознанная команда. Для получения списка команд напишите !помощь")
                        else:  # написал какое-то другое сообщение
                            # на всякий случай убираем из списка удаляющихся, если он там есть
                            with open(DELETION, "r") as del_:
                                lines = del_.readlines()
                            with open(DELETION, "w") as del_:
                                for line in lines:
                                    if int(line.strip('\n')) != user_id:
                                        del_.write(line)
                            # теперь проверяем, регается ли чел
                            stage = check(user_id, "reg")
                            if stage == 1:  # реально регается
                                flag = unique(msg)
                                if flag:
                                    nicks = open(NICKNAMES, "a")
                                    nicks.write(str(user_id) + ' ' + msg + '\n')
                                    nicks.close()
                                    with open(REGISTRATION, "r") as reg:
                                        lines = reg.readlines()
                                    with open(REGISTRATION, "w") as reg:
                                        for line in lines:
                                            if int(line.split()[0]) != user_id:
                                                reg.write(line)
                                        reg.write(str(user_id) + ' 2\n')
                                    send_msg(user_id, "Отлично, вы зарегистрированы")
                                else:
                                    send_msg(user_id, "Данный физтех.никнейм занят, пожалуйста, выберите другой")
                            else:  # не регается
                                send_msg(user_id,
                                         "Ваше сообщение не было доставлено. Чтобы узнать список доступных команд, напишите !помощь")
                except IndexError:
                    send_msg(user_id,
                             "Ваше сообщение не было доставлено. Чтобы узнать список доступных команд, напишите !помощь")
    except (TimeoutError, requests.exceptions.ReadTimeout, socket.timeout, urllib3.exceptions.ReadTimeoutError):
        print('error occured')
        os.system(__file__)
        exit()
