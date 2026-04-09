# Стандартные библиотеки не используемые в лаунчере. Но вы их можете использовать в своем плагине.

import math # математика
import random # рандом
import calendar # календарь                        
import struct # бинарные файлы
import binascii # Преобразование двоичных данных                                
import unicodedata # юникод 
import sqlite3 # база данных
import PIL # для работы с изображениями, цветами

# Используемые библиотеки
import os 
import sys 
import json 
import zipfile 
import requests
import subprocess
import platform
import shutil
import re
import webbrowser
import getpass
import signal
import threading
import time
import itertools
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import minecraft_launcher_lib # Основная логика лаунчера
from colored import fg, attr # Вывод команд в цвете
import tarfile
import urllib.parse

try:
    import keyboard # Комбинации клавиш
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import nbtlib # Для редактирования файлов майнкрафта
    NBT_AVAILABLE = True
except ImportError:
    NBT_AVAILABLE = False

# Переменные отвечающие за цвет команд. Чтобы покрасить команду напишите {COLOR_ЦВЕТ_ИЗ ПЕРЕМЕННЫХ}Пример{COLOR_RESET}
COLOR_RED = fg('red')
COLOR_GREEN = fg('green')
COLOR_YELLOW = fg('yellow')
COLOR_BLUE = fg('blue')
COLOR_MAGENTA = fg('magenta')
COLOR_CYAN = fg('cyan')
COLOR_RESET = attr('reset')

# Создание папок, файлов
LAUNCHER_DATA_DIR = str(Path.home() / "Desktop" / "cobalt_launcher_files")

# Создание папки: 
# НАЗВАНИЕ_DIR = os.path.join(LAUNCHER_DATA_DIR, "НАЗВАНИЕ")

# Создание файла в папке:
# НАЗВАНИЕ_FILE = os.path.join(LAUNCHER_DATA_DIR, "НАЗВАНИЕ.расширение")

# Создание конфигов и папок
CONFIG_FILE = os.path.join(LAUNCHER_DATA_DIR, "config.json")
NOTES_FILE = os.path.join(LAUNCHER_DATA_DIR, "notes.txt")
JAVA_DIR = os.path.join(LAUNCHER_DATA_DIR, "java")
MINECRAFT_DIR = os.path.join(LAUNCHER_DATA_DIR, "minecraft")
ACCOUNTS_FILE = os.path.join(MINECRAFT_DIR, "launcher_profiles.json")
MODS_FAVORITES_FILE = os.path.join(LAUNCHER_DATA_DIR, "mods_favorites.json")
PLUGINS_DIR = os.path.join(LAUNCHER_DATA_DIR, "plugins")

# Переменная ссылка в которой хранится ссылка на .json файл от куда можно скачать плагины лаунчера
PLUGINS_INDEX_URL = "https://raw.githubusercontent.com/m1r0tv0rets/Cobalt_Launcher_Nano/main/plugins.json"

os.makedirs(LAUNCHER_DATA_DIR, exist_ok=True)
os.makedirs(JAVA_DIR, exist_ok=True)
os.makedirs(MINECRAFT_DIR, exist_ok=True)
os.makedirs(PLUGINS_DIR, exist_ok=True)

plugin_commands = {}
plugin_hooks = {'banner': [], 'info': []}

# ПлагинАпи который регистрирует команды плагинов
class PluginAPI:
    def __init__(self, module):
        self.module = module
    def get_plugin_path(self):
        return os.path.dirname(self.module.__file__)
    def register_command(self, name, func, hidden=False):
        plugin_commands[name] = {'func': func, 'hidden': hidden}
    def register_banner_hook(self, func):
        plugin_hooks['banner'].append(func)
    def register_info_hook(self, func):
        plugin_hooks['info'].append(func)
    def get_data_dir(self):
        return LAUNCHER_DATA_DIR
    def get_plugins_dir(self):
        return PLUGINS_DIR

