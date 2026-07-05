if command == "удалить лаунчер":
  root_folder_delete = r"C:\cobalt_launcher_nano_reliz"
  choise_delete_launcher = str(input(f"{RED}Вы действительно хотите удалить лаунчер? да/нет: {COLOR_END}"))
  
  if choise_delete_launcher == "да":
   print(f"{RED}Произвожу удаление{COLOR_END}")
   shutil.rmtree(root_folder_delete)
   print(f"{RED}Закончено!{COLOR_END}")
  
  elif choise_delete_launcher == "нет":
   print(f"{PURPLE}Я не буду удалять лаунчер{COLOR_END}")