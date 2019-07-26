# -*- coding: utf-8 -*-

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


FILE = 'proxies.txt'  # имя файла с проксями
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
HOWMANYALLOW = 1  # +- в каком диапазоне может скрипт изменять потоки для оптимизации
# не советую менять без понимания кода
# =========================================================================================
MINTHREADSALLOW = 5  # минимальное количество тредов, выше которых будет включена оптимизация с изменением потоков
# не советую менять без понимания кода

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
        print("\n======================================================")
        print("Всего отправок: {0}".format(self.all))
        print("Всего успешных: {0}".format(self.success))
        print("Всего отклонено: {0}".format(self.denied))
        print("Всего не удалось отправить: {0}".format(self.bad))
        print("======================================================\n")

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
            req = backoff.on_exception(backoff.expo, exceptions.ConnectionError, max_tries = 10, jitter = None, max_time = 60)(_get)
            answ = json.loads(req(URL, params=self.params, proxies=self.proxies, timeout=TIMEOUT, headers=self.headers, verify=False).text)
        except:
            answ = {"Error": -1337}  # в случае если превысило таймаут - присваиваю ошибку соединения
        return answ


# анализ ответа и удаление прокси из списка
def answ_anal(answ):
    # в зависимости от ответа выводит сообщение и собирает стату
    if answ["Error"] == None:
        print(colored("Отправлено успешно!", "green"))
    elif answ["Error"] == -4:
        print(colored("Ошибка: с этой прокси уже лайкали!", "red"))
    elif answ["Error"] == -8:
        pass  # это ошибка, когда одна и та же прокся используется подряд. костыль, да
    elif answ["Error"] == -1337:
        print(colored("Ошибка: не удалось получить ответ сервера!", "red"))
    else:
        print(colored(("Неизвестная ошибка> " + str(answ)), "red"))
    if PRINTALL:
        print(answ)
    if HOWMANYLIKES and answ["Error"]==None:
        return 1
    elif HOWMANYLIKES:
        return 0


proxies = initial_proxy()  # получаю список проксей из файла FILE
howmany = 0  # переменная количества выдач проксей

def thinking():
    global THREADS
    # скрипт пробует уменшить или увеличить количество потоков на HOWMANYALLOW для оптимизации
    if (THREADS-HOWMANYALLOW) and (len(proxies) % (THREADS-HOWMANYALLOW) == 0) and THREADS > MINTHREADSALLOW:
        if PRINTALL:
            print("Подкорректированы потоки в -")
        THREADS -= 1
        obj = len(proxies) // THREADS
    elif (THREADS) and (len(proxies) % (THREADS+HOWMANYALLOW) == 0) and THREADS > MINTHREADSALLOW:
        if PRINTALL:
            print("Подкорректированы потоки в +")
        THREADS += 1
        obj = len(proxies) // THREADS
    # если не получилось - расчитывает количество проксей и создает дополнительный поток для оставшихся
    else:
        obj = len(proxies) // THREADS
    return obj


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
    elif obj:  # точка остановки в случае ошибки расчета проксей
        ret = proxies[0:obj]  # извлечение среза из общего списка проксей
        del proxies[0:obj]  # удаление среза из общего списка проксей
        return ret  # возвращение расчитанной дозы проксей
    else:
        print('Критическая ошибка!')
        exit(1)


# запуск скрипта
def main(proxy):
    if HOWMANYLIKES:  # локальная переменная успешных отправок
        stats = 0
    for i in proxy:
        if PRINTALL:  # иф дебаггера, см. README
            print("Прокся {0} заюзана".format(i))
            print("Пролайкано {0} раз".format(str(stats)))

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
