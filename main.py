# -*- coding: utf-8 -*-

import os
# функция очистки экрана
def cls():
    os.system('cls' if os.name=='nt' else 'clear')  # очистка командной строки


# автоматическая установка всех либ для линупсов и шинды
try:
    os.system("pip install requests pysocks urllib3 backoff colorama" if os.name=="nt" else "pip3 install --user requests pysocks urllib3 backoff colorama")
except:
    pass
finally:
    cls()   # очистка командной строки


try:
    import sys
    import json
    from requests import get as _get
    from requests import exceptions
    import urllib3
    from multiprocessing import Process
    import backoff
    from abc import ABC, abstractmethod
    import colorama
    colorama.init()
    # ----
    import threading
except:
    print("Ошибка загрузки модулей! см. README.md")
    exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # отключение уведомлений об незащищенности соединения через прокси


def coloring(string, color):
    if color == "red":
        string = "\x1b[31m" + string + "\x1b[0m"
    elif color == "green":
        string = "\x1b[32m" + string + "\x1b[0m"
    elif color == "yellow":
        string = "\x1b[33m" + string + "\x1b[0m"
    elif color == "blue":
        string = "\x1b[34m" + string + "\x1b[0m"
    else:
        pass
    if os.name == "nt":
        string = string + "\n"
    return string


class Data(ABC):
    '''Абстрактный класс с данными'''

    def __init__(self):
        # =========================================================================================
        self.FILE = 'proxies.txt'  # имя файла с проксями
        # =========================================================================================
        self.REPORT = "report.json"  # пока не нужно
        # =========================================================================================
        self.URL = "https://5.61.239.35/makaba/likes.fcgi"  # айпи сервера сосача
        # =========================================================================================
        self.ISPROTOCOLINCLUDE = False  # прокси в формате протокол://прокси, ДА или НЕТ
        # =========================================================================================
        self.TIMEOUT = (15, 20)  
        '''
        Первая цифра - таймаут ожидания коннекта до сервера, второй таймаут ожидания ответа
        можно поставить вторую цифру на 1 чтобы ускорить максимально скрипт, но тогда нельзя будет
        подтвердить успешную отправку
        '''
        # =========================================================================================
        self.PRINTALL = False  # пока не нужно
        # =========================================================================================
        self.HOWMANYLIKES = 0  # Лимит на количество лайков. При изменении на любое число ставит 1 поток
        # =========================================================================================
        self.HOWMANYALLOW = 5  # +- в каком диапазоне может скрипт изменять потоки для оптимизации
        # не советую менять без понимания кода
        # =========================================================================================
        self.MINTHREADSALLOW = 10  # минимальное количество потоков, ниже которого не будет включаться оптимизация
        # должно быть больше HOWMANYALLOW, иначе большая вероятность сломать скрипт
        # =========================================================================================
        self.MAXTRIES = 3  # количество попыток отправки лайка с каждой прокси
        # =========================================================================================
        self.NORMALINPUT = False  # использовать аргументы командной строки
        # =========================================================================================
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



class Proxies(Data):
    '''Класс работы с проксями'''
    
    def __init__(self):
        super().__init__()
        self.proxies_list = []  # список с проксями

    def get_proxies_from_txt(self):
        '''Получение списка проксей из FILE'''
        with open(self.FILE, mode='r') as file:  # безопасное открытие файла
            self.proxies_list = file.read().split("\n")  # чтение файла и разделение полученной строки.
            try:
                self.proxies_list.remove('')  # удаление пустого элемента строки из массива, если он есть
            except ValueError:
                pass
        if not self.ISPROTOCOLINCLUDE:  # если протокол не вписан в файле
            for i in range(0, len(self.proxies_list)):
                self.proxies_list[i] = self.PROTOCOL + '://' + self.proxies_list[i]  # заменям прокси формата 0.0.0.0 на протокол://0.0.0.0
        else:
            pass



class Optimisation(Data):
    '''Класс оптимизации потоков'''
    
    def __init__(self):
        self.coef = None  # сколько выдавать проксей 
        super().__init__()

    def optim(self):
        '''Оптимизация потоков, ничего не менял с прошлой версии'''
        
        if len(self.proxies_list) % self.THREADS and self.THREADS >= self.MINTHREADSALLOW:
            if self.THREADS > len(self.proxies_list):  # если потоков больше, чем проксей
                self.THREADS = len(self.proxies_list) // 2
            for variable in range(self.THREADS - self.HOWMANYALLOW, self.THREADS + self.HOWMANYALLOW + 1):
                if len(self.proxies_list) % self.THREADS:
                    continue
                else:
                    self.THREADS = variable
                    print("Потоки скорректированы до {0}!".format(str(variable)),)
        else:
            print("Потоков меньше, чем разрешено изменять. Использование без изменений...")

    def setting_coef(self):
        self.coef = len(self.proxies_list) // self.THREADS  # получение количества проксей на 1 поток
        if len(self.proxies_list) % self.THREADS:  # если прокси в списке делятся с остатком на потоки
            self.THREADS += 1  # добавление замыкающего потока для сброса остатков проксей
        else:
            pass



