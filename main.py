# -*- coding: utf-8 -*-


import os
# функция очистки экрана
def cls():
    os.system('cls' if os.name=='nt' else 'clear')


# автоматическая установка всех либ для линупсов и шинды
try:
    if os.name != "nt": print("Данной программе может потребоваться исполнение sudo! Если вы против, то завершите ее ctrl+c. Продолжить нажмите Enter")
    input()
    os.system("pip install requests pysocks urllib3 termcolor backoff" if os.name=="nt" else "sudo pip3 install requests pysocks urllib3 termcolor backoff")
except:
    pass
finally:
    cls()


try:
    import sys
    import json
    from requests import get as _get
    from requests import exceptions
    import urllib3
    import threading
    from threading import Thread
    from multiprocessing import Process
    from multiprocessing import Pool
    from termcolor import colored
    import backoff
    from colorama import init, Fore, Back, Style
    init(convert=True)

except:
    print(Fore.RED + "Ошибка библиотек! Попробуйте выполнить установку вручную!")
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
    print(Fore.RED + "Отсутствуют аргументы")
    exit(14)


FILE = 'proxies.txt'  # имя файла с проксями
# =========================================================================================
REPORT = "report.json"  # на данным момент файл, который создастся в случае ошибки оптимизации №12 (см. разбор ошибок)
# =========================================================================================
ISPROTOCOLINCLUDE = False  # прокси в формате протокол://прокси, ДА или НЕТ
# =========================================================================================
TIMEOUT = (15, 25)  # первый таймаут коннекта до сервера, второй ожидания ответа от сервера.
# можно поставить второй таймаут на 1 чтобы ускорить работу. но тогда нельзя будет узнать ответ от сервера и
# не будет работать ограничение на отправленные лайки
# =========================================================================================
PRINTALL = False  # выводить ответы сервера и дебаг-ответы
# =========================================================================================
HOWMANYLIKES = 0  # сколько накрутить лайков. Если больше 0 - то число потоков автоматически становится 1.
# =========================================================================================
HOWMANYALLOW = 5  # +- в каком диапазоне может скрипт изменять потоки для оптимизации
# не советую менять без понимания кода
# =========================================================================================
MINTHREADSALLOW = 10  # минимальное количество потоков, ниже которого не будет включаться оптимизация
# должно быть больше HOWMANYALLOW, иначе большая вероятность сломать скрипт
# =========================================================================================
MAXTRIES = 5  # количество попыток отправки лайка с каждой прокси
# =========================================================================================
# разбор ошибок:
# 12 - критическая ошибка оптимизации потоков, писать нам на почту BUND-development@protonmail.com
# 14 - не все аргументы введены


if HOWMANYLIKES:
    print(colored("Режим лимита лайков, скрипт работает в одном потоке!", "green"))
    THREADS = 1


# параметры отправки лайка
params = {}
params["task"] = TASK
params["board"] = BOARD
params["num"] = POST
URL = "https://2ch.hk/makaba/likes.fcgi"


class Stats:  # пока отложил, из-за мультипотока не работает
    def __init__(self):
        self.success = 0
        self.denied = 0
        self.bad = 0
        self.all = 0

    def add_bad(self):  # счетчик проксей, которые не получили ответ от сервера
        self.bad += 1
        self.all += 1

    def add_success(self):  # счетчик точно поставленных лайков/дизлайков
        self.success += 1
        self.all += 1

    def add_denied(self):  # счетчик проксей, которые получили ответ, но лайк не был принят по каким-то причинам
        self.denied += 1
        self.all += 1

    def print_stats(self):
        print(Fore.GREEN + "\n======================================================")
        print(Fore.CYAN + "Всего отправок: {0}".format(self.all))
        print(Fore.CYAN + "Всего успешных: {0}".format(self.success))
        print(Fore.CYAN + "Всего отклонено: {0}".format(self.denied))
        print(Fore.CYAN + "Всего не удалось отправить: {0}".format(self.bad))
        print(Fore.GREEN + "======================================================\n")

    def get_success(self):
        return self.success


# обработка прокси в словарь для requests
def initial_proxy():
    # чтение из файла проксей
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

    # отправка гет запроса с использованием одной прокси и получения ответа в формате json`а
    def sending(self):
        try:
            req = backoff.on_exception(backoff.expo, exceptions.ConnectionError, max_tries = MAXTRIES, jitter = None, max_time = 60)(_get)
            answ = json.loads(req(URL, params=self.params, proxies=self.proxies, timeout=TIMEOUT, headers=self.headers, verify=False).text)
        except:
            answ = {"Error": -1337}  # в случае если прокся сдохла - присваиваю ошибку соединения
        return answ


