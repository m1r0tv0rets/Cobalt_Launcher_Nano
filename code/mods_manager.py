import os
import json
import re
import webbrowser
import requests
from datetime import datetime
from typing import List, Dict
from constants import COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN, COLOR_BLUE, COLOR_RESET, MODS_FAVORITES_FILE
from utils import download_with_retry, input_yes_no
from config_manager import load_config
from version_manager import get_minecraft_dir_for_version

def get_selected_minecraft_version():
    config = load_config()
    selected_version = config.get("selected_version")
    if not selected_version:
        return None
    match = re.search(r'(\d+\.\d+(?:\.\d+)?)', selected_version)
    if match:
        return match.group(1)
    return selected_version

def install_mod_auto(slug, display_name, loader=None):
    config = load_config()
    selected_version_name = config.get("selected_version")
    if not selected_version_name:
        print(f"{COLOR_RED}Сначала выберите версию Minecraft (команда 'выбрать версию <имя>').{COLOR_RESET}")
        return
    mc_version = get_selected_minecraft_version()
    if not mc_version:
        print(f"{COLOR_RED}Не удалось определить версию Minecraft из '{selected_version_name}'.{COLOR_RESET}")
        return

    mc_dir = get_minecraft_dir_for_version(selected_version_name)
    mods_dir = os.path.join(mc_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    api_url = f"https://api.modrinth.com/v2/project/{slug}/version"
    headers = {"User-Agent": "CobaltLauncher/1.0"}
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        versions = resp.json()
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения версий мода {display_name}: {e}{COLOR_RESET}")
        return

    versions.sort(key=lambda v: v.get('date_published', ''), reverse=True)

    selected_version = None
    for ver in versions:
        game_versions = ver.get('game_versions', [])
        loaders = ver.get('loaders', [])
        if mc_version not in game_versions:
            continue
        if loader and loader.lower() not in [l.lower() for l in loaders]:
            continue
        selected_version = ver
        break

    if not selected_version:
        print(f"{COLOR_RED}Не найдена подходящая версия мода {display_name} для Minecraft {mc_version}{COLOR_RESET}")
        return

    jar_file = None
    for file in selected_version.get('files', []):
        if file.get('filename', '').endswith('.jar'):
            jar_file = file
            break
    if not jar_file:
        print(f"{COLOR_RED}Не найден .jar файл для мода {display_name}{COLOR_RESET}")
        return

    download_url = jar_file.get('url')
    filename = jar_file.get('filename', f"{slug}.jar")
    filepath = os.path.join(mods_dir, filename)

    def progress(current, total):
        if total > 0:
            percent = (current / total) * 100
            bar = '█' * int(percent // 2) + '░' * (50 - int(percent // 2))
            print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}%{COLOR_RESET}", end="")

    print(f"{COLOR_CYAN}Установка {display_name}...{COLOR_RESET}")
    success = download_with_retry(download_url, filepath, progress, max_retries=3)
    if success:
        print(f"\n{COLOR_GREEN}✓ {display_name} установлен в папку модов версии {selected_version_name}.{COLOR_RESET}")
    else:
        print(f"\n{COLOR_RED}Не удалось скачать {display_name}{COLOR_RESET}")

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

def download_mod(mod_info: Dict):
    print(f"{COLOR_CYAN}Скачивание мода '{mod_info.get('title')}'...{COLOR_RESET}")
    try:
        mod_id = mod_info.get('id')
        versions = get_mod_versions(mod_id)
        if not versions:
            print(f"{COLOR_RED}Нет доступных версий для скачивания{COLOR_RESET}")
            return

        print(f"{COLOR_GREEN}Доступные версии мода:{COLOR_RESET}")
        for i, ver in enumerate(versions[:20], 1):
            loaders = ', '.join(ver.get('loaders', []))
            mc_versions = ', '.join(ver.get('game_versions', [])[:3])
            if len(ver.get('game_versions', [])) > 3:
                mc_versions += '...'
            print(f"{COLOR_YELLOW}{i}.{COLOR_RESET} {ver.get('version_number')} [Загрузчики: {loaders}] [MC: {mc_versions}]")
        choice = input(f"{COLOR_YELLOW}Выберите номер версии (или 'в' для отмены): {COLOR_RESET}")
        if choice.lower() == 'в':
            return
        if not choice.isdigit():
            print(f"{COLOR_RED}Неверный ввод{COLOR_RESET}")
            return
        idx = int(choice) - 1
        if idx < 0 or idx >= len(versions):
            print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
            return
        selected_version = versions[idx]

        config = load_config()
        selected_version_name = config.get("selected_version")
        if not selected_version_name:
            print(f"{COLOR_RED}Сначала выберите версию Minecraft (команда 'выбрать версию <имя>').{COLOR_RESET}")
            return
        mc_dir = get_minecraft_dir_for_version(selected_version_name)
        mods_dir = os.path.join(mc_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        jar_file = None
        for file in selected_version.get('files', []):
            if file.get('filename', '').endswith('.jar'):
                jar_file = file
                break
        if not jar_file:
            print(f"{COLOR_RED}Не найден файл .jar для скачивания{COLOR_RESET}")
            return

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
            print(f"\n{COLOR_GREEN}✓ Мод '{mod_info.get('title')}' успешно скачан в папку {mods_dir}{COLOR_RESET}")
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
            download_mod(mod_info)
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

def install_mod_auto(slug, display_name, loader=None):
    config = load_config()
    selected_version_name = config.get("selected_version")
    if not selected_version_name:
        print(f"{COLOR_RED}Сначала выберите версию Minecraft (команда 'выбрать версию <имя>').{COLOR_RESET}")
        return

    mc_dir = get_minecraft_dir_for_version(selected_version_name)
    mods_dir = os.path.join(mc_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    api_url = f"https://api.modrinth.com/v2/project/{slug}/version"
    headers = {"User-Agent": "CobaltLauncher/1.0"}
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        versions = resp.json()
    except Exception as e:
        print(f"{COLOR_RED}Ошибка получения версий мода {display_name}: {e}{COLOR_RESET}")
        return

    if not versions:
        print(f"{COLOR_RED}Не найдено ни одной версии мода {display_name}{COLOR_RESET}")
        return

    versions.sort(key=lambda v: v.get('date_published', ''), reverse=True)
    latest_version = versions[0]

    jar_file = None
    for file in latest_version.get('files', []):
        if file.get('filename', '').endswith('.jar'):
            jar_file = file
            break
    if not jar_file:
        print(f"{COLOR_RED}Не найден .jar файл для мода {display_name}{COLOR_RESET}")
        return

    download_url = jar_file.get('url')
    filename = jar_file.get('filename', f"{slug}.jar")
    filepath = os.path.join(mods_dir, filename)

    def progress(current, total):
        if total > 0:
            percent = (current / total) * 100
            bar = '█' * int(percent // 2) + '░' * (50 - int(percent // 2))
            print(f"\r{COLOR_CYAN}[{bar}] {percent:.1f}%{COLOR_RESET}", end="")

    print(f"{COLOR_CYAN}Скачивание {display_name}...{COLOR_RESET}")
    success = download_with_retry(download_url, filepath, progress, max_retries=3)
    if success:
        print(f"\n{COLOR_GREEN}✓ {display_name} установлен в папку модов версии {selected_version_name}.{COLOR_RESET}")
    else:
        print(f"\n{COLOR_RED}Не удалось скачать {display_name}{COLOR_RESET}")

def install_sodium():
    install_mod_auto("sodium", "Sodium", loader="fabric")

def install_embeddium():
    install_mod_auto("embeddium", "Embeddium", loader="forge")

def install_modmenu():
    install_mod_auto("modmenu", "Mod Menu", loader="fabric")

def install_journeymap():
    install_mod_auto("journeymap", "JourneyMap", loader=None)

def install_xaeros_minimap():
    install_mod_auto("xaeros-minimap", "Xaero's Minimap", loader=None)

def install_vulkanmod():
    install_mod_auto("vulkanmod", "VulkanMod", loader=None)

def install_iris():
    install_mod_auto("iris", "Iris Shaders", loader="fabric")

def install_fabric_api():
    install_mod_auto("fabric-api", "Fabric API", loader="fabric")

def install_quilted_fabric_api():
    install_mod_auto("qfapi", "Quilted Fabric API", loader="quilt")

def install_mod_by_name(mod_name):
    config = load_config()
    selected_version_name = config.get("selected_version")
    if not selected_version_name:
        print(f"{COLOR_RED}Сначала выберите версию Minecraft (команда 'выбрать версию <имя>').{COLOR_RESET}")
        return
    mc_dir = get_minecraft_dir_for_version(selected_version_name)
    mods_dir = os.path.join(mc_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)
    print(f"{COLOR_CYAN}Поиск мода '{mod_name}' на Modrinth...{COLOR_RESET}")
    search_url = f"https://api.modrinth.com/v2/search?query={mod_name}&limit=5&facets=[[\"project_type:mod\"]]"
    headers = {"User-Agent": "CobaltLauncher/1.0"}
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get('hits', [])
        if not hits:
            print(f"{COLOR_RED}Мод '{mod_name}' не найден на Modrinth{COLOR_RESET}")
            return
        print(f"{COLOR_GREEN}Найдено несколько модов:{COLOR_RESET}")
        for i, hit in enumerate(hits[:5], 1):
            title = hit.get('title', 'Без названия')
            slug = hit.get('slug')
            print(f"{COLOR_YELLOW}{i}.{COLOR_RESET} {title} (slug: {slug})")
        choice = input(f"{COLOR_YELLOW}Выберите номер мода для установки (или 'в' для отмены): {COLOR_RESET}")
        if choice.lower() == 'в':
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(hits):
                slug = hits[idx].get('slug')
                if slug:
                    install_mod_auto(slug, hits[idx].get('title'), loader=None)
                else:
                    print(f"{COLOR_RED}Ошибка: slug не найден{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Неверный номер{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}Неверный ввод{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка поиска мода: {e}{COLOR_RESET}")

def open_alt_mod_site():
    url = "https://ru-minecraft.ru"
    print(f"{COLOR_CYAN}Открытие ru-minecraft.ru в браузере...{COLOR_RESET}")
    try:
        webbrowser.open(url)
        print(f"{COLOR_GREEN}Сайт открыт в браузере!{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка открытия браузера: {e}{COLOR_RESET}")
        print(f"{COLOR_YELLOW}Вы можете открыть сайт вручную: {url}{COLOR_RESET}")