def load_plugins():
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
    sys.path.insert(0, PLUGINS_DIR)
    for file in os.listdir(PLUGINS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            try:
                module = __import__(module_name)
                if hasattr(module, "register_plugin"):
                    api = PluginAPI(module)
                    module.register_plugin(api)
                elif hasattr(module, "register_commands"):
                    cmd_dict = {}
                    module.register_commands(cmd_dict)
                    api = PluginAPI(module)
                    for name, func in cmd_dict.items():
                        api.register_command(name, func, hidden=False)
                print(f"{COLOR_GREEN}Загружен плагин: {module_name}{COLOR_RESET}")
            except Exception as e:
                print(f"{COLOR_RED}Ошибка загрузки плагина {module_name}: {e}{COLOR_RESET}")

# Перазапуск лаунчера
def restart_launcher():
    print(f"{COLOR_GREEN}Перезапуск лаунчера...{COLOR_RESET}")
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

# Информация которая окажется в конфиге
def load_config():
    default_config = {
        "java_args": "-Xmx2G -Xms1G",
        "selected_version": None,
        "current_account": None,
        "separate_version_dirs": False,
        "java_path": None,
        "java_version": "17", #Версия джавы
        "user_commands": {},
        "custom_info_lines": [], 
        "servers": [],
        "java_args_by_version": {},
        "java_path_by_version": {}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except json.JSONDecodeError:
            return default_config
    return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=4, ensure_ascii=False)

def add_offline_account(username):
    accounts = load_accounts()
    account_id = max([acc["id"] for acc in accounts], default=0) + 1
    account = {
        "id": account_id,
        "username": username,
        "type": "offline",
        "created_at": datetime.now().isoformat()
    }
    accounts.append(account)
    save_accounts(accounts)
    return account

# НОВАЯ РЕАЛИЗАЦИЯ Ely.by через OAuth
def add_ely_account_oauth():
    print(f"{COLOR_CYAN}Авторизация через Ely.by...{COLOR_RESET}")
    # OAuth параметры (официальные для лаунчеров)
    client_id = "ely-client-id"  # В реальном приложении нужен свой client_id, но для демо используем общий
    redirect_uri = "http://localhost:58462/callback"
    auth_url = f"https://account.ely.by/oauth2/v1/authorize?response_type=code&client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&scope=offline"
    
    # Запускаем временный HTTP сервер для получения кода
    import http.server
    import socketserver
    import urllib.parse as urlparse
    
    auth_code = None
    
    class CallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            parsed = urlparse.urlparse(self.path)
            query = urlparse.parse_qs(parsed.query)
            if 'code' in query:
                auth_code = query['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                # Исправлено: байтовая строка с кириллицей заменена на encode
                self.wfile.write("<html><body><h1>Авторизация успешна! Закройте это окно.</h1></body></html>".encode('utf-8'))
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write("<html><body><h1>Ошибка авторизации</h1></body></html>".encode('utf-8'))
        
        def log_message(self, format, *args):
            pass  # заглушаем вывод сервера
    
    # Запускаем сервер в отдельном потоке
    with socketserver.TCPServer(("localhost", 58462), CallbackHandler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        print(f"{COLOR_YELLOW}Открытие браузера для входа...{COLOR_RESET}")
        webbrowser.open(auth_url)
        print(f"{COLOR_CYAN}Ожидание завершения авторизации...{COLOR_RESET}")
        # Ждём код (максимум 60 секунд)
        for _ in range(120):
            if auth_code:
                break
            time.sleep(0.5)
        httpd.shutdown()
        thread.join(timeout=1)
    
    if not auth_code:
        print(f"{COLOR_RED}Не удалось получить код авторизации{COLOR_RESET}")
        return None
    
    # Обмениваем код на токен
    token_url = "https://account.ely.by/oauth2/v1/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "redirect_uri": redirect_uri
    }
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        response.raise_for_status()
        token_json = response.json()
        access_token = token_json.get("access_token")
        if not access_token:
            print(f"{COLOR_RED}Не удалось получить токен{COLOR_RESET}")
            return None
        # Получаем информацию о профиле
        profile_url = "https://account.ely.by/api/account/profile/v1"
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_resp = requests.get(profile_url, headers=headers, timeout=10)
        profile_resp.raise_for_status()
        profile = profile_resp.json()
        username = profile.get("username", "ElyUser")
        uuid = profile.get("uuid", "")
        # Сохраняем аккаунт
        accounts = load_accounts()
        account_id = max([acc["id"] for acc in accounts], default=0) + 1
        account = {
            "id": account_id,
            "username": username,
            "type": "ely",
            "uuid": uuid,
            "access_token": access_token,
            "refresh_token": token_json.get("refresh_token", ""),
            "created_at": datetime.now().isoformat()
        }
        accounts.append(account)
        save_accounts(accounts)
        print(f"{COLOR_GREEN}Аккаунт Ely.by '{username}' успешно добавлен!{COLOR_RESET}")
        return account
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения токена: {e}{COLOR_RESET}")
        return None

def delete_account(account_id):
    accounts = load_accounts()
    accounts = [acc for acc in accounts if acc["id"] != account_id]
    save_accounts(accounts)
    return True

def get_account_by_id(account_id):
    accounts = load_accounts()
    for account in accounts:
        if account["id"] == account_id:
            return account
    return None

def input_yes_no(prompt):
    while True:
        response = input(prompt).lower()
        if response in ['да', 'д']:
            return True
        elif response in ['нет', 'н']:
            return False
        else:
            print(f"{COLOR_RED}Пожалуйста, ответьте 'да' или 'нет'{COLOR_RESET}")

class ScrollableList:
    def __init__(self, items, page_size=10):
        self.items = items
        self.page_size = page_size
        self.current_page = 0

    def display_page(self):
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_items = self.items[start_idx:end_idx]
        total_pages = (len(self.items) + self.page_size - 1) // self.page_size if self.items else 1
        print(f"{COLOR_CYAN}Страница {self.current_page + 1}/{total_pages}{COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        if not page_items:
            print(f"{COLOR_YELLOW}Нет элементов для отображения{COLOR_RESET}")
        else:
            for i, item in enumerate(page_items, start=1):
                print(f"{COLOR_YELLOW}{start_idx + i:3}.{COLOR_RESET} {item}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")

    def navigate(self):
        if not self.items:
            print(f"{COLOR_YELLOW}Список пуст{COLOR_RESET}")
            return None
        while True:
            self.display_page()
            print(f"\n{COLOR_GREEN}Команды:{COLOR_RESET}")
            print(f"{COLOR_CYAN}с{COLOR_RESET} - следующая страница")
            print(f"{COLOR_CYAN}п{COLOR_RESET} - предыдущая страница")
            print(f"{COLOR_CYAN}число{COLOR_RESET} - выбрать элемент")
            print(f"{COLOR_CYAN}в{COLOR_RESET} - выйти")
            choice = input(f"{COLOR_YELLOW}Выберите: {COLOR_RESET}").lower()
            if choice == 'с':
                if (self.current_page + 1) * self.page_size < len(self.items):
                    self.current_page += 1
                else:
                    print(f"{COLOR_RED}Это последняя страница{COLOR_RESET}")
            elif choice == 'п':
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    print(f"{COLOR_RED}Это первая страница{COLOR_RESET}")
            elif choice == 'в':
                return None
            elif choice.isdigit():
                idx = int(choice) - 1
                actual_idx = self.current_page * self.page_size + idx
                if 0 <= actual_idx < len(self.items):
                    return actual_idx
                else:
                    print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Неверная команда{COLOR_RESET}")

def print_banner():
    banner = f"""
{COLOR_CYAN}Cobalt Launcher Nano:{COLOR_RESET}
{COLOR_CYAN}Версия: {COLOR_RED}0.9 ALPHA{COLOR_RESET}
{COLOR_CYAN}Автор: {COLOR_GREEN}M1rotvorets{COLOR_RESET}
{COLOR_CYAN}Помощники: {COLOR_YELLOW}WaterBucket, Nos0kkk{COLOR_RESET}
{COLOR_CYAN}Репозиторий: {COLOR_BLUE}https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano{COLOR_RESET}
    """
    for hook in plugin_hooks['banner']:
        try:
            banner = hook(banner) or banner
        except Exception as e:
            print(f"{COLOR_RED}Ошибка в хуке баннера: {e}{COLOR_RESET}")
    print(banner)

def print_help():
    help_text = f"""
{COLOR_CYAN}ДОСТУПНЫЕ КОМАНДЫ:{COLOR_RESET}
{COLOR_GREEN}акк{COLOR_RESET}         - Управление аккаунтами
{COLOR_GREEN}альфа{COLOR_RESET}       - Показать альфа версии
{COLOR_GREEN}бета{COLOR_RESET}        - Показать бета версии
{COLOR_GREEN}снапшоты{COLOR_RESET}    - Показать снапшоты
{COLOR_GREEN}релизы{COLOR_RESET}      - Показать релизные версии
{COLOR_GREEN}установить <версия> [модлоадер]{COLOR_RESET}  - Установить версию (модлоадер: forge, fabric, quilt, neoforge)
{COLOR_GREEN}установить гитхаб <версия>{COLOR_RESET}  - Установить версию из GitHub репозитория(Пока не работает) (ZIP архив)
{COLOR_GREEN}запуск [версия]{COLOR_RESET}      - Запустить Minecraft (текущую или указанную)
{COLOR_GREEN}отложенный запуск <версия> <сек> <кол-во>{COLOR_RESET} - Запустить несколько клиентов через время
{COLOR_GREEN}арг{COLOR_RESET}         - Настройка общих аргументов Java
{COLOR_GREEN}арг версии <версия> <аргументы>{COLOR_RESET} - Аргументы Java для конкретной версии
{COLOR_GREEN}джава версии <версия> [путь]{COLOR_RESET} - Установить/сбросить путь Java для версии
{COLOR_GREEN}память <ГБ>{COLOR_RESET} - Установить общий объем памяти
{COLOR_GREEN}папка модов{COLOR_RESET} - Открыть папку модов
{COLOR_GREEN}ресурспак{COLOR_RESET}   - Открыть папку ресурспаков
{COLOR_GREEN}миры{COLOR_RESET}        - Открыть папку миров
{COLOR_GREEN}скриншоты{COLOR_RESET}   - Открыть папку скриншотов
{COLOR_GREEN}конфиги{COLOR_RESET}     - Открыть папку конфигов
{COLOR_GREEN}схемы{COLOR_RESET}       - Открыть папку схем
{COLOR_GREEN}моды{COLOR_RESET}        - Поиск и управление модами (Modrinth)
{COLOR_GREEN}плагины{COLOR_RESET}     - Управление плагинами лаунчера
{COLOR_GREEN}инфо{COLOR_RESET}        - Полезная информация (редактируется)
{COLOR_GREEN}заметка <текст>{COLOR_RESET} - Добавить заметку
{COLOR_GREEN}заметки{COLOR_RESET}     - Показать все заметки
{COLOR_GREEN}бэкап{COLOR_RESET}       - Создать резервную копию (миры, ресурспаки, конфиги, моды, конфиг лаунчера)
{COLOR_GREEN}конфиг лаунчера{COLOR_RESET} - Скопировать конфиг лаунчера на рабочий стол
{COLOR_GREEN}папка{COLOR_RESET}       - Открыть папку Minecraft
{COLOR_GREEN}лог{COLOR_RESET}         - Скопировать последний лог на рабочий стол
{COLOR_GREEN}джава{COLOR_RESET}       - Установить общий путь к Java
{COLOR_GREEN}установить джава{COLOR_RESET} - Скачать и установить Java
{COLOR_GREEN}краш{COLOR_RESET}        - Скопировать краш-репорты на рабочий стол
{COLOR_GREEN}отдельные папки{COLOR_RESET} - Включить/выключить отдельные папки для версий
{COLOR_GREEN}альт мод{COLOR_RESET}    - Открыть ru-minecraft.ru
{COLOR_GREEN}добавить команду{COLOR_RESET} - Мастер добавления пользовательской команды
{COLOR_GREEN}удалить команду <имя>{COLOR_RESET} - Удалить пользовательскую команду
{COLOR_GREEN}команды{COLOR_RESET}     - Список пользовательских команд
{COLOR_GREEN}добавить сервер <имя> <айпи> [версия]{COLOR_RESET} - Добавить сервер в информацию и в игру
{COLOR_GREEN}удалить сервер <айпи>{COLOR_RESET} - Удалить сервер
{COLOR_GREEN}добавить инфо <текст>{COLOR_RESET} - Добавить строку в информацию
{COLOR_GREEN}очистить инфо{COLOR_RESET} - Очистить пользовательскую информацию
{COLOR_GREEN}удалить лаунчер{COLOR_RESET} - Полностью удалить папку лаунчера
    """
    config = load_config()
    if config["user_commands"]:
        help_text += f"\n{COLOR_CYAN}ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ:{COLOR_RESET}\n"
        for name, data in config["user_commands"].items():
            help_text += f"{COLOR_GREEN}{name}{COLOR_RESET} - {data['type']}: {data['params']}\n"
    plugin_cmds = [name for name, info in plugin_commands.items() if not info.get('hidden', False)]
    if plugin_cmds:
        help_text += f"\n{COLOR_CYAN}КОМАНДЫ ПЛАГИНОВ:{COLOR_RESET}\n"
        for name in plugin_cmds:
            help_text += f"{COLOR_GREEN}{name}{COLOR_RESET} - плагин\n"
    print(help_text)

# Скачивание плагинов
def manage_plugins():
    print(f"{COLOR_CYAN}ПОЛУЧЕНИЕ СПИСКА ДОСТУПНЫХ ПЛАГИНОВ...{COLOR_RESET}")
    try:
        response = requests.get(PLUGINS_INDEX_URL, timeout=10)
        response.raise_for_status()
        plugins = response.json()
    except Exception as e:
        print(f"{COLOR_RED}Не удалось загрузить список плагинов: {e}{COLOR_RESET}")
        return

    if not plugins:
        print(f"{COLOR_YELLOW}Нет доступных плагинов{COLOR_RESET}")
        return

    while True:
        print(f"\n{COLOR_CYAN}ДОСТУПНЫЕ ПЛАГИНЫ{COLOR_RESET}")
        for i, p in enumerate(plugins, 1):
            print(f"{COLOR_YELLOW}{i}.{COLOR_RESET} {p['name']} - {p['description']}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        print(f"{COLOR_CYAN}в{COLOR_RESET} - назад")
        choice = input(f"{COLOR_YELLOW}Выберите номер для установки: {COLOR_RESET}").strip()
        if choice.lower() == 'в':
            break
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(plugins):
                install_plugin(plugins[idx])
            else:
                print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Неверный ввод{COLOR_RESET}")

def install_plugin(plugin_info):
    name = plugin_info['name']
    url = plugin_info['download_url']
    print(f"{COLOR_CYAN}Установка плагина '{name}'...{COLOR_RESET}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        archive_path = os.path.join(PLUGINS_DIR, f"{name}.zip")
        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Извлекаем все файлы, но если внутри есть одна папка, перемещаем её содержимое в PLUGINS_DIR
            members = zip_ref.namelist()
            top_dirs = set(m.split('/')[0] for m in members if '/' in m)
            if len(top_dirs) == 1 and all(m.startswith(next(iter(top_dirs))) for m in members):
                # В архиве только одна папка - извлекаем её содержимое напрямую
                for member in members:
                    target = member.replace(next(iter(top_dirs)) + '/', '', 1)
                    if target:
                        source = zip_ref.open(member)
                        target_path = os.path.join(PLUGINS_DIR, target)
                        if member.endswith('/'):
                            os.makedirs(target_path, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            with open(target_path, 'wb') as out:
                                out.write(source.read())
            else:
                zip_ref.extractall(PLUGINS_DIR)
        os.remove(archive_path)
        print(f"{COLOR_GREEN}Плагин '{name}' установлен!{COLOR_RESET}")
        restart_launcher()
    except Exception as e:
        print(f"{COLOR_RED}Ошибка установки: {e}{COLOR_RESET}")

def add_user_command(name, action_type, params):
    config = load_config()
    if name in config["user_commands"]:
        print(f"{COLOR_RED}Команда с таким именем уже существует{COLOR_RESET}")
        return False
    config["user_commands"][name] = {"type": action_type, "params": params}
    save_config(config)
    print(f"{COLOR_GREEN}Команда '{name}' добавлена{COLOR_RESET}")
    return True

def remove_user_command(name):
    config = load_config()
    if name in config["user_commands"]:
        del config["user_commands"][name]
        save_config(config)
        print(f"{COLOR_GREEN}Команда '{name}' удалена{COLOR_RESET}")
        return True
    else:
        print(f"{COLOR_RED}Команда не найдена{COLOR_RESET}")
        return False

def list_user_commands():
    config = load_config()
    if not config["user_commands"]:
        print(f"{COLOR_YELLOW}Нет пользовательских команд{COLOR_RESET}")
        return
    print(f"{COLOR_CYAN}Пользовательские команды:{COLOR_RESET}")
    for name, data in config["user_commands"].items():
        print(f"  {COLOR_GREEN}{name}{COLOR_RESET}: {data['type']} - {data['params']}")

def execute_user_command(cmd, args):
    if cmd in plugin_commands:
        try:
            plugin_commands[cmd]['func'](args)
        except Exception as e:
            print(f"{COLOR_RED}Ошибка выполнения команды плагина: {e}{COLOR_RESET}")
        return True
    config = load_config()
    if cmd in config["user_commands"]:
        cmd_data = config["user_commands"][cmd]
        try:
            if cmd_data["type"] == "url":
                webbrowser.open(cmd_data["params"])
                print(f"{COLOR_GREEN}Открыт URL: {cmd_data['params']}{COLOR_RESET}")
            elif cmd_data["type"] == "html":
                path = cmd_data["params"]
                if os.path.exists(path):
                    webbrowser.open(f"file://{os.path.abspath(path)}")
                    print(f"{COLOR_GREEN}Открыт HTML файл: {path}{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Файл не найден: {path}{COLOR_RESET}")
            elif cmd_data["type"] == "script":
                script_path = cmd_data["params"]
                if os.path.exists(script_path):
                    result = subprocess.run([sys.executable, script_path] + args, capture_output=True, text=True)
                    print(result.stdout)
                    if result.stderr:
                        print(f"{COLOR_RED}{result.stderr}{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Скрипт не найден: {script_path}{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Неизвестный тип команды{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_RED}Ошибка выполнения команды: {e}{COLOR_RESET}")
        return True
    return False

def wizard_add_command():
    print(f"{COLOR_CYAN}Мастер добавления команды{COLOR_RESET}")
    name = input("Введите имя команды (без пробелов): ").strip()
    if not name:
        print(f"{COLOR_RED}Имя не может быть пустым{COLOR_RESET}")
        return
    print("Выберите тип действия:")
    print("1. Открыть сайт (URL)")
    print("2. Открыть HTML файл")
    print("3. Запустить Python скрипт")
    choice = input("Ваш выбор (1-3): ").strip()
    if choice == "1":
        url = input("Введите URL (например, https://example.com): ").strip()
        if url:
            add_user_command(name, "url", url)
    elif choice == "2":
        path = input("Введите путь к HTML файлу: ").strip()
        if path:
            add_user_command(name, "html", path)
    elif choice == "3":
        script = input("Введите путь к Python скрипту: ").strip()
        if script:
            add_user_command(name, "script", script)
    else:
        print(f"{COLOR_RED}Неверный выбор{COLOR_RESET}")

def add_custom_info_line(line):
    config = load_config()
    config["custom_info_lines"].append(line)
    save_config(config)
    print(f"{COLOR_GREEN}Строка добавлена в информацию{COLOR_RESET}")

def clear_custom_info():
    config = load_config()
    config["custom_info_lines"] = []
    save_config(config)
    print(f"{COLOR_GREEN}Пользовательская информация очищена{COLOR_RESET}")

def add_server_to_minecraft(server_name, server_ip, minecraft_dir):
    if not NBT_AVAILABLE:
        print(f"{COLOR_YELLOW}Библиотека nbtlib не установлена. Сервер не будет добавлен в игру. Установите: pip install nbtlib{COLOR_RESET}")
        return False
    servers_dat = os.path.join(minecraft_dir, 'servers.dat')
    try:
        if os.path.exists(servers_dat):
            data = nbtlib.load(servers_dat)
        else:
            data = nbtlib.File({'servers': nbtlib.List[nbtlib.Compound]()})
        servers = data['servers']
        new_server = nbtlib.Compound({
            'name': nbtlib.String(server_name),
            'ip': nbtlib.String(server_ip),
            'icon': nbtlib.String(''),
            'acceptTextures': nbtlib.Byte(0)
        })
        servers.append(new_server)
        data.save(servers_dat)
        print(f"{COLOR_GREEN}Сервер '{server_name}' добавлен в список серверов Minecraft.{COLOR_RESET}")
        return True
    except Exception as e:
        print(f"{COLOR_RED}Ошибка при добавлении сервера в servers.dat: {e}{COLOR_RESET}")
        return False

def add_server(name, ip, version=None):
    config = load_config()
    config["servers"].append({"name": name, "ip": ip})
    save_config(config)
    print(f"{COLOR_GREEN}Сервер '{name}' добавлен в конфиг{COLOR_RESET}")
    if version:
        mc_dir = get_minecraft_dir_for_version(version)
    else:
        mc_dir = MINECRAFT_DIR
    add_server_to_minecraft(name, ip, mc_dir)

def remove_server(ip):
    config = load_config()
    initial_len = len(config["servers"])
    config["servers"] = [s for s in config["servers"] if s["ip"] != ip]
    if len(config["servers"]) < initial_len:
        save_config(config)
        print(f"{COLOR_GREEN}Сервер с IP {ip} удалён из конфига{COLOR_RESET}")
    else:
        print(f"{COLOR_RED}Сервер с таким IP не найден{COLOR_RESET}")

def find_java_executable_in_dir(java_dir):
    for root, dirs, files in os.walk(java_dir):
        if platform.system() == "Windows":
            if "java.exe" in files:
                return os.path.join(root, "java.exe")
        else:
            if "java" in files and os.access(os.path.join(root, "java"), os.X_OK):
                return os.path.join(root, "java")
    for root, dirs, files in os.walk(java_dir):
        if "bin" in dirs:
            bin_path = os.path.join(root, "bin")
            if platform.system() == "Windows":
                java_candidate = os.path.join(bin_path, "java.exe")
                if os.path.exists(java_candidate):
                    return java_candidate
            else:
                java_candidate = os.path.join(bin_path, "java")
                if os.path.exists(java_candidate) and os.access(java_candidate, os.X_OK):
                    return java_candidate
    return None

def get_java_version(java_path):
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True, shell=True, timeout=5)
        output = result.stderr if result.stderr else result.stdout
        patterns = [r'version["\s]+([0-9._]+)', r'\(build ([0-9._]+)\)', r'java version["\s]+([0-9._]+)']
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                version_str = match.group(1)
                main_version_match = re.search(r'^(\d+)', version_str)
                if main_version_match:
                    return int(main_version_match.group(1))
        return None
    except Exception:
        return None

def get_required_java_version(minecraft_version):
    match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', minecraft_version)
    if not match:
        return 8
    major = int(match.group(1))
    minor = int(match.group(2))
    if major == 1:
        if minor >= 18:
            return 17
        elif minor >= 17:
            return 16
        else:
            return 8
    else:
        return 17

def find_suitable_java(minecraft_version):
    required = get_required_java_version(minecraft_version)
    for ver in [8, 11, 16, 17, 21]:
        if ver >= required:
            java_dir_candidate = os.path.join(JAVA_DIR, f"java_{ver}")
            if os.path.exists(java_dir_candidate):
                exe = find_java_executable_in_dir(java_dir_candidate)
                if exe:
                    return exe
    return None

def set_java_path_for_version(version, path=None):
    config = load_config()
    if path is None:
        if version in config["java_path_by_version"]:
            del config["java_path_by_version"][version]
            print(f"{COLOR_GREEN}Путь Java для версии {version} сброшен{COLOR_RESET}")
    else:
        if os.path.exists(path):
            config["java_path_by_version"][version] = path
            print(f"{COLOR_GREEN}Путь Java для версии {version} установлен: {path}{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Указанный путь не существует{COLOR_RESET}")
            return
    save_config(config)

def get_java_download_url(version, os_name, arch):
    api_url = f"https://api.adoptium.net/v3/assets/latest/{version}/hotspot"
    params = {
        "architecture": arch,
        "image_type": "jdk",
        "os": os_name,
        "vendor": "adoptium"
    }
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            binary = data[0].get("binary", {})
            package = binary.get("package", {})
            link = package.get("link")
            if link:
                if link.endswith(".zip"):
                    ext = "zip"
                elif link.endswith(".tar.gz"):
                    ext = "tar.gz"
                else:
                    ext = "unknown"
                return link, ext
    except Exception:
        pass
    return None, None

def download_with_retry(url, filepath, callback=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback and total_size > 0:
                            callback(downloaded, total_size)
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError) as e:
            print(f"\n{COLOR_YELLOW}Попытка {attempt} не удалась: {e}{COLOR_RESET}")
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"{COLOR_CYAN}Повтор через {wait} секунд...{COLOR_RESET}")
                time.sleep(wait)
            else:
                print(f"{COLOR_RED}Не удалось скачать файл после {max_retries} попыток{COLOR_RESET}")
                return False
    return False

class Spinner:
    def __init__(self, message="Загрузка"):
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])
        self.running = False
        self.thread = None
        self.message = message

    def spin(self):
        while self.running:
            print(f"\r{COLOR_CYAN}{self.message} {next(self.spinner)}{COLOR_RESET}", end="", flush=True)
            time.sleep(0.1)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
        print("\r" + " " * (len(self.message) + 10), end="\r", flush=True)

class ProgressCallback:
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.current = 0
        self.total = 0

    def __call__(self, *args):
        if len(args) == 1 and isinstance(args[0], dict):
            data = args[0]
            self.current = data.get('current', 0)
            self.total = data.get('total', 0)
        elif len(args) == 2:
            self.current, self.total = args
        else:
            return

        if self.total > 0:
            percent = (self.current / self.total) * 100
            bar_length = 30
            filled = int(bar_length * self.current / self.total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r{COLOR_CYAN}{self.prefix}[{bar}] {percent:.1f}% ({self.current}/{self.total} файлов){COLOR_RESET}", end="")
            if self.current >= self.total:
                print()

    def get(self, key, default=None):
        if key == 'current':
            return self.current
        elif key == 'total':
            return self.total
        return default

def manage_accounts_scrollable():
    accounts = load_accounts()
    config = load_config()
    if not accounts:
        print(f"{COLOR_YELLOW}Аккаунты не найдены{COLOR_RESET}")
        print(f"{COLOR_GREEN}Выберите тип аккаунта:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Оффлайн аккаунт")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Ely.by аккаунт")
        choice = input(f"{COLOR_YELLOW}Выберите тип: {COLOR_RESET}")
        if choice == '1':
            username = input("Введите имя пользователя: ")
            if username:
                account = add_offline_account(username)
                config["current_account"] = account["id"]
                save_config(config)
                print(f"{COLOR_GREEN}Аккаунт '{username}' добавлен!{COLOR_RESET}")
        elif choice == '2':
            account = add_ely_account_oauth()
            if account:
                config["current_account"] = account["id"]
                save_config(config)
        return
    while True:
        print(f"\n{COLOR_CYAN}УПРАВЛЕНИЕ АККАУНТАМИ{COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        for acc in accounts:
            status = f"{COLOR_GREEN}✓{COLOR_RESET}" if config.get("current_account") == acc["id"] else " "
            print(f"{status} ID: {acc['id']} | {acc['username']} ({acc['type']})")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        print(f"{COLOR_GREEN}Выберите действие:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Добавить оффлайн аккаунт")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Добавить Ely.by аккаунт")
        print(f"{COLOR_YELLOW}3.{COLOR_RESET} Удалить аккаунт")
        print(f"{COLOR_YELLOW}4.{COLOR_RESET} Выбрать текущий аккаунт")
        print(f"{COLOR_YELLOW}5.{COLOR_RESET} Назад")
        choice = input(f"{COLOR_YELLOW}Выберите: {COLOR_RESET}")
        if choice == '1':
            username = input("Введите имя пользователя: ")
            if username:
                account = add_offline_account(username)
                print(f"{COLOR_GREEN}Аккаунт '{username}' добавлен с ID {account['id']}!{COLOR_RESET}")
        elif choice == '2':
            account = add_ely_account_oauth()
            if account:
                print(f"{COLOR_GREEN}Аккаунт Ely.by '{account['username']}' добавлен!{COLOR_RESET}")
        elif choice == '3':
            acc_id = input("Введите ID аккаунта для удаления: ")
            if acc_id.isdigit():
                if delete_account(int(acc_id)):
                    print(f"{COLOR_GREEN}Аккаунт удален!{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Аккаунт не найден!{COLOR_RESET}")
        elif choice == '4':
            acc_id = input("Введите ID аккаунта для выбора: ")
            if acc_id.isdigit():
                acc = get_account_by_id(int(acc_id))
                if acc:
                    config["current_account"] = acc["id"]
                    save_config(config)
                    print(f"{COLOR_GREEN}Текущий аккаунт: {acc['username']}{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Аккаунт не найден!{COLOR_RESET}")
        elif choice == '5':
            break
        else:
            print(f"{COLOR_RED}Неверный выбор!{COLOR_RESET}")

def list_versions_by_type(version_type):
    print(f"{COLOR_CYAN}Получение списка версий...{COLOR_RESET}")
    try:
        versions = minecraft_launcher_lib.utils.get_available_versions(MINECRAFT_DIR)
        filtered_versions = []
        for v in versions:
            if version_type == "alpha" and v['type'] == 'old_alpha':
                filtered_versions.append(v)
            elif version_type == "beta" and v['type'] == 'old_beta':
                filtered_versions.append(v)
            elif version_type == "snapshot" and v['type'] == 'snapshot':
                filtered_versions.append(v)
            elif version_type == "release" and v['type'] == 'release':
                filtered_versions.append(v)
        if not filtered_versions:
            print(f"{COLOR_YELLOW}Версий данного типа не найдено{COLOR_RESET}")
            return
        filtered_versions = filtered_versions[::-1]
        version_list = [f"{v['id']} ({v['type']})" for v in filtered_versions]
        scroll_list = ScrollableList(version_list, page_size=15)
        type_names = {
            "alpha": "АЛЬФА ВЕРСИИ",
            "beta": "БЕТА ВЕРСИИ",
            "snapshot": "СНАПШОТЫ",
            "release": "РЕЛИЗНЫЕ ВЕРСИИ"
        }
        print(f"{COLOR_CYAN}{type_names[version_type]}{COLOR_RESET}")
        selected_idx = scroll_list.navigate()
        if selected_idx is not None:
            selected_version = filtered_versions[selected_idx]['id']
            print(f"\n{COLOR_GREEN}Выбрана версия: {selected_version}{COLOR_RESET}")
            if input_yes_no("Установить эту версию? (да/нет): "):
                install_version_interactive(selected_version)
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения списка версий: {e}{COLOR_RESET}")

def get_minecraft_dir_for_version(version):
    config = load_config()
    if config.get("separate_version_dirs", False):
        return str(Path.home() / f".minecraft_{version}")
    return MINECRAFT_DIR

def install_version_with_progress(version, loader_choice=None):
    print(f"{COLOR_CYAN}Установка версии {version}...{COLOR_RESET}")
    try:
        minecraft_dir = get_minecraft_dir_for_version(version)
        progress_callback = ProgressCallback()
        print(f"{COLOR_YELLOW}Скачивание файлов...{COLOR_RESET}")
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_dir, callback=progress_callback)
        if loader_choice:
            print(f"{COLOR_CYAN}Установка модлоадера...{COLOR_RESET}")
            install_loader(version, loader_choice, minecraft_dir)
        config = load_config()
        config["selected_version"] = version
        save_config(config)
        print(f"{COLOR_GREEN}✓ Версия {version} успешно установлена!{COLOR_RESET}")
    except Exception as e:
        print(f"\n{COLOR_RED}Ошибка установки: {e}{COLOR_RESET}")

def install_loader(version, loader_choice, minecraft_dir):
    loader_progress = ProgressCallback(prefix="Модлоадер: ")
    try:
        if loader_choice == '1':
            forge_versions = minecraft_launcher_lib.forge.list_forge_versions()
            filtered_forge = [fv for fv in forge_versions if fv.startswith(version + '-')]
            if not filtered_forge:
                print(f"{COLOR_RED}Forge для версии {version} не найден{COLOR_RESET}")
                return
            while filtered_forge:
                if len(filtered_forge) == 1:
                    forge_version = filtered_forge[0]
                else:
                    print(f"{COLOR_GREEN}Доступные версии Forge:{COLOR_RESET}")
                    for i, fv in enumerate(filtered_forge[:10], 1):
                        print(f"{COLOR_YELLOW}{i}.{COLOR_RESET} {fv}")
                    choice = input(f"{COLOR_YELLOW}Выберите версию (1-{min(10, len(filtered_forge))}), 'пропустить' для отмены: {COLOR_RESET}")
                    if choice.lower() in ['пропустить', 's', 'skip']:
                        print(f"{COLOR_YELLOW}Установка Forge пропущена{COLOR_RESET}")
                        return
                    if not choice.isdigit():
                        print(f"{COLOR_RED}Неверный выбор{COLOR_RESET}")
                        continue
                    idx = int(choice) - 1
                    if 0 <= idx < len(filtered_forge):
                        forge_version = filtered_forge[idx]
                    else:
                        print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
                        continue
                print(f"{COLOR_CYAN}Установка {forge_version}...{COLOR_RESET}")
                try:
                    minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_dir, callback=loader_progress)
                    print(f"{COLOR_GREEN}Forge {forge_version} установлен{COLOR_RESET}")
                    return
                except Exception as e:
                    print(f"{COLOR_RED}Ошибка установки Forge {forge_version}: {e}{COLOR_RESET}")
                    filtered_forge = [fv for fv in filtered_forge if fv != forge_version]
                    if not filtered_forge:
                        print(f"{COLOR_RED}Больше нет доступных версий Forge. Установка пропущена.{COLOR_RESET}")
                        return
                    print(f"{COLOR_YELLOW}Попробуем другую версию...{COLOR_RESET}")
        elif loader_choice == '2':
            loader_version = minecraft_launcher_lib.fabric.get_recommended_loader_version(version)
            if not loader_version:
                print(f"{COLOR_RED}Не удалось найти рекомендуемую версию Fabric для {version}{COLOR_RESET}")
                return
            minecraft_launcher_lib.fabric.install_fabric(version, minecraft_dir, loader_version=loader_version, callback=loader_progress)
            print(f"{COLOR_GREEN}Fabric {loader_version} установлен{COLOR_RESET}")
        elif loader_choice == '3':
            loader_version = minecraft_launcher_lib.quilt.get_recommended_loader_version(version)
            if not loader_version:
                print(f"{COLOR_RED}Не удалось найти рекомендуемую версию Quilt для {version}{COLOR_RESET}")
                return
            minecraft_launcher_lib.quilt.install_quilt(version, minecraft_dir, loader_version=loader_version, callback=loader_progress)
            print(f"{COLOR_GREEN}Quilt {loader_version} установлен{COLOR_RESET}")
        elif loader_choice == '4':
            response = requests.get("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge", timeout=10)
            if response.status_code == 200:
                neoforge_data = response.json()
                if 'versions' in neoforge_data:
                    filtered_neoforge = [v for v in neoforge_data['versions'] if v.startswith(version)]
                    if filtered_neoforge:
                        latest_neoforge = filtered_neoforge[-1]
                        minecraft_launcher_lib.forge.install_forge_version(latest_neoforge, minecraft_dir, callback=loader_progress)
                        print(f"{COLOR_GREEN}NeoForge {latest_neoforge} установлен{COLOR_RESET}")
                    else:
                        print(f"{COLOR_RED}NeoForge для версии {version} не найден{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Не удалось получить версии NeoForge{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Ошибка получения версий NeoForge{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка установки модлоадера: {e}{COLOR_RESET}")

def install_version_interactive(version=None):
    if not version:
        version = input(f"{COLOR_YELLOW}Введите версию Minecraft: {COLOR_RESET}").strip()
        if not version:
            print(f"{COLOR_RED}Версия не указана{COLOR_RESET}")
            return
    if input_yes_no("Установить с модлоадером? (да/нет): "):
        print(f"{COLOR_GREEN}Выберите модлоадер:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Forge")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Fabric")
        print(f"{COLOR_YELLOW}3.{COLOR_RESET} Quilt")
        print(f"{COLOR_YELLOW}4.{COLOR_RESET} NeoForge")
        loader_choice = input(f"{COLOR_YELLOW}Ваш выбор (1-4): {COLOR_RESET}").strip()
        if loader_choice not in ['1','2','3','4']:
            print(f"{COLOR_RED}Неверный выбор, установка без модлоадера{COLOR_RESET}")
            loader_choice = None
    else:
        loader_choice = None
    install_version_with_progress(version, loader_choice)

def install_version_from_github(version_name):
    print(f"{COLOR_CYAN}Установка версии {version_name} из GitHub репозитория...{COLOR_RESET}")
    base_url = "https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano/raw/main/minecraft_version"
    zip_url = f"{base_url}/{version_name}.zip"
    minecraft_dir = get_minecraft_dir_for_version(version_name)
    versions_dir = os.path.join(minecraft_dir, "versions", version_name)
    if os.path.exists(versions_dir):
        print(f"{COLOR_YELLOW}Версия {version_name} уже существует. Перезапись?{COLOR_RESET}")
        if not input_yes_no("Перезаписать? (да/нет): "):
            return
        shutil.rmtree(versions_dir)
    os.makedirs(versions_dir, exist_ok=True)
    zip_path = os.path.join(versions_dir, f"{version_name}.zip")
    print(f"{COLOR_CYAN}Скачивание {zip_url}...{COLOR_RESET}")
    def progress_callback(current, total):
        if total > 0:
            percent = (current / total) * 100
            bar_length = 30
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}%{COLOR_RESET}", end="")
    success = download_with_retry(zip_url, zip_path, progress_callback, max_retries=3)
    if not success:
        print(f"{COLOR_RED}Не удалось скачать архив версии{COLOR_RESET}")
        shutil.rmtree(versions_dir, ignore_errors=True)
        return
    print(f"\n{COLOR_CYAN}Распаковка...{COLOR_RESET}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(versions_dir)
        os.remove(zip_path)
        # Проверка JSON удалена
        config = load_config()
        config["selected_version"] = version_name
        save_config(config)
        print(f"{COLOR_GREEN}✓ Версия {version_name} успешно установлена из GitHub!{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка распаковки: {e}{COLOR_RESET}")
        shutil.rmtree(versions_dir, ignore_errors=True)

def set_java_args():
    config = load_config()
    current_args = config.get("java_args", "-Xmx2G -Xms1G")
    print(f"\n{COLOR_CYAN}Текущие общие аргументы Java: {current_args}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Примеры:{COLOR_RESET}")
    print(f"{COLOR_GREEN}  -Xmx4G -Xms2G{COLOR_RESET}")
    print(f"{COLOR_GREEN}  -Xmx8G -Xms4G -XX:+UseG1GC{COLOR_RESET}")
    new_args = input(f"\n{COLOR_YELLOW}Введите новые общие аргументы (Enter для отмены): {COLOR_RESET}")
    if new_args:
        config["java_args"] = new_args
        save_config(config)
        print(f"{COLOR_GREEN}Общие аргументы обновлены!{COLOR_RESET}")

def set_java_args_for_version(version, args):
    config = load_config()
    config["java_args_by_version"][version] = args
    save_config(config)
    print(f"{COLOR_GREEN}Аргументы для версии {version} сохранены{COLOR_RESET}")

def set_memory(gb):
    if not gb.isdigit():
        print(f"{COLOR_RED}Укажите количество гигабайт числом{COLOR_RESET}")
        return
    gb_int = int(gb)
    if gb_int < 1 or gb_int > 32:
        print(f"{COLOR_RED}Укажите значение от 1 до 32 GB{COLOR_RESET}")
        return
    config = load_config()
    current_args = config.get("java_args", "")
    new_args = re.sub(r"-Xmx\d+G", "", current_args)
    new_args = re.sub(r"-Xms\d+G", "", new_args)
    new_args = re.sub(r"\s+", " ", new_args).strip()
    memory_args = f"-Xmx{gb}G -Xms{gb}G"
    if new_args:
        new_args = f"{memory_args} {new_args}"
    else:
        new_args = memory_args
    config["java_args"] = new_args
    save_config(config)
    print(f"{COLOR_GREEN}Общая память установлена на {gb}GB{COLOR_RESET}")

minecraft_processes = []
hotkey_thread_running = False

def monitor_hotkey(proc, pid):
    global hotkey_thread_running
    if not KEYBOARD_AVAILABLE:
        return
    try:
        keyboard.wait('alt+shift')
        if proc.poll() is None:
            print(f"\n{COLOR_YELLOW}Горячая клавиша Alt+Shift нажата, завершение Minecraft (PID {pid})...{COLOR_RESET}")
            proc.terminate()
            proc.wait()
    except:
        pass
    finally:
        hotkey_thread_running = False

def launch_minecraft_thread(version, java_path, java_args_str, username, minecraft_dir, account_type, access_token=None):
    try:
        options = {'username': username, 'uuid': '', 'token': ''}
        if account_type == 'ely' and access_token:
            print(f"{COLOR_YELLOW}Авторизация Ely.by: требует доработки.{COLOR_RESET}")
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_dir, options)
        java_args = java_args_str.split()
        java_executable = java_path if java_path else ('java' if platform.system() != "Linux" else shutil.which("java") or "java")
        minecraft_command = [java_executable] + java_args + minecraft_command[1:]
        proc = subprocess.Popen(
            minecraft_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        pid = proc.pid
        prefix = f"{COLOR_MAGENTA}[Minecraft-{pid}]{COLOR_RESET}"
        minecraft_processes.append((pid, proc))
        print(f"{COLOR_GREEN}Minecraft запущен (PID {pid}){COLOR_RESET}")
        print(f"{COLOR_YELLOW}Для завершения используйте Ctrl+C в этом окне (завершит лаунчер и игру) или закройте окно игры{COLOR_RESET}")
        if KEYBOARD_AVAILABLE:
            threading.Thread(target=monitor_hotkey, args=(proc, pid), daemon=True).start()
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"{prefix} {line.rstrip()}")
            else:
                break
        proc.wait()
        for i, (p, pr) in enumerate(minecraft_processes):
            if p == pid:
                minecraft_processes.pop(i)
                break
        print(f"{COLOR_GREEN}Minecraft (PID {pid}) завершил работу{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка запуска в потоке: {e}{COLOR_RESET}")

def launch_minecraft(version=None):
    config = load_config()
    if not version:
        version = config.get("selected_version")
    if not version:
        print(f"{COLOR_RED}Сначала установите версию Minecraft!{COLOR_RESET}")
        return
    accounts = load_accounts()
    current_account_id = config.get("current_account")
    if not current_account_id or not any(a["id"] == current_account_id for a in accounts):
        print(f"{COLOR_RED}Сначала настройте аккаунт!{COLOR_RESET}")
        return
    account = next((a for a in accounts if a["id"] == current_account_id), None)
    if not account:
        print(f"{COLOR_RED}Аккаунт не найден!{COLOR_RESET}")
        return
    username = account["username"]
    minecraft_dir = get_minecraft_dir_for_version(version)
    java_path = None
    if version in config["java_path_by_version"]:
        java_path = config["java_path_by_version"][version]
        print(f"{COLOR_CYAN}Используется Java для версии: {java_path}{COLOR_RESET}")
    elif config.get("java_path"):
        java_path = config["java_path"]
        print(f"{COLOR_CYAN}Используется общий путь Java: {java_path}{COLOR_RESET}")
    else:
        auto_java = find_suitable_java(version)
        if auto_java:
            java_path = auto_java
            print(f"{COLOR_CYAN}Автоматически найдена подходящая Java: {java_path}{COLOR_RESET}")
        else:
            print(f"{COLOR_YELLOW}Не задан путь к Java, будет использована системная{COLOR_RESET}")
    if java_path and os.path.exists(java_path):
        java_version = get_java_version(java_path)
        if java_version:
            print(f"{COLOR_GREEN}Версия Java: {java_version}{COLOR_RESET}")
            required = get_required_java_version(version)
            if java_version < required:
                print(f"{COLOR_RED}ВНИМАНИЕ: Для Minecraft {version} требуется Java {required} или выше!{COLOR_RESET}")
                print(f"{COLOR_RED}Текущая Java: {java_version}{COLOR_RESET}")
                if not input_yes_no("Продолжить запуск? (да/нет): "):
                    return
        else:
            print(f"{COLOR_YELLOW}Не удалось определить версию Java{COLOR_RESET}")
    if version in config["java_args_by_version"]:
        java_args_str = config["java_args_by_version"][version]
    else:
        java_args_str = config.get("java_args", "-Xmx2G -Xms1G")
    print(f"{COLOR_CYAN}ЗАПУСК MINECRAFT{COLOR_RESET}")
    print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    print(f"{COLOR_GREEN}Версия:{COLOR_RESET} {version}")
    print(f"{COLOR_GREEN}Аккаунт:{COLOR_RESET} {username}")
    print(f"{COLOR_GREEN}Аргументы:{COLOR_RESET} {java_args_str}")
    memory_match = re.search(r'-Xmx(\d+)G', java_args_str)
    if memory_match:
        print(f"{COLOR_GREEN}Память:{COLOR_RESET} {memory_match.group(1)}GB")
    print(f"{COLOR_GREEN}Папка:{COLOR_RESET} {minecraft_dir}")
    print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    access_token = account.get("access_token") if account.get("type") == "ely" else None
    thread = threading.Thread(
        target=launch_minecraft_thread,
        args=(version, java_path, java_args_str, username, minecraft_dir, account.get('type'), access_token),
        daemon=True
    )
    thread.start()

def delayed_launch(version, delay_seconds, count):
    try:
        delay = int(delay_seconds)
        cnt = int(count)
    except ValueError:
        print(f"{COLOR_RED}Неверные аргументы. Используйте: отложенный запуск <версия> <секунды> <количество>{COLOR_RESET}")
        return
    print(f"{COLOR_CYAN}Запланирован запуск {cnt} клиентов версии {version} через {delay} секунд{COLOR_RESET}")
    def launch_wrapper():
        for i in range(cnt):
            threading.Timer(i * 2, lambda: launch_minecraft(version)).start()
    threading.Timer(delay, launch_wrapper).start()

def show_info():
    config = load_config()
    info_lines = []
    info_lines.append(f"{COLOR_CYAN}Последние новости Minecraft{COLOR_RESET}")
    info_lines.append(f"{COLOR_BLUE}- https://t.me/nerkinboat{COLOR_RESET}")
    info_lines.append(f"{COLOR_BLUE}- https://www.youtube.com/@Nerkin/{COLOR_RESET}")
    info_lines.append(f"{COLOR_CYAN}- Реклама:{COLOR_RESET}")
    info_lines.append(f"{COLOR_BLUE}- https://t.me/playdacha Айпи: playdacha.ru{COLOR_RESET}")
    info_lines.append(f"{COLOR_CYAN}- Ванильный сервер майнкрафт. Есть приваты и команда /home. Маленькое и дружелюбное комьюнити.{COLOR_RESET}")
    if config["servers"]:
        info_lines.append(f"{COLOR_CYAN}Ваши серверы:{COLOR_RESET}")
        for s in config["servers"]:
            info_lines.append(f"{COLOR_GREEN}  {s['name']}: {s['ip']}{COLOR_RESET}")
    if config["custom_info_lines"]:
        info_lines.append(f"{COLOR_CYAN}Пользовательская информация:{COLOR_RESET}")
        for line in config["custom_info_lines"]:
            info_lines.append(f"  {line}")
    for hook in plugin_hooks['info']:
        try:
            info_lines = hook(info_lines) or info_lines
        except Exception as e:
            print(f"{COLOR_RED}Ошибка в хуке информации: {e}{COLOR_RESET}")
    for line in info_lines:
        print(line)

def copy_launcher_config():
    desktop = Path.home() / "Desktop"
    if not os.path.exists(CONFIG_FILE):
        print(f"{COLOR_YELLOW}Файл конфига лаунчера не найден{COLOR_RESET}")
        return
    dest = desktop / f"cobalt_launcher_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        shutil.copy2(CONFIG_FILE, dest)
        print(f"{COLOR_GREEN}Конфиг лаунчера скопирован: {dest}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка копирования: {e}{COLOR_RESET}")

def create_backup():
    desktop = Path.home() / "Desktop"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = desktop / f"minecraft_backup_{timestamp}.zip"
    folders_to_backup = ["saves", "resourcepacks", "config", "shaderpacks", "schematics", "mods"]
    print(f"{COLOR_CYAN}Создание резервной копии...{COLOR_RESET}")
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_files = 0
            for folder in folders_to_backup:
                folder_path = os.path.join(MINECRAFT_DIR, folder)
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, MINECRAFT_DIR)
                            zipf.write(file_path, arcname)
                            total_files += 1
                else:
                    print(f"{COLOR_YELLOW}Папка {folder} не существует, пропускаем...{COLOR_RESET}")
            if os.path.exists(CONFIG_FILE):
                zipf.write(CONFIG_FILE, "launcher_config.json")
                total_files += 1
                print(f"{COLOR_GREEN}Добавлен конфиг лаунчера{COLOR_RESET}")
        print(f"{COLOR_GREEN}Резервная копия создана!{COLOR_RESET}")
        print(f"{COLOR_CYAN}Файл: {backup_file}{COLOR_RESET}")
        print(f"{COLOR_CYAN}Файлов сохранено: {total_files}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка создания бэкапа: {e}{COLOR_RESET}")

