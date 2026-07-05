if command == "моды":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\mods", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\mods")

elif command == "ресурспак":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\resourcepacks", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\resourcepacks")

elif command == "миры":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\saves", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\saves")

elif command == "скрины":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\screenshots", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\screenshots")

elif command == "шейдеры":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\shaderpacks", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\shaderpacks")

elif command == "схемы":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\schematics", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\schematics")

elif command == "конфиги":
 os.makedirs(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\config", exist_ok=True)
 os.startfile(rf"C:\cobalt_launcher_nano_reliz\instances\{instance_name}\config")

elif command == "корень":
 os.makedirs(r"C:\cobalt_launcher_nano_reliz", exist_ok=True)
 os.startfile(r"C:\cobalt_launcher_nano_reliz")