if command == "заметки":
  with open(r"C:\cobalt_launcher_nano_reliz\config_files\notes.txt", "r", encoding="utf-8") as file:
   view_notes = file.readlines()
     
  for number_notes_list, notes_list in enumerate (view_notes, start=1):
   print(f"{BLUE}{number_notes_list}) {notes_list} {COLOR_END}")