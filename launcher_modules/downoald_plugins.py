if command == "скачать плагин":
  github_plugins_json_url = "https://raw.githubusercontent.com/m1r0tv0rets/Cobalt_Launcher_Nano/main/plugins.json"
  plugins_folder = Path(r"C:\cobalt_launcher_nano_reliz\plugins")
  
  print(f"{SKY_BLUE}Получение списка плагинов с GitHub...{COLOR_END}")
  plugins_list = json.loads(urllib.request.urlopen(github_plugins_json_url).read())
  
  for number, plugin in enumerate(plugins_list, start=1):
    print(f"{number}. {plugin['name']} — {plugin.get('description', 'Без описания')}")
  
  choice_plugins = str(input(f"{GREEN}Введите номер плагина для установки или нажмите Enter для отмены: {COLOR_END}"))
  
  if choice_plugins.isdigit():  
   choice_index_plugin = int(choice_plugins) - 1  
    
   if 0 <= choice_index_plugin < len(plugins_list):
    selected_plugin = plugins_list[choice_index_plugin]
    url = selected_plugin["download_url"]
        
    if url:
     print(f"Скачивание плагина: {selected_plugin['name']}...")
     file_name = url.split("/")[-1]
     urllib.request.urlretrieve(url, plugins_folder / file_name)
     print(f"{GREEN}Плагин успешно установлен!{COLOR_END}")
     os.execv(sys.executable, [sys.executable] + sys.argv)