if command == "офф акк":
  print(f"""
{GREEN}Что хотите сделать?{COLOR_END}
{GREEN}1) Создать акк{COLOR_END}
{GREEN}2) Показать созданные аккаунты{COLOR_END}
{GREEN}3) Удалить аккаунт{COLOR_END}
""")
  choise_offline_account = str(input("Укажите номер: "))
  if choise_offline_account == "1":
     minecraft_nickname = str(input(f"{RED}Введите свой никнейм: {COLOR_END}"))
     print(f"{GREEN}Ваш аккаунт {minecraft_nickname} успешно создан!{COLOR_END}")
    
     config_nickname_folder = r"C:\cobalt_launcher_nano_reliz\config_files\accounts.txt"
     nickname_save = f"{minecraft_nickname}\n"

     with open(config_nickname_folder, "a", encoding="utf-8") as file:
      file.write(nickname_save)
    
  elif choise_offline_account == "2":
   look_accounts = r"C:\cobalt_launcher_nano_reliz\config_files\accounts.txt"
   with open(look_accounts, "r", encoding="utf-8") as file:
    for number, line in enumerate(file, start=1):
        print(f"[{number}] {line.strip()}")
        
  elif choise_offline_account == "3":
    offline_accounts_delete_folder = r"C:\cobalt_launcher_nano_reliz\config_files\accounts.txt"

    with open(offline_accounts_delete_folder, "r", encoding="utf-8") as file:
     lines = file.readlines()

    for number, line in enumerate(lines, start=1):
     print(f"[{number}] {line.strip()}")

    number_accounts_delete = int(input(f"{GREEN}Введите номер аккаунта, который хотите удалить: {COLOR_END}"))
    del lines[number_accounts_delete - 1]

    with open(offline_accounts_delete_folder, "w", encoding="utf-8") as file:
     file.writelines(lines)
     print(f"{RED}Аккаунт под номером {number_accounts_delete} успешно удален!{COLOR_END}")