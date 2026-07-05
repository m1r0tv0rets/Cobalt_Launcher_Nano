if command == "лог":
 log_folder = Path(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\logs")
 desktop_folder = os.path.join(os.environ['USERPROFILE'], 'Desktop')
 
 if log_folder.exists() and any(log_folder.iterdir()):
  log_files = [f for f in log_folder.glob("*.txt") if f.is_file()]
  
  if log_files:
   latest_log = max(log_files, key=os.path.getmtime)
   shutil.copy(latest_log, os.path.join(desktop_folder, "latest_minecraft_log.txt"))
   print(f"{GREEN}Последний измененный лог успешно скопирован на Рабочий стол!{COLOR_END}")
  else:
   print(f"{RED}В папке logs нет текстовых файлов логов!{COLOR_END}")