class Getting(Data):
    '''Класс получения проксей и вводимых данных'''
    
    def __init__(self):
        self.params = {}  # параметры запроса
        self.PROTOCOL = None  # перменная протокола
        self.THREADS = None  # переменная потоков
        super().__init__()

    def get_part_proxies(self):
        '''Выдача среза из списка проксей в зависимости от coef'''
        if len(self.proxies_list) <= self.coef:  # если это последняя партия проксей
            pack_of_proxy = self.proxies_list  # копирование остатка списка
            #self.proxies_list.clear()  # очистка списка, нужно для кореектного деббагинга
            return pack_of_proxy
        else:
            pack_of_proxy = self.proxies_list[0:self.coef]  # получение среза проксей для потока
            del self.proxies_list[0:self.coef]  # удаление среза
            return pack_of_proxy
    
    def get_data(self):
        '''Получение данных'''
        if self.NORMALINPUT:  # если ввод из аргументов командной строки
            self.params = {
            "task": None,
            "board": sys.argv[1],
            "num": sys.argv[2],
            }
            if sys.argv[4]:
                self.params["task"] = "dislike"
            else:
                self.params["task"] = "like"
            self.PROTOCOL = sys.argv[3]
            self.THREADS = int(sys.argv[5])
        else:  # если ввод через input
            self.params = {
            "task": input(coloring("Двачую или рейдж (like/dislike)> ", "white")),
            "board": input(coloring("Введите доску> ", "white")),
            "num": input(coloring("Введите пост> ", "white")),
            }
            self.PROTOCOL = input(coloring("Введите протокол (http/socks4/socks5)> ", "white"))
            self.THREADS = int(input(coloring("Введите потоки> ", "white")))

        if self.HOWMANYLIKES:
            print(coloring("Форсирование на 1 поток!", "yellow"))
            self.THREADS = 1



class Posting(Data):
    '''Класс отправки'''
    
    def __init__(self):
        super().__init__()
    
    def sending(self, proxy):
        # одиночный словарь с проксей
        self.proxies = {"https": proxy}
        self.answer = {"Error": "NoName"}
        try:
            # создание запроса с обработкой исключений с помощью backoff
            req = backoff.on_exception(backoff.expo, exceptions.ConnectionError, max_tries = self.MAXTRIES, jitter = None, max_time = 30)(_get)
            # отправка самого лайка
            self.answer = json.loads(req(self.URL, params=self.params, proxies=self.proxies, timeout=self.TIMEOUT, headers=self.headers, verify=False).text)
        except KeyboardInterrupt:
            print(coloring("Выключение...", "yellow"))
            self.answer = {"Error": -8}
            self.exit = True
        except:
            self.answer = {"Error": -1337}  # если не удалось отправить, то присваиеваем ошибку 
        Posting.answer_analising(self, self.answer)  # просто анализ ответа и вывод
    
    def answer_analising(self, answer):
        # в зависимости от ответа выводит сообщение и собирает стату
        if answer["Error"] == None:
            print(coloring("Отправлено успешно!", "green"))
            if self.HOWMANYLIKES:
                self.cheker += 1
        elif answer["Error"] == -4:
            print(coloring("Ошибка: с этой прокси уже лайкали!", "yellow"))
        elif answer["Error"] == -8:
            pass  # это ошибка, когда попадается одини тот же айпи
        elif answer["Error"] == -1337:
            print(coloring("Ошибка: не удалось получить ответ сервера!", "red"))
        else:
            print(coloring("Неизвестная ошибка> " + str(answer["Error"]), "red"))

    def start_sending(self, list):
        if self.HOWMANYLIKES:
            self.cheker = 0
        for i in list:
            if self.exit:
                print(coloring("Поток обнаружил запрос на выключение...", "yellow"))
                break
            elif self.HOWMANYLIKES and self.cheker >= self.HOWMANYLIKES:
                print(coloring("Достигнут лимит лайков! Выключение...", "yellow"))
                break
            Posting.sending(self, i)  # запуск метода отправки



class Main(Optimisation, Getting, Posting, Proxies):
    '''Основной класс для запуска остального кода'''
    
    def __init__(self):
        self.exit = False
        super().__init__()
    


    def main_main(self):
        '''Запускающий метод'''
        Main.get_data(self)  # получение входящих данных
        Main.get_proxies_from_txt(self)  # загружаем и обрабатываем прокси
        Main.optim(self)  # оптимизируем потоки
        Main.setting_coef(self)  # получение коэфецента выдачи проксей на один поток
        for j in range(0, self.THREADS):  # магия многопотока
            instr = Main.get_part_proxies(self)
            proc = threading.Thread(target=Main.start_sending, args=(self, instr))  # многопоток под мультиплатформу
            #proc = Process(target=Main.start_sending, args=(self, instr))  # многопоток для линуксоидов
            proc.start()
        print(coloring("Все потоки запущены!", "green"))
        
        while False:  # заготовка на будущее
            past_input = input("")
            if past_input == "q":
                self.exit = True
                print("Выключение...")
            else:
                print("Неизвестная команда!")
                continue



if __name__ == "__main__":
    starting = Main()  # инициация основного класса
    starting.main_main()  # запуск основного метода основного класса
