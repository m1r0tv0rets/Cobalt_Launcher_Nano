if command == "запуск мод":
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

 modloader_versions_folder = Path(r"C:\cobalt_launcher_nano_reliz\modloader_minecraft")
 if modloader_versions_folder.exists():
  for versions_dir in modloader_versions_folder.rglob("versions"):
   if versions_dir.is_dir():
    for version_path in versions_dir.iterdir():
     if version_path.is_dir():
      print(f"{GREEN}{version_path.name}{COLOR_END}")

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

 if not collector_java_exe:
  collector_java_exe = r"C:\cobalt_launcher_nano_reliz\java\java_17\bin\java.exe"

 version = f"{version_minecraft}"
 if 'instance_name' not in locals() or not instance_name:
  instance_name = "default"
 instances_game_directory = rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}"
 username = offline_accounts_input or choise_number_username

 minecraft_modloader_folder = ""
 if modloader_versions_folder.exists():
  for p in modloader_versions_folder.rglob("*.json"):
   if p.stem == version:
    minecraft_modloader_folder = str(p.parent.parent.parent)
    break

 if not minecraft_modloader_folder:
  minecraft_modloader_folder = rf"C:\cobalt_launcher_nano_reliz\modloader_minecraft\{version_minecraft}"

 if user_arguments_input:
  final_java_arguments = user_arguments_input.split()
 else:
  final_java_arguments = [f"-Xmx{ram_size}G", f"-Xms{ram_size}G"]

 options = {
  "username": username,
  "uuid": "",
  "token": "",
  "executablePath": collector_java_exe,
  "jvmArguments": final_java_arguments,
  "enableLoggingConfig": False,
  "gameDirectory": instances_game_directory
 }

 launch_command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_modloader_folder, options)

 log_dir = rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\logs"
 os.makedirs(log_dir, exist_ok=True)

 current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
 unique_log_path = os.path.join(log_dir, f"log_{current_time}.txt")

 log_file = open(unique_log_path, "w", encoding="utf-8")

 subprocess.Popen(launch_command, stdout=log_file, stderr=log_file, creationflags=subprocess.CREATE_NEW_CONSOLE)
 print(f"{GREEN}Minecraft {version} запущен! Консоль открыта, лог успешно пишется в файл log_{current_time}.txt{COLOR_END}")
