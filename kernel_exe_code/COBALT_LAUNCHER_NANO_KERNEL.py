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

RED = fg('red')
GREEN = fg('green')
YELLOW = fg('yellow')
BLUE = fg('blue')
PURPLE = fg('magenta')
SKY_BLUE = fg('cyan')
COLOR_END = attr('reset')

root_folder = r"C:\cobalt_launcher_nano_reliz" 
folders = ['java', 'minecraft_vanilla', 'plugins', 'config_files', 'instances', 'launcher_models']

for folder in folders:                                                                                                                                                                                        
 create_folders = os.path.join(root_folder, folder)
 os.makedirs(create_folders, exist_ok=True)
 
root_minecraft_folder = Path(r"C:\cobalt_launcher_nano_reliz\minecraft_vanilla")
create_folder_screenshots = os.path.join(root_minecraft_folder, "screenshots")
os.makedirs(create_folder_screenshots, exist_ok=True)
 
try:
 with open(r"C:\cobalt_launcher_nano_reliz\config_files\accounts.txt", "x", encoding="utf-8") as file:
  pass
 with open(r"C:\cobalt_launcher_nano_reliz\config_files\notes.txt", "x", encoding="utf-8") as file:
  pass
except FileExistsError:
 pass

root_folder_java = Path(r"C:\cobalt_launcher_nano_reliz\java\temp_java_zip")
root_folder_java.mkdir(parents=True, exist_ok=True)

java8_github = r"https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano/releases/download/java/java_8.zip"
java17_github = r"https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano/releases/download/java/java_17.zip"
java21_github = r"https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano/releases/download/java/java_21.zip"

java8_folder = Path(r"C:\cobalt_launcher_nano_reliz\java\java_8")
java17_folder = Path(r"C:\cobalt_launcher_nano_reliz\java\java_17")
java21_folder = Path(r"C:\cobalt_launcher_nano_reliz\java\java_21")

java8_temp_folder = root_folder_java / "java_8.zip"
java17_temp_folder = root_folder_java / "java_17.zip"
java21_temp_folder = root_folder_java / "java_21.zip"

if java8_folder.is_dir():
 pass
else:
    print(f"{RED}ВНИМАНИЕ: ЛАУНЧЕР СКАЧИВАЕТ РЕСУРСЫ!!!{COLOR_END}")
    print(f"{YELLOW}Скачивание Java 8...{COLOR_END}")
    req = urllib.request.Request(
        java8_github, 
        headers={'User-Agent': 'Mozilla'}  
    )
    with urllib.request.urlopen(req) as response, open(java8_temp_folder, 'wb') as out_file:
        out_file.write(response.read())

    print(f"{YELLOW}Распаковка Java 8...{COLOR_END}")
    with zipfile.ZipFile(java8_temp_folder, 'r') as zip_ref:
        zip_ref.extractall(java8_folder)  
    
    java8_temp_folder.unlink() 
    print(f"{GREEN}Java 8 успешно установлена!{COLOR_END}")
    
if java17_folder.is_dir():
 pass
else:
    print(f"{YELLOW}Скачивание Java 17...{COLOR_END}")
    req = urllib.request.Request(
        java17_github, 
        headers={'User-Agent': 'Mozilla'}  
    )
    with urllib.request.urlopen(req) as response, open(java17_temp_folder, 'wb') as out_file:
        out_file.write(response.read())

    print(f"{YELLOW}Распаковка Java 17...{COLOR_END}")
    with zipfile.ZipFile(java17_temp_folder, 'r') as zip_ref:
        zip_ref.extractall(java17_folder)  
    
    java17_temp_folder.unlink() 
    print(f"{GREEN}Java 17 успешно установлена!{COLOR_END}")
    
if java21_folder.is_dir():
 pass
else:
    print(f"{YELLOW}Скачивание Java 21...{COLOR_END}")
    req = urllib.request.Request(
        java21_github, 
        headers={'User-Agent': 'Mozilla'}  
    )
    with urllib.request.urlopen(req) as response, open(java21_temp_folder, 'wb') as out_file:
        out_file.write(response.read())

    print(f"{YELLOW}Распаковка Java 21...{COLOR_END}")
    with zipfile.ZipFile(java21_temp_folder, 'r') as zip_ref:
        zip_ref.extractall(java21_folder)  
    
    java21_temp_folder.unlink() 
    print(f"{GREEN}Java 21 успешно установлена!{COLOR_END}")
    print(f"{RED}ВНИМАНИЕ: ЛАУНЧЕР ГОТОВ К РАБОТЕ!{COLOR_END}")
    
print(f"""
{SKY_BLUE}Cobalt Launcher Nano:{COLOR_END}
{RED}Версия: 1.1 СТАБИЛЬНАЯ{COLOR_END}
{GREEN}Автор: M1rotvorets{COLOR_END}
{YELLOW}Не знаете команды? Введите "помощь" чтобы вывести список {COLOR_END}
{BLUE}ДЛЯ ПЛАГИНОВ КОМАНДА ПОМОЩИ СОСТОИТ ИЗ НАЗВАНИЯ ПЛАГИНА И СЛОВА ПОМОЩЬ {COLOR_END}
""")

choice_instances = str(input(f"{RED}Выберите инстанс или создайте новый: {COLOR_END}"))

while True:
 # глобальный слушитель
 command = (input(f"{PURPLE}Введите команду: {COLOR_END}"))
 
 # загрузчик плагинов
 root_folder_pluguns = Path(r"C:\cobalt_launcher_nano_reliz\plugins")

 for plugin_file in root_folder_pluguns.glob("*.py"):
  try:
   command_text = plugin_file.read_text(encoding="utf-8")
   exec(command_text, globals(), locals())
  
  except Exception as e:
   print(f"[Ошибка выполнения команды из {plugin_file.name}]: {e}")
   
 # загрузчик модулей лаунчера
 root_folder_launcher_models = Path(r"C:\cobalt_launcher_nano_reliz\launcher_models")

 for launcher_models_file in root_folder_launcher_models.glob("*.py"):
  try:
   command_text = launcher_models_file.read_text(encoding="utf-8")
   exec(command_text, globals(), locals())
  
  except Exception as e:
   print(f"[Ошибка выполнения команды из {launcher_models_file.name}]: {e}")