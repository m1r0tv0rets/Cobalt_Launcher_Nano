### Документация по созданию плагинов для Cobalt Launcher Nano

**Содержание:**

1) Введение
2) Структура плагина
3) Примеры плагинов
4) Установка плагинов
5) Регистрация плагина
6) Советы и предостарожности
---

**Введение**

Cobalt Launcher Nano поддерживает расширение функциональности через плагины. Плагины позволяют добавлять новые функции, пользователь может их сам создавать и использовать либо скачивать с помощью команды "установить плагин"

Плагины располагаются в папке:
```
C:\cobalt_launcher_nano_reliz\plugins
```
При запуске лаунчер автоматически загружает все файлы с расширением .py из этой папки.

---

**Структура плагина**

Минимальный плагин представляет собой обычный Python-файл с вызовом переменной command(Глобального слушителя команд):
Можно использовать любые переменные и библиотеки из основного кода. Но сторонние нельзя. 

1) БИБЛИОТЕКИ

```python
# библиотеки для плагинов
import math
import random

# pip install minecraft_launcher_lib colored 
import minecraft_launcher_lib
from colored import fg, attr

import os
import sys
import webbrowser
import subprocess
import shutil
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
import zipfile
import json
```
2) ЦВЕТНЫЕ КОМАНДЫ
Для Цветного вывода команд можно использовать Переменные по типу RED, GREEN, BLUE а в конце обязательно использовать COLOR_END. И обязательно чтобы пайтон считывал переменные в комментарии ставьте перед ним букву f.

ПРИМЕР:
```python
kowk = str(input(f"{RED}Введите кошк: {COLOR_END}")
```

```python
RED = fg('red')
GREEN = fg('green')
YELLOW = fg('yellow')
BLUE = fg('blue')
PURPLE = fg('magenta')
SKY_BLUE = fg('cyan')
COLOR_END = attr('reset')
```

---

**Примеры плагинов**

Создайте файл hello.py в папке plugins:

```python
if command == "hello_plugin":
 print(f"{PURPLE}hello world!{COLOR_END}")
```

Пример с созданием папки:

```python
root_minecraft_folder = Path(r"C:\cobalt_launcher_nano_reliz\minecraft_vanilla") # переменная корневого пути
create_folder_kowk = os.path.join(root_minecraft_folder, "kowka") # переменная создание подпапки kowka в папке minecraft_vanilla
os.makedirs(create_folder_kowk, exist_ok=True) # создание папки kowk если она если есть данная папка то ничего не трогаем
```

Пример с использованием библиотеки:

```python
import random # запрос библиотеки

if command == "рандом никнейм"
 nickname = str(input("Нажмите 1 чтобы выбрать рандомный никнейм")) # ввод строки

 list_nickname = ["steve", "alex", "kowk"] # создание списка

 ready_nickname = random.choice(list_nickname) # перебор элементов списка с помощью метода choice и сохранение в переменную

 print(f"{GREEN} ВАШ РАНДОМНЫЙ НИКНЕЙМ: {ready_nickname} {COLOR_END}") # вывод
```

---

**Установка плагинов**

Лаунчер имеет встроенную команду плагины, которая открывает меню для скачивания плагинов из официального репозитория  Вы можете также вручную скопировать файл .py в папку plugins – после перезапуска лаунчера он будет загружен.

---

**Регистрация плагина**

Для этого надо мне написать в @m1rotv0rets. Я отвечу и проверю на наличие вредонсного кода. Если будет всё нормально плагин будет выложен.

---

**Советы и предостарожности**

Имена команд должны быть уникальными. Если два плагина зарегистрируют команду с одинаковым именем, последняя загруженная перезапишет предыдущую (порядок загрузки – алфавитный по имени файла).
Обработка ошибок: старайтесь перехватывать исключения внутри функций плагина, чтобы не крашить лаунчер.
