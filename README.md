# 2ch-likes-cheater
##Накрутка лайков "двачую" для 2ch.hk by BUND


Лайкает ("двачует") посты на сосаче
ver. 1.2
###Что нужно для установки?
-нужен питон версии 3.x и выше
-так же pip install requests requests[socks4] urllib3

Как стартовать? 
`python main.py [доска] [пост] [протокол проксей] [0 - лайк, 1 - дизлайк] [потоки, желательно не больше 50 для стабильной работы]`
Если у вас поставлено 2 питона или не стартует - вместо python пишите python3

Как пихать прокси? 
прокси:порт

А если очень хочется пихать протокол://прокси:порт? 
Тогда открываешь main.py блокнотом и переменную ISPROTOCOLINCLUDE ставишь True (по дефолту стоит False)

А что еще можно поменять в коде?
FILE - название файла из которого программа берет прокси
TIMEOUT - первое значение в скобках таймаут до сервера, второе таймаут получения ответа от сервера. Желательно чтобы первая цифра была меньше второй
PRINTALL - переменная вывода ответа сервера и дебаг-ответов, (по дефолту False). Если хочешь выводить каждый ответ сервера макабы полностью - меняй на True, ответ "-1337" значит, что прокся мертвая. -4 пост уже лайкали. null/None - пост успешно пролайкан
HOWMANYLIKES - сколько ставить лайков/дизлайков перед выходом. По дефолту 0 - все зависит от количества проксей. 

В коде есть много комментариев, так что фанатские фиксы и допилы не составят труда.

Вопросы - BUND-development@protonmail.com
