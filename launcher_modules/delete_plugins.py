if command == "удалить плагин":
  plugins_folder = Path(r"C:\cobalt_launcher_nano_reliz\plugins")
  files = list(plugins_folder.glob("*.py"))
    
  for number, file in enumerate(files, start=1):
    print(f"{SKY_BLUE}{number}) {file.name} {COLOR_END}")
        
  choice_delete_plugin = input(f"{GREEN}Введите номер файла для удаления: {COLOR_END}")
    
  if choice_delete_plugin .isdigit():
   index_plugin = int(choice_delete_plugin) - 1
   
   if 0 <= index_plugin < len(files):
    files[index_plugin].unlink()  
    print(f"{RED}Плагин успешно удален!{COLOR_END}")