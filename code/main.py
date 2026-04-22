import os
import sys
import re
import shutil
import webbrowser
import signal
import threading
import time
import zipfile
import subprocess
import platform
import json
import requests
from pathlib import Path
from datetime import datetime

from constants import LAUNCHER_DATA_DIR, BASE_MINECRAFT_DIR, JAVA_DIR, COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN, COLOR_BLUE, COLOR_MAGENTA, COLOR_RESET, plugin_commands, NOTES_FILE, CONFIG_FILE
from utils import input_yes_no, ScrollableList, download_file
from config_manager import load_config, save_config, set_java_args, set_java_args_for_version, set_memory
from accounts import load_accounts, add_offline_account, get_account_by_id, delete_account, rename_account
from java_manager import set_java_path, install_java_version, ensure_java_for_version, set_java_path_for_version, install_java_interactive, find_java_executable_in_dir, get_java_version
from version_manager import (
    get_installed_versions, get_available_versions, install_version_with_progress, install_version_interactive,
    launch_minecraft, delayed_launch, list_versions_by_type, get_minecraft_dir_for_version
)
from mods_manager import (
    manage_mods_menu, install_sodium, install_embeddium, install_modmenu,
    install_journeymap, install_xaeros_minimap, install_vulkanmod, install_iris,
    install_fabric_api, install_quilted_fabric_api, install_mod_by_name, open_alt_mod_site
)
from plugin_api import load_plugins, manage_plugins
from ui import print_banner, show_quick_info, print_help
import nbtlib

def get_selected_version_dir():
    config = load_config()
    version = config.get("selected_version")
    if not version:
        print(f"{COLOR_RED}Не выбрана версия. Используйте 'выбрать версию <имя>'.{COLOR_RESET}")
        return None
    from version_manager import get_minecraft_dir_for_version
    return get_minecraft_dir_for_version(version)

def get_selected_version_dir():
    config = load_config()
    version = config.get("selected_version")
    if not version:
        print(f"{COLOR_RED}Не выбрана версия. Используйте 'выбрать версию <имя>' или установите версию.{COLOR_RESET}")
        return None
    return get_minecraft_dir_for_version(version)

def open_folder(folder_name, minecraft_dir):
    folder_path = os.path.join(minecraft_dir, folder_name)
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

def copy_latest_log(minecraft_dir):
    logs_dir = os.path.join(minecraft_dir, "logs")
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

def copy_crash_reports(minecraft_dir):
    crashes_dir = os.path.join(minecraft_dir, "crash-reports")
    if not os.path.exists(crashes_dir):
        print(f"{COLOR_YELLOW}Папка crash-reports не найдена{COLOR_RESET}")
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

def create_backup(minecraft_dir):
    desktop = Path.home() / "Desktop"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = desktop / f"minecraft_backup_{timestamp}.zip"
    folders_to_backup = ["saves", "resourcepacks", "config", "shaderpacks", "schematics", "mods"]
    print(f"{COLOR_CYAN}Создание резервной копии для {minecraft_dir}...{COLOR_RESET}")
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_files = 0
            for folder in folders_to_backup:
                folder_path = os.path.join(minecraft_dir, folder)
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, minecraft_dir)
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

def open_minecraft_folder(version=None):
    if version:
        folder = get_minecraft_dir_for_version(version)
    else:
        selected = load_config().get("selected_version")
        if not selected:
            print(f"{COLOR_RED}Не выбрана версия. Используйте 'выбрать версию <имя>'.{COLOR_RESET}")
            return
        folder = get_minecraft_dir_for_version(selected)
    try:
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)
        print(f"{COLOR_GREEN}Папка Minecraft открыта: {folder}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия папки: {e}{COLOR_RESET}")

def list_java_versions():
    if not os.path.exists(JAVA_DIR):
        print(f"{COLOR_YELLOW}Папка Java не найдена{COLOR_RESET}")
        return
    versions = []
    for item in os.listdir(JAVA_DIR):
        java_path = os.path.join(JAVA_DIR, item)
        if os.path.isdir(java_path) and item.startswith("java_"):
            exe = find_java_executable_in_dir(java_path)
            if exe:
                ver_num = get_java_version(exe)
                versions.append((item, exe, ver_num))
    if not versions:
        print(f"{COLOR_YELLOW}Нет установленных версий Java. Используйте 'установить джава'.{COLOR_RESET}")
        return
    print(f"{COLOR_CYAN}Установленные версии Java:{COLOR_RESET}")
    for i, (name, path, ver) in enumerate(versions, 1):
        ver_str = f" (Java {ver})" if ver else ""
        print(f"  {COLOR_YELLOW}{i}.{COLOR_RESET} {name}{ver_str} -> {path}")
    print(f"{COLOR_BLUE}──────────────────────────────────{COLOR_RESET}")
    choice = input(f"{COLOR_YELLOW}Выберите номер, чтобы сделать версией по умолчанию (или Enter для отмены): {COLOR_RESET}").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(versions):
            config = load_config()
            config["java_path"] = versions[idx][1]
            config["java_version"] = versions[idx][0].replace("java_", "")
            save_config(config)
            print(f"{COLOR_GREEN}Java по умолчанию установлена: {versions[idx][1]}{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")

