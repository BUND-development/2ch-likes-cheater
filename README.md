# 2ch-likes-cheater
## Накрутка лайков "двачую" для 2ch.hk by BUND


Лайкает ("двачует") посты на сосаче  
ver. 2.0  
Код был полностью реструктурирован, возможны баги на разных платформах!  
### Что нужно для установки?
1. нужен питон версии 3.x и выше. Офф. сайт: `https://www.python.org/`  

### Как стартовать?  
1. Переходим в папку с main.py  
2. Нажимаем в проводнике на путь к файлу  
3. Пишем `cmd` и нажимаем энтер  
4. Прописываем `python main.py`  
Если у вас поставлено 2 питона или не стартует - вместо python пишите python3  


### Как пихать прокси?  
прокси:порт  (пример: 123.123.123.123:1234)    

### А если очень хочется пихать протокол://прокси:порт?  
Тогда открываешь main.py блокнотом и переменную `self.ISPROTOCOLINCLUDE` ставишь True (по дефолту стоит False)    

### А что еще можно поменять в коде?  
`self.FILE` - название файла из которого программа берет прокси  
`self.TIMEOUT` - первое значение в скобках таймаут до сервера, второе таймаут получения ответа от сервера. Желательно чтобы первая цифра была меньше второй  
`self.HOWMANYLIKES` - сколько ставить лайков/дизлайков перед выходом. По дефолту 0 - все зависит от количества проксей. Работает, но урезает потоки.     
`self.HOWMANYALLOW` - в каком диапазоне +- скрипт может пробовать фиксить потоки. Допилено.  
`self.MINTHREADSALLOW` - минимальное значение количества потоков, ниже которого скрипт не будет оптимизировать потоки    
`self.MAXTRIES` - количество попыток отправки лайка  
`self.NORMALINPUT` - вводить ли через аргументы комадной строки данные (`python main.py [доска] [пост] [протокол проксей] [0 - лайк, 1 - дизлайк] [потоки, желательно не больше, чем количество проксей/2]`)  
Примечание для линуксоидов: поскольку в шинде модуль `multiprocessing` работает криво, пришлось заменить его на обычный многопоток. Что повлекло за собой уменьшение производительности в 
системах со слабой мощностью на ядро. Если вы хотите врубить его - то закомментите строчку 273 и раскомментите 274.  


### Ошибки, которые могут возникнуть
Ошибки типа `No module find ....` или `Ошибка загрузки модулей!` обычно бывают, когда скрипт не смог установить или загрузить библиотеки. Попробуйте `pip install requests pysocks urllib3 backoff colorama` для винды или 
`pip3 install --user requests pysocks urllib3 backoff colorama` для Linux.  


В коде есть много комментариев, так что фанатские фиксы и допилы не составят труда.  

Вопросы - BUND-development@protonmail.com
