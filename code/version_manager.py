import os
import json
import shlex
import subprocess
import threading
import requests
import re
import zipfile
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from constants import BASE_MINECRAFT_DIR, LAUNCHER_DATA_DIR, COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN, COLOR_MAGENTA, COLOR_BLUE, COLOR_RESET, minecraft_processes
from utils import download_file, ProgressCallback, input_yes_no
from config_manager import load_config, save_config
from java_manager import ensure_java_for_version, find_suitable_java, get_java_version, get_required_java_version
from accounts import load_accounts, get_account_by_id

VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
_version_cache = None

def sanitize_version_name(version):
    return version.replace(' ', '_').replace('/', '_').replace('\\', '_')

def get_minecraft_dir_for_version(version):
    safe_name = sanitize_version_name(version)
    version_dir = f"{BASE_MINECRAFT_DIR}_{safe_name}"
    os.makedirs(version_dir, exist_ok=True)
    return version_dir

def get_installed_versions():
    installed = []
    for item in os.listdir(LAUNCHER_DATA_DIR):
        if item.startswith("minecraft_"):
            version_dir = os.path.join(LAUNCHER_DATA_DIR, item)
            versions_subdir = os.path.join(version_dir, "versions")
            if os.path.exists(versions_subdir):
                for v in os.listdir(versions_subdir):
                    v_path = os.path.join(versions_subdir, v)
                    if os.path.isdir(v_path):
                        json_file = os.path.join(v_path, f"{v}.json")
                        jar_file = os.path.join(v_path, f"{v}.jar")
                        if os.path.exists(json_file) and os.path.exists(jar_file):
                            installed.append(v)
    return sorted(set(installed), reverse=True)

def get_version_manifest():
    global _version_cache
    if _version_cache is not None:
        return _version_cache
    try:
        resp = requests.get(VERSION_MANIFEST_URL, timeout=10)
        resp.raise_for_status()
        _version_cache = resp.json()
        return _version_cache
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения манифеста версий: {e}{COLOR_RESET}")
        return None

def get_available_versions():
    manifest = get_version_manifest()
    if not manifest:
        return []
    versions = []
    for v in manifest.get('versions', []):
        versions.append({
            'id': v['id'],
            'type': v['type']
        })
    return versions

def get_version_json(version_id, minecraft_dir):
    version_json_path = os.path.join(minecraft_dir, 'versions', version_id, f'{version_id}.json')
    if os.path.exists(version_json_path):
        with open(version_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    manifest = get_version_manifest()
    if not manifest:
        return None
    for v in manifest['versions']:
        if v['id'] == version_id:
            url = v['url']
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"{COLOR_RED}Ошибка скачивания version.json: {e}{COLOR_RESET}")
                return None
    print(f"{COLOR_RED}Версия {version_id} не найдена в манифесте{COLOR_RESET}")
    return None

def extract_natives(minecraft_dir, version_json):
    natives_dir = os.path.join(minecraft_dir, 'versions', version_json['id'], 'natives')
    os.makedirs(natives_dir, exist_ok=True)
    system = platform.system().lower()
    if system == 'windows':
        classifier = 'natives-windows'
    elif system == 'linux':
        classifier = 'natives-linux'
    elif system == 'darwin':
        classifier = 'natives-osx'
    else:
        classifier = None
    if not classifier:
        return
    libraries = version_json.get('libraries', [])
    for lib in libraries:
        classifiers = lib.get('downloads', {}).get('classifiers', {})
        if classifier in classifiers:
            nat_info = classifiers[classifier]
            lib_path = os.path.join(minecraft_dir, 'libraries', nat_info['path'])
            if os.path.exists(lib_path):
                try:
                    with zipfile.ZipFile(lib_path, 'r') as jar:
                        jar.extractall(natives_dir)
                except Exception as e:
                    print(f"{COLOR_YELLOW}Не удалось распаковать natives из {lib_path}: {e}{COLOR_RESET}")

def download_assets(version_json, minecraft_dir):
    asset_index = version_json.get('assetIndex', {})
    if not asset_index or 'url' not in asset_index:
        return
    assets_index_dir = os.path.join(minecraft_dir, 'assets', 'indexes')
    os.makedirs(assets_index_dir, exist_ok=True)
    index_id = asset_index['id']
    index_path = os.path.join(assets_index_dir, f'{index_id}.json')
    if not os.path.exists(index_path):
        print(f"{COLOR_YELLOW}Скачивание индекса ассетов {index_id}...{COLOR_RESET}")
        if not download_file(asset_index['url'], index_path, None):
            print(f"{COLOR_RED}Не удалось скачать индекс ассетов{COLOR_RESET}")
            return
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    objects = index_data.get('objects', {})
    total = len(objects)
    print(f"{COLOR_YELLOW}Скачивание ассетов (всего {total} файлов)...{COLOR_RESET}")
    for idx, (hash_path, info) in enumerate(objects.items(), 1):
        hash_val = info['hash']
        sub_folder = hash_val[:2]
        dest_dir = os.path.join(minecraft_dir, 'assets', 'objects', sub_folder)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, hash_val)
        if not os.path.exists(dest_file):
            url = f"https://resources.download.minecraft.net/{sub_folder}/{hash_val}"
            download_file(url, dest_file, None)
        if idx % 100 == 0 or idx == total:
            print(f"\r{COLOR_CYAN}Прогресс: {idx}/{total} ассетов{COLOR_RESET}", end="")
    print()

