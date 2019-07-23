# -*- coding: utf-8 -*-

try:
    import sys
    import json
    import requests
    import urllib3
    import threading
    from threading import Thread
    from multiprocessing import Pool
except:
    print("Не были установлены все либы, см. README.txt")
    exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # отключение уведомлений об незащищенности соединения через прокси

try:
    BOARD = str(sys.argv[1])  # доска
    POST = str(sys.argv[2])  # пост
    PROTOCOL = str(sys.argv[3])  # протокол прокси
    if sys.argv[4] == '0':  # если четвертый аргумент 0 - то накручивает лайки, если не равно 0 - дизлайки
        TASK = 'like'
    else:
        TASK = 'dislike'
    THREADS = int(sys.argv[5])  # потоки
except IndexError:
    print("Отсутствуют аргументы")
    exit(1)

#BOARD = 'd'  #доска
#POST = ''  # номер поста
#PROTOCOL = 'http'  # протокол проксей
FILE = 'proxies.txt'  # файл с проксями
ISPROTOCOLINCLUDE = False  # прокси в формате протокол://прокси, ДА или НЕТ
TIMEOUT = (3, 7)  # первый таймаут коннекта до сервера, второй ожидания ответа от сервера
PRINTALL = False  # выводить ответы сервера и дебаг-ответы
HOWMANYLIKES = 0  # сколько накрутить лайков, если 0 - пока не кончатся прокси

# параметры отправки лайка
params = {}
params["task"] = TASK
params["board"] = BOARD
params["num"] = POST
URL = "https://2ch.hk/makaba/likes.fcgi"


class Stats:
    def __init__(self):
        self.success = 0
        self.denied = 0
        self.bad = 0
        self.all = 0

    def add_bad(self):
        self.bad += 1
        self.all += 1

    def add_success(self):
        self.success += 1
        self.all += 1

    def add_denied(self):
        self.denied += 1
        self.all += 1

    def print_stats(self):
        #print('\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@2ch likes poster@@@@@@\n@@@@@@@@@by Afanasiy@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
        print("Всего отправок: {0}".format(self.all))
        print("Всего успешных: {0}".format(self.success))
        print("Всего отклонено: {0}".format(self.denied))
        print("Всего не удалось отправить: {0}".format(self.bad))

    def get_success(self):
        return self.success

stats = Stats()  # инициализация статистики


# обработка прокси в словарь для requests
def initial_proxy():
    file = open(FILE, mode="r").read()
    # разделение прокси листа на сами прокси
    proxy = file.split('\n')
    # удаляем пустую строку, если есть
    try:
        proxy.remove('')
    except ValueError:
        pass
    # если не проставлены протоколы в proxies.txt, то мы их добавляем
    if not ISPROTOCOLINCLUDE:
        for i in range(0, len(proxy)):
            proxy[i] = PROTOCOL + '://' + proxy[i]
    else:
        pass
    # возвращаем список проксей в формате протокол://прокси:порт
    return proxy


# отправка лайка
class Send:
    def __init__(self, proxy, protocol, post, parametrs):
        self.protocol = protocol
        self.proxy = proxy
        # создание словаря с одной проксей
        self.proxies = {}
        self.proxies['https'] = self.proxy
        self.post = post
        self.params = parametrs
        # заголовки
        self.headers = {}
        self.headers["Host"] = "2ch.hk"
        self.headers["User-Agent"] = 'Mozilla/5.0 (Linux; Android 7.1; vivo 1716 Build/N2G47H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36'
        self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        self.headers["Accept-Language"] = "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3"
        self.headers["Accept-Encoding"] = "gzip, deflate, br"
        self.headers["X-Requested-With"] = "XMLHttpRequest"
        self.headers["COOKIE"] = ""
        self.headers["Connection"] = "close"
        self.headers["UPGRADE-INSECURE-REQUESTS"] = "1"
        self.headers["DNT"] = "1"

    # отправка гет запроса с использованием одной прокси
    def sending(self):
        try:
            answ = json.loads(requests.get(URL, params=self.params, proxies=self.proxies, timeout=TIMEOUT, headers=self.headers, verify=False).text)
        except:
            answ = {"Error": -1337}
        return answ


# анализ ответа и удаление прокси из списка
def answ_anal(answ):
    # в зависимости от ответа выводит сообщение и собирает стату
    if answ["Error"] == None:
        print("Отправлено успешно!")
        stats.add_success()
    elif answ["Error"] == -4:
        print("Ошибка, с этой прокси уже лайкали")
        stats.add_denied()
    elif answ["Error"] == -1337:
        print("Ошибка соединения")
        stats.add_bad()
    else:
        print("Неизвестная ошибка> " + str(answ))
    if PRINTALL:
        print(answ)


proxies = initial_proxy()


# запуск скрипта
def main(test):
    for i in proxies:
        if PRINTALL:
            print("Прокся {0} заюзана".format(i))
        elif HOWMANYLIKES > 0 and Stats.get_success() >= HOWMANYLIKES:
            print("Все пролайкано, выключаюсь")
            break
        # инициализация класса для прокси
        send = Send(i, PROTOCOL, POST, params)
        # удаление прокси
        proxies.remove(i)
        # отправка лайка
        answer = send.sending()
        # анализ ответа
        answ_anal(answer)




if __name__ == "__main__":
    with Pool(THREADS) as p:  # многопоток AS IZ
        p.map(main, 'test')
    print('Все потоки запущены')
    stats.print_stats()
