import os
import sys
import json
import zipfile
import requests
import subprocess
import platform
import shutil
import re
import threading
import time
from pathlib import Path
from datetime import datetime
import minecraft_launcher_lib
from colored import fg, attr

COLOR_RED = fg('red')
COLOR_GREEN = fg('green')
COLOR_YELLOW = fg('yellow')
COLOR_BLUE = fg('blue')
COLOR_MAGENTA = fg('magenta')
COLOR_CYAN = fg('cyan')
COLOR_RESET = attr('reset')

MINECRAFT_DIR = str(Path.home() / ".minecraft")
LAUNCHER_DATA_DIR = str(Path.home() / ".cobalt_launcher_nano")
CONFIG_FILE = os.path.join(LAUNCHER_DATA_DIR, "config.json")
NOTES_FILE = os.path.join(LAUNCHER_DATA_DIR, "notes.txt")
ACCOUNTS_FILE = os.path.join(LAUNCHER_DATA_DIR, "accounts.json")
JAVA_DIR = os.path.join(LAUNCHER_DATA_DIR, "java")

os.makedirs(LAUNCHER_DATA_DIR, exist_ok=True)
os.makedirs(JAVA_DIR, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "separate_version_dirs" not in config:
                    config["separate_version_dirs"] = False
                if "java_path" not in config:
                    config["java_path"] = None
                return config
        except json.JSONDecodeError:
            return {"java_args": "-Xmx2G -Xms1G", "selected_version": None, "current_account": None, "separate_version_dirs": False, "java_path": None}
    return {"java_args": "-Xmx2G -Xms1G", "selected_version": None, "current_account": None, "separate_version_dirs": False, "java_path": None}

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
    account = {
        "id": len(accounts) + 1,
        "username": username,
        "type": "offline",
        "created_at": datetime.now().isoformat()
    }
    accounts.append(account)
    save_accounts(accounts)
    return account

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
        
        print(f"{COLOR_CYAN}Страница {self.current_page + 1}/{(len(self.items) + self.page_size - 1) // self.page_size}{COLOR_RESET}")
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
        
        for i, item in enumerate(page_items, start=1):
            print(f"{COLOR_YELLOW}{start_idx + i:3}.{COLOR_RESET} {item}")
        
        print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    
    def navigate(self):
        while True:
            self.display_page()
            print(f"\n{COLOR_GREEN}Команды:{COLOR_RESET}")
            print(f"{COLOR_CYAN}н{COLOR_RESET} - следующая страница")
            print(f"{COLOR_CYAN}п{COLOR_RESET} - предыдущая страница")
            print(f"{COLOR_CYAN}число{COLOR_RESET} - выбрать элемент")
            print(f"{COLOR_CYAN}в{COLOR_RESET} - выйти")
            
            choice = input(f"{COLOR_YELLOW}Выберите: {COLOR_RESET}").lower()
            
            if choice == 'н':
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
{COLOR_CYAN}Версия: {COLOR_RED}0.7 Alpha{COLOR_RESET}
{COLOR_CYAN}Автор: {COLOR_GREEN}M1rotvorets{COLOR_RESET}
{COLOR_CYAN}Помощники: {COLOR_YELLOW}WaterBucket, Nosok{COLOR_RESET}
{COLOR_CYAN}Репозиторий: {COLOR_BLUE}https://github.com/m1r0tv0rets/Cobalt_Launcher_Nano{COLOR_RESET}
{COLOR_MAGENTA}Для освобождения консоли нажмите {COLOR_RED}Alt+Shift{COLOR_RESET}{COLOR_MAGENTA} в любой момент!{COLOR_RESET}
    """
    print(banner)

def print_help():
    help_text = f"""
{COLOR_CYAN}ДОСТУПНЫЕ КОМАНДЫ:{COLOR_RESET}
{COLOR_GREEN}помощь{COLOR_RESET}      - Показать это сообщение
{COLOR_GREEN}акк{COLOR_RESET}         - Управление аккаунтами
{COLOR_GREEN}альфа{COLOR_RESET}       - Показать альфа версии
{COLOR_GREEN}бета{COLOR_RESET}        - Показать бета версии
{COLOR_GREEN}снапшоты{COLOR_RESET}    - Показать снапшоты
{COLOR_GREEN}релизы{COLOR_RESET}      - Показать релизные версии
{COLOR_GREEN}установить{COLOR_RESET}  - Установить версию
{COLOR_GREEN}запуск{COLOR_RESET}      - Запустить Minecraft
{COLOR_GREEN}арг{COLOR_RESET}         - Настройка аргументов Java
{COLOR_GREEN}память{COLOR_RESET}      - Установить объем памяти
{COLOR_GREEN}моды{COLOR_RESET}        - Открыть папку модов
{COLOR_GREEN}ресурспак{COLOR_RESET}   - Открыть папку ресурспаков
{COLOR_GREEN}миры{COLOR_RESET}        - Открыть папку миров
{COLOR_GREEN}конфиги{COLOR_RESET}     - Открыть папку конфигов
{COLOR_GREEN}схемы{COLOR_RESET}       - Открыть папку схем
{COLOR_GREEN}инфо{COLOR_RESET}        - Полезная информация
{COLOR_GREEN}заметка{COLOR_RESET}     - Добавить заметку
{COLOR_GREEN}заметки{COLOR_RESET}     - Показать все заметки
{COLOR_GREEN}бэкап{COLOR_RESET}       - Создать резервную копию
{COLOR_GREEN}папка{COLOR_RESET}       - Открыть папку Minecraft
{COLOR_GREEN}лог{COLOR_RESET}         - Скопировать последний лог на рабочий стол
{COLOR_GREEN}джава{COLOR_RESET}       - Установить путь к Java
{COLOR_GREEN}отдельные папки{COLOR_RESET} - Включить/выключить отдельные папки для версий
{COLOR_GREEN}выход{COLOR_RESET}       - Выйти из лаунчера
{COLOR_MAGENTA}Для освобождения консоли нажмите {COLOR_RED}Alt+Shift{COLOR_RESET}{COLOR_MAGENTA} в любой момент!{COLOR_RESET}
    """
    print(help_text)

def manage_accounts_scrollable():
    accounts = load_accounts()
    config = load_config()
    
    if not accounts:
        print(f"{COLOR_YELLOW}Аккаунты не найдены{COLOR_RESET}")
        if input_yes_no("Добавить оффлайн аккаунт? (да/нет): "):
            username = input("Введите имя пользователя: ")
            account = add_offline_account(username)
            config["current_account"] = account["id"]
            save_config(config)
            print(f"{COLOR_GREEN}Аккаунт '{username}' добавлен!{COLOR_RESET}")
        return
    
    account_list = []
    for acc in accounts:
        status = f"{COLOR_GREEN}✓{COLOR_RESET}" if config.get("current_account") == acc["id"] else " "
        account_list.append(f"{status} {acc['username']} ({acc['type']}) - ID: {acc['id']}")
    
    scroll_list = ScrollableList(account_list, page_size=15)
    
    print(f"{COLOR_CYAN}УПРАВЛЕНИЕ АККАУНТАМИ{COLOR_RESET}")
    
    while True:
        print(f"\n{COLOR_GREEN}Выберите действие:{COLOR_RESET}")
        print(f"{COLOR_YELLOW}1.{COLOR_RESET} Просмотр аккаунтов")
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Добавить оффлайн аккаунт")
        print(f"{COLOR_YELLOW}3.{COLOR_RESET} Удалить аккаунт")
        print(f"{COLOR_YELLOW}4.{COLOR_RESET} Выбрать текущий аккаунт")
        print(f"{COLOR_YELLOW}5.{COLOR_RESET} Назад")
        
        choice = input(f"{COLOR_YELLOW}Выберите: {COLOR_RESET}")
        
        if choice == '1':
            selected_idx = scroll_list.navigate()
            if selected_idx is not None:
                selected_acc = accounts[selected_idx]
                print(f"\n{COLOR_CYAN}Выбран аккаунт:{COLOR_RESET}")
                print(f"  {COLOR_GREEN}Имя:{COLOR_RESET} {selected_acc['username']}")
                print(f"  {COLOR_GREEN}Тип:{COLOR_RESET} {selected_acc['type']}")
                print(f"  {COLOR_GREEN}ID:{COLOR_RESET} {selected_acc['id']}")
                print(f"  {COLOR_GREEN}Создан:{COLOR_RESET} {selected_acc['created_at']}")
        
        elif choice == '2':
            username = input("Введите имя пользователя: ")
            if username:
                account = add_offline_account(username)
                print(f"{COLOR_GREEN}Аккаунт '{username}' добавлен с ID {account['id']}!{COLOR_RESET}")
        
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
        
        version_list = [f"{v['id']} ({v['type']})" for v in filtered_versions]
        scroll_list = ScrollableList(version_list[::-1], page_size=15)
        
        type_names = {
            "alpha": "АЛЬФА ВЕРСИИ",
            "beta": "БЕТА ВЕРСИИ",
            "snapshot": "СНАПШОТЫ",
            "release": "РЕЛИЗНЫЕ ВЕРСИИ"
        }
        
        print(f"{COLOR_CYAN}{type_names[version_type]}{COLOR_RESET}")
        
        selected_idx = scroll_list.navigate()
        if selected_idx is not None:
            selected_version = filtered_versions[len(filtered_versions)-1-selected_idx]['id']
            print(f"\n{COLOR_GREEN}Выбрана версия: {selected_version}{COLOR_RESET}")
            
            if input_yes_no("Установить эту версию? (да/нет): "):
                install_version(selected_version)
    
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения списка версий: {e}{COLOR_RESET}")

def get_minecraft_dir_for_version(version):
    config = load_config()
    if config.get("separate_version_dirs", False):
        return str(Path.home() / f".minecraft_{version}")
    return MINECRAFT_DIR

def install_version(version):
    print(f"{COLOR_CYAN}Установка версии {version}...{COLOR_RESET}")
    
    try:
        minecraft_dir = get_minecraft_dir_for_version(version)
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_dir)
        
        config = load_config()
        config["selected_version"] = version
        save_config(config)
        
        print(f"{COLOR_GREEN}Версия {version} успешно установлена!{COLOR_RESET}")
        
    except Exception as e:
        print(f"{COLOR_RED}Ошибка установки: {e}{COLOR_RESET}")

def set_java_args():
    config = load_config()
    current_args = config.get("java_args", "-Xmx2G -Xms1G")
    
    print(f"\n{COLOR_CYAN}Текущие аргументы Java: {current_args}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Примеры:{COLOR_RESET}")
    print(f"{COLOR_GREEN}  -Xmx4G -Xms2G{COLOR_RESET} - 4GB максимум, 2GB минимум")
    print(f"{COLOR_GREEN}  -Xmx8G -Xms4G -XX:+UseG1GC{COLOR_RESET} - с оптимизацией G1GC")
    
    new_args = input(f"\n{COLOR_YELLOW}Введите новые аргументы (Enter для отмены): {COLOR_RESET}")
    
    if new_args:
        config["java_args"] = new_args
        save_config(config)
        print(f"{COLOR_GREEN}Аргументы обновлены!{COLOR_RESET}")

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
    
    new_args = re.sub(r"-Xmx\d+G", f"-Xmx{gb}G", current_args)
    new_args = re.sub(r"-Xms\d+G", f"-Xms{gb}G", new_args)
    
    if "-Xmx" not in new_args:
        new_args = f"-Xmx{gb}G -Xms{gb}G " + new_args
    
    config["java_args"] = new_args.strip()
    save_config(config)
    print(f"{COLOR_GREEN}Память установлена на {gb}GB{COLOR_RESET}")

keyboard_listener_running = False
minecraft_process = None

def keyboard_listener():
    global keyboard_listener_running, minecraft_process
    import keyboard
    
    print(f"{COLOR_MAGENTA}Слушатель клавиатуры запущен. Нажмите Alt+Shift для освобождения консоли{COLOR_RESET}")
    
    while keyboard_listener_running:
        if keyboard.is_pressed('alt+shift'):
            if minecraft_process and minecraft_process.poll() is None:
                print(f"{COLOR_RED}Завершение Minecraft...{COLOR_RESET}")
                minecraft_process.terminate()
                minecraft_process.wait()
                print(f"{COLOR_GREEN}Minecraft закрыт{COLOR_RESET}")
                minecraft_process = None
        time.sleep(0.1)

def launch_minecraft():
    global keyboard_listener_running, minecraft_process
    
    config = load_config()
    
    if not config.get("selected_version"):
        print(f"{COLOR_RED}Сначала установите версию Minecraft!{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Используйте команду 'установить' для выбора версии{COLOR_RESET}")
        return
    
    accounts = load_accounts()
    current_account_id = config.get("current_account")
    
    if not current_account_id or not any(a["id"] == current_account_id for a in accounts):
        print(f"{COLOR_RED}Сначала настройте аккаунт!{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Используйте команду 'акк' для управления аккаунтами{COLOR_RESET}")
        return
    
    account = next((a for a in accounts if a["id"] == current_account_id), None)
    if not account:
        print(f"{COLOR_RED}Аккаунт не найден!{COLOR_RESET}")
        return
    
    version = config["selected_version"]
    username = account["username"]
    minecraft_dir = get_minecraft_dir_for_version(version)
    
    print(f"{COLOR_CYAN}ЗАПУСК MINECRAFT{COLOR_RESET}")
    print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    print(f"{COLOR_GREEN}Версия:{COLOR_RESET} {version}")
    print(f"{COLOR_GREEN}Аккаунт:{COLOR_RESET} {username}")
    print(f"{COLOR_GREEN}Память:{COLOR_RESET} {config.get('java_args', '')[5:11]}")
    print(f"{COLOR_GREEN}Папка:{COLOR_RESET} {minecraft_dir}")
    print(f"{COLOR_MAGENTA}Для закрытия нажмите Alt+Shift в любой момент{COLOR_RESET}")
    print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    
    options = {
        'username': username,
        'uuid': '',
        'token': ''
    }
    
    print(f"{COLOR_CYAN}Подготовка к запуску...{COLOR_RESET}")
    
    try:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
            version, minecraft_dir, options
        )
        
        java_args = config.get("java_args", "").split()
        
        java_executable = 'java'
        if config.get("java_path"):
            java_executable = config["java_path"]
        
        minecraft_command = [java_executable] + java_args + minecraft_command[1:]
        
        print(f"{COLOR_GREEN}Запуск Minecraft...{COLOR_RESET}")
        
        minecraft_process = subprocess.Popen(minecraft_command)
        
        keyboard_listener_running = True
        listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
        listener_thread.start()
        
        minecraft_process.wait()
        
        keyboard_listener_running = False
        listener_thread.join(timeout=1)
        
        print(f"{COLOR_GREEN}Minecraft завершил работу{COLOR_RESET}")
        
    except Exception as e:
        keyboard_listener_running = False
        print(f"{COLOR_RED}Ошибка запуска: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Проверьте установку Java и наличие файлов игры{COLOR_RESET}")

def show_info():
    print(f"{COLOR_CYAN}Последние новости Minecraft{COLOR_RESET}")
    print(f"{COLOR_BLUE}- https://t.me/nerkinboat{COLOR_RESET}")
    print(f"{COLOR_BLUE}- https://www.youtube.com/@Nerkin/{COLOR_RESET}")
    print(f"{COLOR_CYAN}- Реклама:{COLOR_RESET}")
    print(f"{COLOR_BLUE}- https://t.me/minecraft_cubach Айпи: cubach.com{COLOR_RESET}")
    print(f"{COLOR_CYAN}- Сервер ванилла+ (ванилла с плагинами) Есть боссы, напитки, кастомные вещи, дружелюбное комьюнити.{COLOR_RESET}")
    print(f"{COLOR_BLUE}- https://t.me/playdacha Айпи: playdacha.ru{COLOR_RESET}")
    print(f"{COLOR_CYAN}- Ванильнный сервер майнкрафт. Есть приваты и команда /home. Мале нькое и дружелюбное комьюнити.{COLOR_RESET}")

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
                if os.path.exists(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, MINECRAFT_DIR)
                            zipf.write(file_path, arcname)
                            total_files += 1
        
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
            subprocess.run(["open", MINECRAFT_DIR])
        else:
            subprocess.run(["xdg-open", MINECRAFT_DIR])
        print(f"{COLOR_GREEN}Папка Minecraft открыта: {MINECRAFT_DIR}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия папки: {e}{COLOR_RESET}")

def open_folder(folder_name):
    folder_path = os.path.join(MINECRAFT_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"{COLOR_YELLOW}Папка {folder_name} не существует.{COLOR_RESET}")
        if input_yes_no("Создать папку? (да/нет): "):
            os.makedirs(folder_path)
            print(f"{COLOR_GREEN}Папка создана: {folder_path}{COLOR_RESET}")
        else:
            return
    
    try:
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder_path])
        else:
            subprocess.run(["xdg-open", folder_path])
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
    
    print(f"\n{COLOR_CYAN}Текущий путь к Java: {current_path}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Примеры:{COLOR_RESET}")
    print(f"{COLOR_GREEN}  C:\\Program Files\\Java\\jdk-17\\bin\\java.exe{COLOR_RESET} - Windows")
    print(f"{COLOR_GREEN}  /usr/lib/jvm/java-17-openjdk/bin/java{COLOR_RESET} - Linux")
    
    new_path = input(f"\n{COLOR_YELLOW}Введите новый путь к Java (Enter для сброса): {COLOR_RESET}")
    
    if new_path:
        config["java_path"] = new_path
        save_config(config)
        print(f"{COLOR_GREEN}Путь к Java обновлен!{COLOR_RESET}")
    elif new_path == "" and current_path != "Не установлен":
        config["java_path"] = None
        save_config(config)
        print(f"{COLOR_GREEN}Путь к Java сброшен, будет использована системная Java.{COLOR_RESET}")

def toggle_separate_dirs():
    config = load_config()
    current = config.get("separate_version_dirs", False)
    config["separate_version_dirs"] = not current
    
    status = "включено" if config["separate_version_dirs"] else "выключено"
    print(f"{COLOR_CYAN}Отдельные папки для версий: {COLOR_GREEN}{status}{COLOR_RESET}")
    
    if config["separate_version_dirs"]:
        print(f"{COLOR_YELLOW}Теперь каждая версия Minecraft будет установлена в отдельную папку.{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Например: .minecraft_1.20.1, .minecraft_1.19.4 и т.д.{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}Все версии Minecraft будут использовать одну папку .minecraft{COLOR_RESET}")
    
    save_config(config)

def main():
    print_banner()
    
    config = load_config()
    
    print(f"{COLOR_MAGENTA}Не знаете команды? Введите '{COLOR_GREEN}помощь{COLOR_MAGENTA}' для списка команд{COLOR_RESET}")
    
    while True:
        try:
            user_input = input(f"\n{COLOR_CYAN}cobalt>{COLOR_RESET} ").strip()
            
            if not user_input:
                continue
            
            parts = user_input.split()
            cmd = parts[0].lower()
            
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
            
            elif cmd == 'установить' and len(parts) > 1:
                install_version(parts[1])
            
            elif cmd == 'запуск' or cmd == 'launch':
                launch_minecraft()
            
            elif cmd == 'арг' or cmd == 'args':
                set_java_args()
            
            elif cmd == 'память' and len(parts) > 1:
                set_memory(parts[1])
            
            elif cmd == 'моды':
                open_folder("mods")
            
            elif cmd == 'ресурспак':
                open_folder("resourcepacks")
            
            elif cmd == 'миры':
                open_folder("saves")
            
            elif cmd == 'конфиги':
                open_folder("config")
            
            elif cmd == 'схемы':
                open_folder("schematics")
            
            elif cmd == 'инфо':
                show_info()
            
            elif cmd == 'заметка' and len(parts) > 1:
                note_text = ' '.join(parts[1:])
                with open(NOTES_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note_text}\n")
                print(f"{COLOR_GREEN}Заметка добавлена!{COLOR_RESET}")
            
            elif cmd == 'заметки' or cmd == 'notes':
                if os.path.exists(NOTES_FILE):
                    print(f"{COLOR_CYAN}ЗАМЕТКИ{COLOR_RESET}")
                    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(f"{COLOR_YELLOW}Заметок пока нет{COLOR_RESET}")
            
            elif cmd == 'бэкап' or cmd == 'backup':
                create_backup()
            
            elif cmd == 'папка' or cmd == 'folder':
                open_minecraft_folder()
            
            elif cmd == 'лог' or cmd == 'log':
                copy_latest_log()
            
            elif cmd == 'джава':
                set_java_path()
            
            elif user_input.lower() == 'отдельные папки':
                toggle_separate_dirs()
            
            elif cmd == 'выход' or cmd == 'exit' or cmd == 'quit':
                print(f"{COLOR_CYAN}До свидания!{COLOR_RESET}")
                break
            
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