def open_minecraft_folder():
    try:
        if platform.system() == "Windows":
            os.startfile(MINECRAFT_DIR)
        elif platform.system() == "Darwin":
            subprocess.run(["open", MINECRAFT_DIR], check=False)
        else:
            subprocess.run(["xdg-open", MINECRAFT_DIR], check=False)
        print(f"{COLOR_GREEN}Папка Minecraft открыта: {MINECRAFT_DIR}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия папки: {e}{COLOR_RESET}")

def open_folder(folder_name):
    folder_path = os.path.join(MINECRAFT_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"{COLOR_YELLOW}Папка {folder_name} не существует.{COLOR_RESET}")
        if input_yes_no("Создать папку? (да/нет): "):
            os.makedirs(folder_path, exist_ok=True)
            print(f"{COLOR_GREEN}Папка создана: {folder_path}{COLOR_RESET}")
        else:
            return
    try:
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder_path], check=False)
        else:
            subprocess.run(["xdg-open", folder_path], check=False)
        print(f"{COLOR_GREEN}Папка {folder_name} открыта: {folder_path}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия папки: {e}{COLOR_RESET}")

def copy_latest_log():
    logs_dir = os.path.join(MINECRAFT_DIR, "logs")
    if not os.path.exists(logs_dir):
        print(f"{COLOR_YELLOW}Папка logs не найдена{COLOR_RESET}")
        return
    log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log') or f.endswith('.txt')]
    if not log_files:
        print(f"{COLOR_YELLOW}Лог-файлы не найдены{COLOR_RESET}")
        return
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)))
    source_path = os.path.join(logs_dir, latest_log)
    desktop = Path.home() / "Desktop"
    dest_path = desktop / f"minecraft_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    try:
        shutil.copy2(source_path, dest_path)
        print(f"{COLOR_GREEN}Лог скопирован на рабочий стол: {dest_path}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка копирования лога: {e}{COLOR_RESET}")