def install_modloader_from_github():
    url = "https://api.github.com/repos/m1r0tv0rets/Cobalt_Launcher_Nano/releases/tags/modloader_minecraft"
    try:
        print(f"{COLOR_CYAN}Загрузка списка доступных сборок...{COLOR_RESET}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        release = resp.json()
        assets = release.get('assets', [])
        if not assets:
            print(f"{COLOR_RED}В релизе нет файлов для скачивания{COLOR_RESET}")
            return
        print(f"{COLOR_CYAN}Доступные сборки модлоадеров:{COLOR_RESET}")
        for i, asset in enumerate(assets, 1):
            name = asset['name']
            size_mb = asset['size'] / (1024 * 1024)
            print(f"  {COLOR_YELLOW}{i}.{COLOR_RESET} {name} ({size_mb:.1f} MB)")
        choice = input(f"{COLOR_YELLOW}Выберите номер для скачивания и установки (или 'в' для отмены): {COLOR_RESET}").strip()
        if choice.lower() == 'в':
            return
        if not choice.isdigit():
            print(f"{COLOR_RED}Неверный ввод{COLOR_RESET}")
            return
        idx = int(choice) - 1
        if idx < 0 or idx >= len(assets):
            print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
            return
        asset = assets[idx]
        download_url = asset['browser_download_url']
        zip_name = asset['name']
        zip_path = os.path.join(LAUNCHER_DATA_DIR, zip_name)

        def progress_callback(current, total):
            if total > 0:
                percent = (current / total) * 100
                bar_length = 30
                filled = int(bar_length * current / total)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}% ({current/1024/1024:.1f} MB / {total/1024/1024:.1f} MB){COLOR_RESET}", end="")

        print(f"{COLOR_CYAN}Скачивание {zip_name}...{COLOR_RESET}")
        if not download_file(download_url, zip_path, progress_callback):
            print(f"\n{COLOR_RED}Ошибка скачивания{COLOR_RESET}")
            return
        print(f"\n{COLOR_GREEN}Скачивание завершено.{COLOR_RESET}")

        version_name = os.path.splitext(zip_name)[0]
        target_version_dir = os.path.join(LAUNCHER_DATA_DIR, f"minecraft_{version_name}")
        os.makedirs(target_version_dir, exist_ok=True)

        print(f"{COLOR_CYAN}Распаковка архива...{COLOR_RESET}")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = zf.namelist()
            if 'versions/' in members or any(m.startswith('versions/') for m in members):
                zf.extractall(target_version_dir)
                print(f"{COLOR_GREEN}Установлена версия {version_name} в {target_version_dir}{COLOR_RESET}")
            else:
                root_dirs = set(m.split('/')[0] for m in members if '/' in m)
                if len(root_dirs) == 1 and root_dirs.pop() == version_name:
                    zf.extractall(target_version_dir)
                    print(f"{COLOR_GREEN}Установлена версия {version_name} в {target_version_dir}{COLOR_RESET}")
                else:
                    version_subdir = os.path.join(target_version_dir, 'versions', version_name)
                    os.makedirs(version_subdir, exist_ok=True)
                    for member in members:
                        if member.endswith('/'):
                            continue
                        target_path = os.path.join(version_subdir, member)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(member) as src, open(target_path, 'wb') as dst:
                            dst.write(src.read())
                    print(f"{COLOR_GREEN}Установлена версия {version_name} в {version_subdir}{COLOR_RESET}")

        os.remove(zip_path)
        print(f"{COLOR_GREEN}Готово! Версия '{version_name}' добавлена. Используйте 'установленные' для проверки.{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка: {e}{COLOR_RESET}")

def add_server_to_minecraft(server_name, server_ip, minecraft_dir):
    if not nbtlib:
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
        mc_dir = get_selected_version_dir()
        if not mc_dir:
            mc_dir = BASE_MINECRAFT_DIR
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
        url = input("Введите URL (например, https://ya.ru): ").strip()
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
            print(f"{COLOR_YELLOW}Авторизация Ely.by пока не реализована. Используйте оффлайн аккаунт.{COLOR_RESET}")
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
        print(f"{COLOR_YELLOW}2.{COLOR_RESET} Переименовать аккаунт")
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
            acc_id = input("Введите ID аккаунта для переименования: ")
            if acc_id.isdigit():
                acc = get_account_by_id(int(acc_id))
                if acc:
                    new_name = input(f"Введите новое имя для {acc['username']}: ")
                    if new_name:
                        rename_account(int(acc_id), new_name)
                else:
                    print(f"{COLOR_RED}Аккаунт не найден!{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Неверный ID{COLOR_RESET}")
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

