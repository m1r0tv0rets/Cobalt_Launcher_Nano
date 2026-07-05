if command == "создать заметки":
  notes = (input("{RED}Введите текст своей заметки: {COLOR_END}"))
    
  with open(r"C:\cobalt_launcher_nano_reliz\config_files\notes.txt", "a", encoding="utf-8") as file:
   file.write(notes + "\n")
   print("{GREEN}Текст заметки успешно сохранен!{COLOR_END}")
      
  with open(r"C:\cobalt_launcher_nano_reliz\config_files\notes.txt", "r", encoding="utf-8") as f:
   saved_notes = f.read()
   print(f"{GREEN}Ваша сохраненная заметка:\n{saved_notes} {COLOR_END}")