def install_minecraft_version(version_id, minecraft_dir, callback=None):
    print(f"{COLOR_CYAN}Установка ванильной версии {version_id}...{COLOR_RESET}")
    version_json = get_version_json(version_id, minecraft_dir)
    if not version_json:
        return False
    version_dir = os.path.join(minecraft_dir, 'versions', version_id)
    os.makedirs(version_dir, exist_ok=True)
    json_path = os.path.join(version_dir, f'{version_id}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(version_json, f, indent=2)
    downloads = version_json.get('downloads', {})
    client_info = downloads.get('client')
    if client_info:
        client_url = client_info['url']
        client_path = os.path.join(version_dir, f'{version_id}.jar')
        print(f"{COLOR_YELLOW}Скачивание клиента...{COLOR_RESET}")
        if not download_file(client_url, client_path, callback):
            return False
    libraries = version_json.get('libraries', [])
    total = len(libraries)
    for idx, lib in enumerate(libraries):
        if callback:
            callback({'current': idx + 1, 'total': total})
        downloads_lib = lib.get('downloads', {})
        artifact = downloads_lib.get('artifact')
        if artifact and 'url' in artifact:
            url = artifact['url']
            path = artifact['path']
            dest = os.path.join(minecraft_dir, 'libraries', path)
            if not os.path.exists(dest):
                download_file(url, dest, None)
        classifiers = downloads_lib.get('classifiers')
        if classifiers:
            for classifier_name, nat_info in classifiers.items():
                url = nat_info['url']
                path = nat_info['path']
                dest = os.path.join(minecraft_dir, 'libraries', path)
                if not os.path.exists(dest):
                    download_file(url, dest, None)
    download_assets(version_json, minecraft_dir)
    extract_natives(minecraft_dir, version_json)
    if callback:
        callback({'current': total, 'total': total})
    print(f"{COLOR_GREEN}Ванильная версия {version_id} установлена.{COLOR_RESET}")
    return True

def install_version_with_progress(version, loader_choice=None):
    minecraft_dir = get_minecraft_dir_for_version(version)
    ensure_java_for_version(version)
    progress = ProgressCallback()
    success = install_minecraft_version(version, minecraft_dir, progress)
    if not success:
        return
    config = load_config()
    config["selected_version"] = version
    print(f"{COLOR_GREEN}✓ Версия {version} успешно установлена!{COLOR_RESET}")
    save_config(config)

def install_version_interactive(version=None):
    if not version:
        version = input(f"{COLOR_YELLOW}Введите версию Minecraft: {COLOR_RESET}").strip()
        if not version:
            print(f"{COLOR_RED}Версия не указана{COLOR_RESET}")
            return
    install_version_with_progress(version, None)

def build_classpath(minecraft_dir, version_json):
    classpath = []
    version_id = version_json.get('id', '')
    client_jar = os.path.join(minecraft_dir, 'versions', version_id, f'{version_id}.jar')
    if os.path.exists(client_jar):
        classpath.append(client_jar)
    for lib in version_json.get('libraries', []):
        jar_path = None
        if 'downloads' in lib and 'artifact' in lib['downloads']:
            path = lib['downloads']['artifact']['path']
            jar_path = os.path.join(minecraft_dir, 'libraries', path)
        elif 'name' in lib:
            parts = lib['name'].split(':')
            if len(parts) >= 3:
                group, name, version = parts[0], parts[1], parts[2]
                group_path = group.replace('.', os.sep)
                jar_path = os.path.join(minecraft_dir, 'libraries', group_path, name, version, f'{name}-{version}.jar')
        if jar_path and os.path.exists(jar_path):
            classpath.append(jar_path)
    return os.pathsep.join(classpath)

def get_minecraft_command(version, minecraft_dir, options):
    version_json_path = os.path.join(minecraft_dir, 'versions', version, f'{version}.json')
    if not os.path.exists(version_json_path):
        raise Exception(f"Версия {version} не установлена")
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_json = json.load(f)
    main_class = version_json.get('mainClass', 'net.minecraft.client.main.Main')
    game_args = []
    jvm_args = []
    natives_dir = os.path.join(minecraft_dir, 'versions', version, 'natives')
    os.makedirs(natives_dir, exist_ok=True)
    arguments = version_json.get('arguments')
    if arguments:
        for arg in arguments.get('jvm', []):
            if isinstance(arg, dict):
                rules = arg.get('rules', [])
                allow = True
                for rule in rules:
                    if rule.get('action') == 'disallow' and 'os' in rule:
                        if rule['os'].get('name') == platform.system().lower():
                            allow = False
                    elif rule.get('action') == 'allow' and 'os' in rule:
                        if rule['os'].get('name') != platform.system().lower():
                            allow = False
                if allow:
                    value = arg.get('value')
                    if isinstance(value, list):
                        jvm_args.extend(value)
                    elif value:
                        jvm_args.append(value)
            else:
                jvm_args.append(arg)
        for arg in arguments.get('game', []):
            if isinstance(arg, dict):
                value = arg.get('value')
                if isinstance(value, list):
                    game_args.extend(value)
                elif value:
                    game_args.append(value)
            else:
                game_args.append(arg)
    else:
        game_args = shlex.split(version_json.get('minecraftArguments', ''))
        jvm_args = ['-Djava.library.path=${natives_directory}', '-cp', '${classpath}']
    classpath = build_classpath(minecraft_dir, version_json)
    if not classpath:
        client_jar = os.path.join(minecraft_dir, 'versions', version, f'{version}.jar')
        if os.path.exists(client_jar):
            classpath = client_jar
    has_cp = any(arg == '-cp' or arg == '--classpath' for arg in jvm_args)
    if not has_cp:
        jvm_args = ['-cp', classpath] + jvm_args
    def replace_placeholders(arg):
        return arg.replace('${version_name}', version) \
                  .replace('${game_directory}', minecraft_dir) \
                  .replace('${assets_root}', os.path.join(minecraft_dir, 'assets')) \
                  .replace('${assets_index_name}', version_json.get('assetIndex', {}).get('id', version)) \
                  .replace('${auth_uuid}', options.get('uuid', '00000000-0000-0000-0000-000000000000')) \
                  .replace('${auth_access_token}', options.get('token', '0')) \
                  .replace('${auth_player_name}', options.get('username', 'Player')) \
                  .replace('${user_type}', options.get('user_type', 'mojang')) \
                  .replace('${version_type}', version_json.get('type', 'release')) \
                  .replace('${natives_directory}', natives_dir) \
                  .replace('${library_directory}', os.path.join(minecraft_dir, 'libraries')) \
                  .replace('${classpath}', classpath) \
                  .replace('${classpath_separator}', os.pathsep) \
                  .replace('${clientid}', options.get('clientid', '0')) \
                  .replace('${auth_xuid}', options.get('xuid', ''))
    game_args = [replace_placeholders(arg) for arg in game_args]
    jvm_args = [replace_placeholders(arg) for arg in jvm_args]
    command = jvm_args + [main_class] + game_args
    command = [arg for arg in command if arg]
    return command

def ensure_natives(version, minecraft_dir):
    version_json_path = os.path.join(minecraft_dir, 'versions', version, f'{version}.json')
    if not os.path.exists(version_json_path):
        return
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_json = json.load(f)
    natives_dir = os.path.join(minecraft_dir, 'versions', version, 'natives')
    if os.path.exists(natives_dir) and any(os.scandir(natives_dir)):
        return
    print(f"{COLOR_YELLOW}Извлечение нативных библиотек для {version}...{COLOR_RESET}")
    extract_natives(minecraft_dir, version_json)

def launch_minecraft_thread(version, java_path, java_args_str, username, minecraft_dir, account_type, access_token=None):
    try:
        ensure_natives(version, minecraft_dir)
        options = {'username': username}
        if account_type == 'ely' and access_token:
            print(f"{COLOR_YELLOW}Авторизация Ely.by: требует доработки.{COLOR_RESET}")
        minecraft_command = get_minecraft_command(version, minecraft_dir, options)
        java_args = shlex.split(java_args_str) if java_args_str else []
        java_executable = java_path if java_path else ('java' if platform.system() != "Linux" else shutil.which("java") or "java")
        full_command = [java_executable] + java_args + minecraft_command
        print(f"{COLOR_CYAN}Команда запуска: {' '.join(full_command)}{COLOR_RESET}")
        proc = subprocess.Popen(
            full_command,
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
        try:
            import keyboard
            KEYBOARD_AVAILABLE = True
        except ImportError:
            KEYBOARD_AVAILABLE = False
        if KEYBOARD_AVAILABLE:
            def monitor_hotkey(proc, pid):
                try:
                    keyboard.wait('alt+shift')
                    if proc.poll() is None:
                        print(f"\n{COLOR_YELLOW}Горячая клавиша Alt+Shift нажата, завершение Minecraft (PID {pid})...{COLOR_RESET}")
                        proc.terminate()
                        proc.wait()
                except:
                    pass
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
            required = get_required_java_version(version.split('-')[0])
            if java_version < required:
                print(f"{COLOR_RED}ВНИМАНИЕ: Для Minecraft {version} требуется Java {required} или выше!{COLOR_RESET}")
                print(f"{COLOR_RED}Текущая Java: {java_version}{COLOR_RESET}")
                print(f"{COLOR_YELLOW}Вы можете установить Java {required} командой: {COLOR_GREEN}установить джава{COLOR_RESET}")
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
    print(f"{COLOR_GREEN}Аргументы JVM:{COLOR_RESET} {java_args_str}")
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

def list_versions_by_type(version_type):
    print(f"{COLOR_CYAN}Получение списка версий...{COLOR_RESET}")
    try:
        versions = get_available_versions()
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
        from utils import ScrollableList
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