def signal_handler(sig, frame):
    global minecraft_processes
    for pid, proc in minecraft_processes:
        if proc.poll() is None:
            print(f"{COLOR_YELLOW}Завершение Minecraft (PID {pid})...{COLOR_RESET}")
            proc.terminate()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    load_plugins()
    print_banner()
    show_quick_info()
    config = load_config()
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
            elif cmd == 'установленные' or cmd == 'installed':
                installed = get_installed_versions()
                if not installed:
                    print(f"{COLOR_YELLOW}Нет установленных версий. Используйте 'установить <версия>' для установки.{COLOR_RESET}")
                else:
                    print(f"{COLOR_CYAN}Установленные версии Minecraft:{COLOR_RESET}")
                    for i, ver in enumerate(installed, 1):
                        print(f"  {COLOR_YELLOW}{i}.{COLOR_RESET} {ver}")
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
                install_java_interactive()
            elif cmd == 'установить' and len(args) == 0:
                install_version_interactive()
            elif cmd == 'установить' and len(args) == 1:
                install_version_interactive(args[0])
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
            elif cmd == 'папка' or cmd == 'folder':
                if len(args) == 0:
                    open_minecraft_folder()
                elif args[0] == 'модов':
                    version_dir = get_selected_version_dir()
                    if version_dir:
                        open_folder("mods", version_dir)
                elif args[0] == 'версии':
                    if len(args) > 1:
                        open_minecraft_folder(args[1])
                    else:
                        print(f"{COLOR_RED}Укажите версию. Например: 'папка версии 1.12.2'{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Неизвестная подкоманда. Используйте: 'папка', 'папка модов', 'папка версии <версия>'.{COLOR_RESET}")
            elif cmd == 'моды':
                manage_mods_menu()
            elif cmd == 'плагины':
                manage_plugins()
            elif cmd == 'ресурспак':
                version_dir = get_selected_version_dir()
                if version_dir:
                    open_folder("resourcepacks", version_dir)
            elif cmd == 'миры':
                version_dir = get_selected_version_dir()
                if version_dir:
                    open_folder("saves", version_dir)
            elif cmd == 'скриншоты':
                version_dir = get_selected_version_dir()
                if version_dir:
                    open_folder("screenshots", version_dir)
            elif cmd == 'конфиги':
                version_dir = get_selected_version_dir()
                if version_dir:
                    open_folder("config", version_dir)
            elif cmd == 'схемы':
                version_dir = get_selected_version_dir()
                if version_dir:
                    open_folder("schematics", version_dir)
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
                version_dir = get_selected_version_dir()
                if version_dir:
                    create_backup(version_dir)
            elif cmd == 'конфиг лаунчера' or (cmd == 'конфиг' and len(args) > 0 and args[0] == 'лаунчера'):
                copy_launcher_config()
            elif cmd == 'лог' or cmd == 'log':
                version_dir = get_selected_version_dir()
                if version_dir:
                    copy_latest_log(version_dir)
            elif cmd == 'краш' or cmd == 'crash':
                version_dir = get_selected_version_dir()
                if version_dir:
                    copy_crash_reports(version_dir)
            elif cmd == 'джава':
                set_java_path()
            elif cmd == 'версии джава':
                list_java_versions()
            elif cmd == 'модлоадеры':
                install_modloader_from_github()
            elif cmd == 'выбрать' or cmd == 'версию' or cmd == 'use':
                if len(args) == 0:
                    print(f"{COLOR_YELLOW}Текущая выбранная версия: {config.get('selected_version', 'не выбрана')}{COLOR_RESET}")
                else:
                    if args[0].isdigit():
                        idx = int(args[0]) - 1
                        installed = get_installed_versions()
                        if 0 <= idx < len(installed):
                            version_name = installed[idx]
                            config["selected_version"] = version_name
                            save_config(config)
                            print(f"{COLOR_GREEN}Выбрана версия: {version_name}{COLOR_RESET}")
                        else:
                            print(f"{COLOR_RED}Неверный номер версии{COLOR_RESET}")
                    else:
                        version_name = ' '.join(args)
                        installed = get_installed_versions()
                        if version_name in installed:
                            config["selected_version"] = version_name
                            save_config(config)
                            print(f"{COLOR_GREEN}Выбрана версия: {version_name}{COLOR_RESET}")
                        else:
                            print(f"{COLOR_RED}Версия '{version_name}' не найдена. Используйте 'установленные' для просмотра.{COLOR_RESET}")
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
            elif cmd == 'sodium':
                install_sodium()
            elif cmd == 'embeddium':
                install_embeddium()
            elif cmd == 'modmenu':
                install_modmenu()
            elif cmd == 'journeymap':
                install_journeymap()
            elif cmd == 'xaeros':
                install_xaeros_minimap()
            elif cmd == 'vulkanmod':
                install_vulkanmod()
            elif cmd == 'iris':
                install_iris()
            elif cmd == 'fabricapi':
                install_fabric_api()
            elif cmd == 'quiltapi':
                install_quilted_fabric_api()
            elif cmd == 'установить' and len(args) >= 2 and args[0] == 'мод':
                mod_name = ' '.join(args[1:])
                install_mod_by_name(mod_name)
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