if command == "запуск ванили": 
  offline_accounts_input = ""
  choise_number_username = ""
  collector_java_exe = ""
  user_arguments_input = ""
    
  user_input_mode = str(input(f"{YELLOW}Введите свой никнейм или выберите из созданных (введите созданные): {COLOR_END}")).strip()
    
  if user_input_mode == "созданные":
   offline_accounts_path_folder = r"C:\cobalt_launcher_nano_reliz\config_files\accounts.txt"
        
   with open(offline_accounts_path_folder, "r", encoding="utf-8") as f:
    accounts_list = [line.strip() for line in f.readlines() if line.strip()]
        
   for number_list_accounts, file_accounts in enumerate(accounts_list, start=1):
    print(f"{BLUE}{number_list_accounts}) {file_accounts} {COLOR_END}")
        
   username_choice = int(input(f"{YELLOW}Введите номер аккаунта: {COLOR_END}"))
   choise_number_username = accounts_list[username_choice - 1]
   print(f"{GREEN}Выбран аккаунт под номером {username_choice}! Ваш никнейм: {choise_number_username} {COLOR_END}")
    
  else:
   offline_accounts_input = user_input_mode
  
  vanilla_versions_folder = Path(r"C:\cobalt_launcher_nano_reliz\minecraft_vanilla\versions")
  
  for versions_list_folder in vanilla_versions_folder.iterdir():
   if versions_list_folder.is_dir():
    print(f"{GREEN}{versions_list_folder.name} {COLOR_END}")
  
  version_minecraft = str(input(f"{YELLOW}Введите название версии которую вы хотите запустить: {COLOR_END}")).strip()
  ram_size = str(input(f"{YELLOW}Сколько хотите выделить ОЗУ игре: {COLOR_END}")).strip()
  version_java = str(input(f"{YELLOW}Какую версию джавы вы хотите использовать? 8(До 1.16.5), 17(До 1.21.4), 21(До последних) (или свою джаву) (или свои аргументы): {COLOR_END}")).strip()
    
  if version_java == "8":
   collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_8\java_8\bin\java.exe"
    
  elif version_java == "17":
   collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_17\java_17\bin\java.exe"
    
  elif version_java == "21":
   collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_21\java_21\bin\java.exe"
    
  elif version_java == "свою джаву":
   print(f"{PURPLE}Пример пути: C:\\cobalt_launcher_nano_reliz\\java\\java_17\\bin\\java.exe{COLOR_END}")
   collector_java_exe = str(input(f"{GREEN}Введите путь до джавы: {COLOR_END}")).strip()
    
  elif version_java == "свои аргументы":
   print(f"{YELLOW}Отсюда можно взять аргументы https://rubukkit.org{COLOR_END}")
   print(f"{YELLOW}Пример: -Xmx4G -Xms4G{COLOR_END}")
   user_arguments_input = str(input(f"{RED}Введите аргументы: {COLOR_END}")).strip()
   collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_17\bin\java.exe"

  if not collector_java_exe:
   collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_17\bin\java.exe"

  minecraft_folder = r"C:\cobalt_launcher_nano_reliz\minecraft_vanilla" 
  version = f"{version_minecraft}"
  instances_game_directory = rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}"
  username = offline_accounts_input or choise_number_username

  if user_arguments_input:
   final_java_arguments = user_arguments_input.split()
  
  else:
   final_java_arguments = [f"-Xmx{ram_size}G", f"-Xms2G"]

  options = {
   "username": username,
   "uuid": "",          
   "token": "",         
   "executablePath": collector_java_exe, 
   "jvmArguments": final_java_arguments,
   "enableLoggingConfig": False,
   "gameDirectory": instances_game_directory,
  }

  launch_command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_folder, options)

  cmd_command = ["cmd.exe", "/K"] + launch_command
  subprocess.Popen(cmd_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
  print(f"{GREEN}Minecraft {version} скоро запустится!{COLOR_END}")