# анализ ответа и удаление прокси из списка
def answ_anal(answ):
    # в зависимости от ответа выводит сообщение и собирает стату
    if answ["Error"] == None:
        print(Fore.GREEN + "Отправлено успешно!")
    elif answ["Error"] == -4:
        print(Fore.YELLOW + "Ошибка: с этой прокси уже лайкали!")
    elif answ["Error"] == -8:
        pass  # это ошибка, когда попадается одини тот же айпи
    elif answ["Error"] == -1337:
        print(Fore.RED + "Ошибка: не удалось получить ответ сервера!")
    else:
        print(Fore.GREEN + "Неизвестная ошибка> " + str(answ))
    if PRINTALL:
        print(answ)
    if HOWMANYLIKES and answ["Error"]==None:
        return 1
    elif HOWMANYLIKES:
        return 0


proxies = initial_proxy()  # получаю список проксей из файла FILE
howmany = 0  # переменная количества выдач проксей


# оптимизация потоков
def optim(pr_amount, streams, value):
    if pr_amount % streams:  # оптимизация
        for i in range(streams - value, streams + value + 1):
            if pr_amount % i == 0:  # проверка, подходит ли i значение потоков как четный делитель количества проксей
                streams = i
                print("Потоки скорректированны до {0}".format(str(streams)))
                return streams
            else:
                continue
        return streams
    else:
        return streams


def thinking():
    global THREADS
    if THREADS <= MINTHREADSALLOW:
        return len(proxies) // THREADS
    THREADS = optim(len(proxies), THREADS, HOWMANYALLOW)
    ret = len(proxies) // THREADS
    return ret


if PRINTALL:
    print("Длина прокси-листа: " + str(len(proxies)))

# получение информации о количестве проксей и рассчет пркосей для каждого независимого потока
def get_instructions(obj):
    global howmany
    howmany += 1  # счетчик сколько раз была использована функция, нужно для расчета потоков
    global proxies

    if PRINTALL:
        print(len(proxies))
        print("Запущена функция выдачи массивов проксей")

    if howmany > THREADS:  # заполнение последнего добивающего прокси потока
        ret = proxies
        if PRINTALL:
            print("Последний заполняющий поток")
            print(ret)
        proxies.clear()
        return ret

    elif obj:
        ret = proxies[0:obj]  # извлечение среза из общего списка проксей
        del proxies[0:obj]  # удаление среза из общего списка проксей
        return ret  # возвращение расчитанной дозы проксей
    # дополнительная ошибка

    else:
        print('Критическая ошибка! Просьба отправить report.txt на BUND-development@protonmail.com')
        with open(REPORT, "w") as write_file:
            # создание файла репорта
            report = "Протокол проксей: {0}, потоки: {1}, количество проксей: {2}, сколько разрешено редактировать {3}, минимальное количество потоков: {4}"
            report = report.format( str(PROTOCOL), str(THREADS), str(len(proxies)), str(HOWMANYALLOW), str(MINTHREADSALLOW) )
            json.dump(report, write_file)
        exit(12)


# запуск скрипта
def main(proxy):
    if HOWMANYLIKES:  # локальная переменная успешных отправок
        stats = 0
    for i in proxy:
        if PRINTALL:  # иф дебаггера, см. README
            print("Прокся {0} заюзана".format(i))
            if HOWMANYLIKES: print("Пролайкано {0} раз".format(str(stats)))

        elif HOWMANYLIKES > 0 and stats >= HOWMANYLIKES:  # проверка количества успешных отправок для прокси, см README
            print(colored("Лимит лайков достигнут успешно, выключение...", "green"))
            break
        # инициализация класса для прокси
        send = Send(i, PROTOCOL, POST, params)
        # отправка лайка
        answer = send.sending()
        # анализ ответа
        if HOWMANYLIKES:
            stats += answ_anal(answer)
        else:
            answ_anal(answer)


if __name__ == "__main__":
    print(colored("Скрипт запущен! Загрузка потоков...", "green"))

    if THREADS > len(proxies):  # если потоков больше, чем проксей - то урезаем потоки.
        THREADS = len(proxies)
    obj = thinking()  # анализ потоков
    if len(proxies) % THREADS:
        threads_new = THREADS + 1
    else:
        threads_new = THREADS


    for jj in range(0, threads_new):
        instr = get_instructions(obj)
        proc = Process(target=main, args=(instr,))
        proc.start()
    print('Все потоки запущены!')
