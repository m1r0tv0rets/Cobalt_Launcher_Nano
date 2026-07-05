if command == "установить мод версию":
 github_modloader_minecraft_json_url = "https://raw.githubusercontent.com/m1r0tv0rets/Cobalt_Launcher_Nano/main/modloader_minecraft.json"
 modloader_minecraft_folder = Path(r"C:\cobalt_launcher_nano_reliz\modloader_minecraft")
 modloader_temp_zip_file = modloader_minecraft_folder / "temp_modloader.zip"
 
 print(f"{SKY_BLUE}Получение списка модлоадеров с GitHub...{COLOR_END}")
 modloader_minecraft_list = json.loads(urllib.request.urlopen(github_modloader_minecraft_json_url).read())
 
 for number, modloader_minecraft in enumerate(modloader_minecraft_list, start=1):
  print(f"{number}. {modloader_minecraft['name']}")
     
 choice_modloader_minecraft = str(input(f"{GREEN}Введите номер модлоадера для установки или нажмите Enter для отмены: {COLOR_END}"))
 
 if choice_modloader_minecraft.isdigit(): 
  choice_index_modloader_minecraft = int(choice_modloader_minecraft) - 1 
     
  if 0 <= choice_index_modloader_minecraft < len(modloader_minecraft_list):
   selected_modloader_minecraft = modloader_minecraft_list[choice_index_modloader_minecraft]
   downoald_url_modloader = selected_modloader_minecraft["download_url"]
         
   if downoald_url_modloader:
    print(f"Скачивание модлоадера: {selected_modloader_minecraft['name']}...")
    requests_browser_client = urllib.request.Request(downoald_url_modloader, headers={'User-Agent': 'Mozilla'})
     
    with urllib.request.urlopen(requests_browser_client) as response, open(modloader_temp_zip_file, 'wb') as out_file:
     out_file.write(response.read())
                 
    print(f"{YELLOW}Распаковка файлов модлоадера...{COLOR_END}")
     
    target_version_folder = modloader_minecraft_folder / selected_modloader_minecraft['name']
    os.makedirs(target_version_folder, exist_ok=True)
     
    with zipfile.ZipFile(modloader_temp_zip_file, 'r') as zip_ref:
     zip_ref.extractall(target_version_folder)
                 
    modloader_temp_zip_file.unlink()
    print(f"{GREEN}{selected_modloader_minecraft['name']} успешно установлен!{COLOR_END}")