def set_java_path():
    config = load_config()
    current_path = config.get("java_path", "Не установлен")
    print(f"\n{COLOR_CYAN}Текущий общий путь к Java: {current_path}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Примеры:{COLOR_RESET}")
    print(f"{COLOR_GREEN}  C:\\Program Files\\Java\\jdk-17\\bin\\java.exe{COLOR_RESET} - Windows")
    print(f"{COLOR_GREEN}  /usr/lib/jvm/java-17-openjdk/bin/java{COLOR_RESET} - Linux")
    new_path = input(f"\n{COLOR_YELLOW}Введите новый путь к Java (Enter для сброса): {COLOR_RESET}")
    if new_path:
        if os.path.exists(new_path):
            config["java_path"] = new_path
            save_config(config)
            print(f"{COLOR_GREEN}Путь к Java обновлен!{COLOR_RESET}")
            java_version = get_java_version(new_path)
            if java_version:
                print(f"{COLOR_GREEN}Версия Java: {java_version}{COLOR_RESET}")
                config["java_version"] = str(java_version)
                save_config(config)
            else:
                print(f"{COLOR_YELLOW}Не удалось определить версию Java{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Указанный путь не существует!{COLOR_RESET}")
    elif new_path == "" and current_path != "Не установлен":
        config["java_path"] = None
        config["java_version"] = "17"
        save_config(config)
        print(f"{COLOR_GREEN}Общий путь к Java сброшен, будет использована системная Java.{COLOR_RESET}")

