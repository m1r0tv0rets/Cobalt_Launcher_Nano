if command == "конфиги лаунчера":
  current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
  desktop_folder = os.path.join(os.environ["USERPROFILE"], "Desktop")
  shutil.copytree(r"C:\cobalt_launcher_nano_reliz\config_files", f"Бэкап Кобальт Лаунчера {current_time}")
  print(f"{GREEN}Все файлы успешно скопированы на рабочий стол!{COLOR_END}")