def toggle_separate_dirs():
    config = load_config()
    current = config.get("separate_version_dirs", False)
    config["separate_version_dirs"] = not current
    status = "включено" if config["separate_version_dirs"] else "выключено"
    print(f"{COLOR_CYAN}Отдельные папки для версий: {COLOR_GREEN}{status}{COLOR_RESET}")
    if config["separate_version_dirs"]:
        print(f"{COLOR_YELLOW}Теперь каждая версия Minecraft будет установлена в отдельную папку.{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}Все версии Minecraft будут использовать одну папку .minecraft{COLOR_RESET}")
    save_config(config)

def install_java():
    print(f"{COLOR_CYAN}Автоматическая установка Java...{COLOR_RESET}")
    system = platform.system()
    arch = platform.machine().lower()
    os_map = {
        "Windows": "windows",
        "Linux": "linux",
        "Darwin": "mac"
    }
    os_name = os_map.get(system)
    if not os_name:
        print(f"{COLOR_RED}Операционная система {system} не поддерживается{COLOR_RESET}")
        return
    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "i386": "x86",
        "i686": "x86",
        "aarch64": "arm",
        "armv7l": "arm"
    }
    arch_api = arch_map.get(arch.lower(), arch)
    if arch_api not in ["x64", "x86", "arm", "ppc64le", "s390x"]:
        print(f"{COLOR_RED}Архитектура {arch} не поддерживается{COLOR_RESET}")
        return
    java_versions = {
        "1": {"name": "Java 8", "version": "8"},
        "2": {"name": "Java 11", "version": "11"},
        "3": {"name": "Java 17", "version": "17"},
        "4": {"name": "Java 21", "version": "21"}
    }
    print(f"{COLOR_YELLOW}Выберите версию Java для установки:{COLOR_RESET}")
    print(f"{COLOR_RED}ВНИМАНИЕ: Для Minecraft 1.17+ требуется Java 17 или выше!{COLOR_RESET}")
    for key, value in java_versions.items():
        print(f"{COLOR_CYAN}{key}.{COLOR_RESET} {value['name']}")
    choice = input(f"{COLOR_YELLOW}Ваш выбор (1-4, рекомендуется 3 для Java 17): {COLOR_RESET}")
    if choice not in java_versions:
        print(f"{COLOR_RED}Неверный выбор{COLOR_RESET}")
        return
    java_version = java_versions[choice]["version"]
    print(f"{COLOR_CYAN}Получение ссылки для скачивания...{COLOR_RESET}")
    url, ext = get_java_download_url(java_version, os_name, arch_api)
    if not url:
        print(f"{COLOR_RED}Не удалось получить ссылку для скачивания Java {java_version}{COLOR_RESET}")
        return
    java_install_dir = os.path.join(JAVA_DIR, f"java_{java_version}")
    os.makedirs(java_install_dir, exist_ok=True)
    download_path = os.path.join(java_install_dir, f"java.{ext}")
    print(f"{COLOR_CYAN}Скачивание Java {java_version}...{COLOR_RESET}")
    print(f"{COLOR_YELLOW}URL: {url}{COLOR_RESET}")
    def progress_callback(current, total):
        if total > 0:
            percent = (current / total) * 100
            bar_length = 30
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}% ({current/1024/1024:.1f} MB / {total/1024/1024:.1f} MB){COLOR_RESET}", end="")
    success = download_with_retry(url, download_path, progress_callback, max_retries=3)
    if not success:
        print(f"{COLOR_RED}Не удалось скачать Java{COLOR_RESET}")
        return
    print(f"\n{COLOR_GREEN}Скачивание завершено{COLOR_RESET}")
    print(f"{COLOR_CYAN}Распаковка...{COLOR_RESET}")
    try:
        if ext == "zip":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(java_install_dir)
        else:
            with tarfile.open(download_path, 'r:gz') as tar_ref:
                tar_ref.extractall(java_install_dir)
        os.remove(download_path)
    except Exception as e:
        print(f"{COLOR_RED}Ошибка распаковки: {e}{COLOR_RESET}")
        return
    java_exe = find_java_executable_in_dir(java_install_dir)
    if java_exe:
        config = load_config()
        config["java_path"] = java_exe
        config["java_version"] = java_version
        save_config(config)
        print(f"{COLOR_GREEN}Java {java_version} успешно установлена!{COLOR_RESET}")
        print(f"{COLOR_CYAN}Путь к Java: {java_exe}{COLOR_RESET}")
        if input_yes_no("Проверить установку Java? (да/нет): "):
            try:
                result = subprocess.run([java_exe, "-version"], capture_output=True, text=True, shell=True)
                print(f"{COLOR_GREEN}Java версия:{COLOR_RESET}")
                lines = result.stderr.split('\n') if result.stderr else result.stdout.split('\n')
                for line in lines[:3]:
                    print(line)
            except Exception as e:
                print(f"{COLOR_RED}Ошибка проверки Java: {e}{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}Java установлена, но исполняемый файл не найден{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Установите путь к Java вручную командой 'джава'{COLOR_RESET}")

def copy_crash_reports():
    crashes_dir = os.path.join(MINECRAFT_DIR, "crashes")
    if not os.path.exists(crashes_dir):
        print(f"{COLOR_YELLOW}Папка crashes не найдена{COLOR_RESET}")
        return
    crash_files = []
    for root, dirs, files in os.walk(crashes_dir):
        for file in files:
            if file.endswith('.txt') and 'crash' in file.lower():
                crash_files.append(os.path.join(root, file))
    if not crash_files:
        print(f"{COLOR_YELLOW}Краш-репорты не найдены{COLOR_RESET}")
        return
    desktop = Path.home() / "Desktop"
    crash_folder = desktop / f"minecraft_crash_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(crash_folder, exist_ok=True)
    copied_files = 0
    for crash_file in crash_files:
        try:
            dest_file = os.path.join(crash_folder, os.path.basename(crash_file))
            shutil.copy2(crash_file, dest_file)
            copied_files += 1
        except Exception as e:
            print(f"{COLOR_RED}Ошибка копирования {crash_file}: {e}{COLOR_RESET}")
    if copied_files > 0:
        print(f"{COLOR_GREEN}Скопировано {copied_files} краш-репортов в папку: {crash_folder}{COLOR_RESET}")
        try:
            if platform.system() == "Windows":
                os.startfile(crash_folder)
            elif platform.system() == "Darwin":
                subprocess.run(["open", crash_folder], check=False)
            else:
                subprocess.run(["xdg-open", crash_folder], check=False)
        except Exception:
            pass
    else:
        print(f"{COLOR_RED}Не удалось скопировать ни одного краш-репорта{COLOR_RESET}")

def delete_launcher_data():
    print(f"{COLOR_RED}ВНИМАНИЕ: Будет полностью удалена папка {LAUNCHER_DATA_DIR}{COLOR_RESET}")
    print(f"{COLOR_RED}Это удалит все установленные версии, аккаунты, настройки и моды!{COLOR_RESET}")
    if input_yes_no("Вы уверены, что хотите удалить лаунчер? (да/нет): "):
        try:
            shutil.rmtree(LAUNCHER_DATA_DIR)
            print(f"{COLOR_GREEN}Папка лаунчера удалена. Программа будет закрыта.{COLOR_RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"{COLOR_RED}Ошибка удаления: {e}{COLOR_RESET}")
    else:
        print(f"{COLOR_GREEN}Операция отменена{COLOR_RESET}")

def load_mods_favorites():
    if os.path.exists(MODS_FAVORITES_FILE):
        try:
            with open(MODS_FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_mods_favorites(favorites):
    with open(MODS_FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, indent=4, ensure_ascii=False)

def add_mod_to_favorites(mod_info):
    favorites = load_mods_favorites()
    for fav in favorites:
        if fav.get('id') == mod_info.get('id'):
            print(f"{COLOR_YELLOW}Мод уже в избранном!{COLOR_RESET}")
            return False
    mod_info['added_at'] = datetime.now().isoformat()
    favorites.append(mod_info)
    save_mods_favorites(favorites)
    print(f"{COLOR_GREEN}Мод '{mod_info.get('title', 'Без названия')}' добавлен в избранное!{COLOR_RESET}")
    return True

def remove_mod_from_favorites(mod_id):
    favorites = load_mods_favorites()
    new_favorites = [fav for fav in favorites if fav.get('id') != mod_id]
    if len(new_favorites) < len(favorites):
        save_mods_favorites(new_favorites)
        print(f"{COLOR_GREEN}Мод удален из избранного!{COLOR_RESET}")
        return True
    else:
        print(f"{COLOR_RED}Мод не найден в избранном!{COLOR_RESET}")
        return False

def search_mods_modrinth(query: str, limit: int = 20) -> List[Dict]:
    print(f"{COLOR_CYAN}Поиск модов на Modrinth...{COLOR_RESET}")
    try:
        url = f"https://api.modrinth.com/v2/search?query={query}&limit={limit}&facets=[[\"project_type:mod\"]]"
        headers = {"User-Agent": "CobaltLauncher/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        mods = []
        for hit in data.get('hits', []):
            mod_info = {
                'id': hit.get('project_id'),
                'title': hit.get('title', 'Без названия'),
                'description': hit.get('description', 'Нет описания'),
                'downloads': hit.get('downloads', 0),
                'follows': hit.get('follows', 0),
                'author': hit.get('author', 'Неизвестен'),
                'versions': hit.get('versions', []),
                'icon_url': hit.get('icon_url'),
                'slug': hit.get('slug'),
                'source': 'modrinth'
            }
            mods.append(mod_info)
        return mods
    except Exception as e:
        print(f"{COLOR_RED}Ошибка поиска на Modrinth: {e}{COLOR_RESET}")
        return []

def show_mod_details(mod_info: Dict):
    print(f"\n{COLOR_CYAN}════════════════════════════════════════════════{COLOR_RESET}")
    print(f"{COLOR_GREEN}Название:{COLOR_RESET} {mod_info.get('title', 'Без названия')}")
    print(f"{COLOR_GREEN}Источник:{COLOR_RESET} {mod_info.get('source', 'Неизвестен').upper()}")
    if 'description' in mod_info:
        desc = mod_info['description']
        if len(desc) > 200:
            desc = desc[:200] + "..."
        print(f"{COLOR_GREEN}Описание:{COLOR_RESET} {desc}")
    if 'downloads' in mod_info:
        print(f"{COLOR_GREEN}Загрузки:{COLOR_RESET} {mod_info['downloads']:,}")
    if 'author' in mod_info:
        print(f"{COLOR_GREEN}Автор:{COLOR_RESET} {mod_info['author']}")
    print(f"{COLOR_CYAN}════════════════════════════════════════════════{COLOR_RESET}")

def get_mod_versions(mod_id: str) -> List[Dict]:
    try:
        url = f"https://api.modrinth.com/v2/project/{mod_id}/version"
        headers = {"User-Agent": "CobaltLauncher/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения версий мода: {e}{COLOR_RESET}")
        return []

def download_mod(mod_info: Dict, game_version: str = None):
    print(f"{COLOR_CYAN}Скачивание мода '{mod_info.get('title')}'...{COLOR_RESET}")
    try:
        mod_id = mod_info.get('id')
        versions = get_mod_versions(mod_id)
        if not versions:
            print(f"{COLOR_RED}Нет доступных версий для скачивания{COLOR_RESET}")
            return
        if game_version:
            compatible_versions = [v for v in versions if game_version in v.get('game_versions', [])]
        else:
            compatible_versions = versions
        if not compatible_versions:
            print(f"{COLOR_YELLOW}Нет версий, совместимых с Minecraft {game_version or 'любой'}{COLOR_RESET}")
            return
        if len(compatible_versions) == 1:
            selected_version = compatible_versions[0]
        else:
            print(f"{COLOR_GREEN}Доступные версии мода:{COLOR_RESET}")
            for i, ver in enumerate(compatible_versions[:10], 1):
                loaders = ', '.join(ver.get('loaders', []))
                mc_versions = ', '.join(ver.get('game_versions', [])[:3])
                print(f"{COLOR_YELLOW}{i}.{COLOR_RESET} {ver.get('version_number')} [Загрузчики: {loaders}] [MC: {mc_versions}...]")
            choice = input(f"{COLOR_YELLOW}Выберите версию (1-{min(10, len(compatible_versions))}): {COLOR_RESET}")
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(compatible_versions):
                    selected_version = compatible_versions[idx]
                else:
                    print(f"{COLOR_RED}Неверный выбор{COLOR_RESET}")
                    return
            else:
                print(f"{COLOR_RED}Неверный выбор{COLOR_RESET}")
                return
        dependencies = selected_version.get('dependencies', [])
        if dependencies:
            print(f"{COLOR_CYAN}Зависимости:{COLOR_RESET}")
            for dep in dependencies:
                if dep.get('dependency_type') == 'required':
                    print(f"  - {dep.get('version_id', 'Неизвестно')} (обязательно)")
        jar_file = None
        for file in selected_version.get('files', []):
            if file.get('filename', '').endswith('.jar'):
                jar_file = file
                break
        if not jar_file:
            print(f"{COLOR_RED}Не найден файл .jar для скачивания{COLOR_RESET}")
            return
        mods_dir = os.path.join(MINECRAFT_DIR, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        download_url = jar_file.get('url')
        filename = jar_file.get('filename', f"mod_{mod_id}.jar")
        filepath = os.path.join(mods_dir, filename)
        print(f"{COLOR_YELLOW}Скачивание {filename}...{COLOR_RESET}")
        def progress_callback(current, total):
            if total > 0:
                percent = (current / total) * 100
                bar_length = 30
                filled = int(bar_length * current / total)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}%{COLOR_RESET}", end="")
        success = download_with_retry(download_url, filepath, progress_callback, max_retries=3)
        if success:
            print(f"\n{COLOR_GREEN}✓ Мод успешно скачан: {filepath}{COLOR_RESET}")
        else:
            print(f"\n{COLOR_RED}Не удалось скачать мод{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка скачивания мода: {e}{COLOR_RESET}")

def manage_mods_menu():
    while True:
        print(f"\n{COLOR_CYAN}УПРАВЛЕНИЕ МОДАМИ{COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        print(f"{COLOR_GREEN}Выберите действие:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Поиск модов на Modrinth")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Показать избранные моды")
        print(f"{COLOR_YELLOW}3.{COLOR_RESET} Назад")
        choice = input(f"{COLOR_YELLOW}Выберите: {COLOR_RESET}")
        if choice == '1':
            search_mods_menu()
        elif choice == '2':
            show_favorites_menu()
        elif choice == '3':
            break
        else:
            print(f"{COLOR_RED}Неверный выбор!{COLOR_RESET}")

def search_mods_menu():
    query = input(f"{COLOR_YELLOW}Введите запрос для поиска: {COLOR_RESET}")
    if not query:
        print(f"{COLOR_RED}Запрос не может быть пустым!{COLOR_RESET}")
        return
    mods = search_mods_modrinth(query)
    if not mods:
        print(f"{COLOR_YELLOW}Моды не найдены{COLOR_RESET}")
        return
    while True:
        print(f"\n{COLOR_CYAN}НАЙДЕННЫЕ МОДЫ ({len(mods)}){COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        for i, mod in enumerate(mods, 1):
            title = mod.get('title', 'Без названия')
            if len(title) > 40:
                title = title[:37] + "..."
            print(f"{COLOR_YELLOW}{i:3}.{COLOR_RESET} {title}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        print(f"{COLOR_GREEN}Команды:{COLOR_RESET}")
        print(f"{COLOR_CYAN}число{COLOR_RESET} - просмотреть информацию о моде")
        print(f"{COLOR_CYAN}в{COLOR_RESET} - вернуться назад")
        choice = input(f"{COLOR_YELLOW}Выберите мод или команду: {COLOR_RESET}").lower()
        if choice == 'в':
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(mods):
                mod_details_menu(mods[idx])
            else:
                print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Неверная команда{COLOR_RESET}")

def mod_details_menu(mod_info: Dict):
    while True:
        show_mod_details(mod_info)
        print(f"\n{COLOR_GREEN}Действия с модом:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Скачать мод")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Добавить в избранное")
        print(f"{COLOR_YELLOW}3.{COLOR_RESET} Назад")
        choice = input(f"{COLOR_YELLOW}Выберите действие: {COLOR_RESET}")
        if choice == '1':
            config = load_config()
            game_version = config.get("selected_version")
            if game_version:
                match = re.search(r'(\d+\.\d+(?:\.\d+)?)', game_version)
                if match:
                    game_version = match.group(1)
            if not game_version:
                game_version = input(f"{COLOR_YELLOW}Введите версию Minecraft (например, 1.20.1): {COLOR_RESET}")
            download_mod(mod_info, game_version)
        elif choice == '2':
            add_mod_to_favorites(mod_info)
        elif choice == '3':
            break
        else:
            print(f"{COLOR_RED}Неверный выбор!{COLOR_RESET}")

def show_favorites_menu():
    favorites = load_mods_favorites()
    if not favorites:
        print(f"{COLOR_YELLOW}У вас пока нет избранных модов{COLOR_RESET}")
        return
    while True:
        print(f"\n{COLOR_CYAN}ИЗБРАННЫЕ МОДЫ ({len(favorites)}){COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        for i, fav in enumerate(favorites, 1):
            title = fav.get('title', 'Без названия')
            if len(title) > 40:
                title = title[:37] + "..."
            source = fav.get('source', 'unknown').upper()
            print(f"{COLOR_YELLOW}{i:3}.{COLOR_RESET} {title} [{source}]")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        print(f"{COLOR_GREEN}Команды:{COLOR_RESET}")
        print(f"{COLOR_CYAN}число{COLOR_RESET} - просмотреть информацию о моде")
        print(f"{COLOR_CYAN}у{COLOR_RESET} - удалить мод из избранного")
        print(f"{COLOR_CYAN}в{COLOR_RESET} - вернуться назад")
        choice = input(f"{COLOR_YELLOW}Выберите мод или команду: {COLOR_RESET}").lower()
        if choice == 'в':
            break
        elif choice == 'у':
            mod_id = input(f"{COLOR_YELLOW}Введите ID мода для удаления: {COLOR_RESET}")
            remove_mod_from_favorites(mod_id)
            favorites = load_mods_favorites()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(favorites):
                mod_details_menu(favorites[idx])
            else:
                print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Неверная команда{COLOR_RESET}")

def open_alt_mod_site():
    url = "https://ru-minecraft.ru"
    print(f"{COLOR_CYAN}Открытие ru-minecraft.ru в браузере...{COLOR_RESET}")
    try:
        webbrowser.open(url)
        print(f"{COLOR_GREEN}Сайт открыт в браузере!{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия браузера: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Вы можете открыть сайт вручную: {url}{COLOR_RESET}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def signal_handler(sig, frame):
    global minecraft_processes
    for pid, proc in minecraft_processes:
        if proc.poll() is None:
            print(f"{COLOR_YELLOW}Завершение Minecraft (PID {pid})...{COLOR_RESET}")
            proc.terminate()
    sys.exit(0)

# Триггеры к командам, мелкие функции
def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    load_plugins()
    print_banner()
    config = load_config()
    print(f"{COLOR_MAGENTA}Не знаете команды? Введите '{COLOR_GREEN}помощь{COLOR_MAGENTA}' для списка команд{COLOR_RESET}")
    while True:
        try:
            user_input = input(f"\n{COLOR_CYAN}Введите команду>{COLOR_RESET} ").strip()
            if not user_input:
                continue
            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            if execute_user_command(cmd, args):
                continue
            if cmd == 'помощь' or cmd == 'help':
                print_help()
            elif cmd == 'акк' or cmd == 'accounts':
                manage_accounts_scrollable()
            elif cmd == 'альфа':
                list_versions_by_type("alpha")
            elif cmd == 'бета':
                list_versions_by_type("beta")
            elif cmd == 'снапшоты':
                list_versions_by_type("snapshot")
            elif cmd == 'релизы':
                list_versions_by_type("release")
            elif cmd == 'установить' and len(args) > 0 and args[0] == 'джава':
                install_java()
            elif cmd == 'установить' and len(args) > 0 and args[0] == 'гитхаб':
                if len(args) > 1:
                    install_version_from_github(args[1])
                else:
                    print(f"{COLOR_RED}Укажите название версии. Например: 'установить гитхаб 1.16.5-custom'{COLOR_RESET}")
            elif cmd == 'установить':
                if len(args) == 0:
                    install_version_interactive()
                elif len(args) == 1:
                    install_version_interactive(args[0])
                else:
                    version = args[0]
                    loader_map = {'forge': '1', 'fabric': '2', 'quilt': '3', 'neoforge': '4'}
                    loader_name = args[1].lower()
                    if loader_name in loader_map:
                        install_version_with_progress(version, loader_map[loader_name])
                    else:
                        print(f"{COLOR_RED}Неизвестный модлоадер. Доступны: forge, fabric, quilt, neoforge{COLOR_RESET}")
            elif cmd == 'запуск' or cmd == 'launch':
                if len(args) > 0:
                    launch_minecraft(args[0])
                else:
                    launch_minecraft()
            elif cmd == 'отложенный' and len(args) >= 3 and args[0] == 'запуск':
                version = args[1]
                delay = args[2]
                count = args[3] if len(args) > 3 else '1'
                delayed_launch(version, delay, count)
            elif cmd == 'арг' or cmd == 'args':
                if len(args) >= 2 and args[0] == 'версии':
                    version = args[1]
                    arg_string = ' '.join(args[2:]) if len(args) > 2 else ''
                    set_java_args_for_version(version, arg_string)
                else:
                    set_java_args()
            elif cmd == 'джава_версии':
                if len(args) >= 1:
                    version = args[0]
                    path = args[1] if len(args) > 1 else None
                    set_java_path_for_version(version, path)
                else:
                    print(f"{COLOR_RED}Укажите версию. Например: 'джава_версии 1.12.2 C:\\java8\\bin\\java.exe'{COLOR_RESET}")
            elif cmd == 'память':
                if len(args) > 0:
                    set_memory(args[0])
                else:
                    print(f"{COLOR_RED}Укажите количество гигабайт. Например: 'память 4'{COLOR_RESET}")
            elif cmd == 'папка' and len(args) > 0 and args[0] == 'модов':
                open_folder("mods")
            elif cmd == 'моды':
                manage_mods_menu()
            elif cmd == 'плагины':
                manage_plugins()
            elif cmd == 'ресурспак':
                open_folder("resourcepacks")
            elif cmd == 'миры':
                open_folder("saves")
            elif cmd == 'скриншоты':
                open_folder("screenshots")
            elif cmd == 'конфиги':
                open_folder("config")
            elif cmd == 'схемы':
                open_folder("schematics")
            elif cmd == 'инфо':
                show_info()
            elif cmd == 'заметка':
                if len(args) > 0:
                    note_text = ' '.join(args)
                    with open(NOTES_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note_text}\n")
                    print(f"{COLOR_GREEN}Заметка добавлена!{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Введите текст заметки. Например: 'заметка купить хлеб'{COLOR_RESET}")
            elif cmd == 'заметки' or cmd == 'notes':
                if os.path.exists(NOTES_FILE):
                    print(f"{COLOR_CYAN}ЗАМЕТКИ{COLOR_RESET}")
                    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(f"{COLOR_YELLOW}Заметок пока нет{COLOR_RESET}")
            elif cmd == 'бэкап' or cmd == 'backup':
                create_backup()
            elif cmd == 'конфиг лаунчера' or (cmd == 'конфиг' and len(args) > 0 and args[0] == 'лаунчера'):
                copy_launcher_config()
            elif cmd == 'папка' or cmd == 'folder':
                open_minecraft_folder()
            elif cmd == 'лог' or cmd == 'log':
                copy_latest_log()
            elif cmd == 'краш' or cmd == 'crash':
                copy_crash_reports()
            elif cmd == 'джава':
                set_java_path()
            elif user_input.lower() == 'отдельные папки':
                toggle_separate_dirs()
            elif (cmd == 'альт' and len(args) > 0 and args[0] == 'мод') or cmd == 'альт мод':
                open_alt_mod_site()
            elif cmd == 'добавить' and len(args) > 0 and args[0] == 'команду':
                wizard_add_command()
            elif cmd == 'удалить' and len(args) > 1 and args[0] == 'команду':
                remove_user_command(args[1])
            elif cmd == 'команды':
                list_user_commands()
            elif cmd == 'добавить' and len(args) >= 2 and args[0] == 'сервер':
                name = args[1]
                ip = args[2] if len(args) > 2 else input("Введите IP сервера: ")
                version = args[3] if len(args) > 3 else None
                add_server(name, ip, version)
            elif cmd == 'удалить' and len(args) >= 2 and args[0] == 'сервер':
                remove_server(args[1])
            elif cmd == 'добавить' and len(args) >= 2 and args[0] == 'инфо':
                line = ' '.join(args[1:])
                add_custom_info_line(line)
            elif cmd == 'очистить инфо' or (cmd == 'очистить' and len(args) > 0 and args[0] == 'инфо'):
                clear_custom_info()
            elif cmd == 'удалить' and len(args) > 0 and args[0] == 'лаунчер':
                delete_launcher_data()
            else:
                print(f"{COLOR_RED}Неизвестная команда: {cmd}{COLOR_RESET}")
                print(f"{COLOR_YELLOW}Введите '{COLOR_GREEN}помощь{COLOR_YELLOW}' для списка команд{COLOR_RESET}")
        except KeyboardInterrupt:
            print(f"\n{COLOR_CYAN}Выход из лаунчера...{COLOR_RESET}")
            break
        except Exception as e:
            print(f"{COLOR_RED}Ошибка: {e}{COLOR_RESET}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{COLOR_RED}Критическая ошибка: {e}{COLOR_RESET}")
        input("Нажмите Enter для выхода...")