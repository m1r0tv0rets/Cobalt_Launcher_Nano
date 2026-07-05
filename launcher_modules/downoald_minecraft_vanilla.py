if command == "скачать ваниль":
  minecraft_vanilla_folder_download = r"C:\cobalt_launcher_nano_reliz\minecraft_vanilla"
  all_versions = minecraft_launcher_lib.utils.get_version_list()

  filtered_versions = []

  print(f"{RED}Какую категорию версий показать?{COLOR_END}")
  print(f"{RED}Доступные варианты: альфа, бета, снапшоты, релизы{COLOR_END}")
  type_choice = str(input(f"{GREEN}Введите категорию: {COLOR_END}")).strip().lower()
  
  if type_choice == "альфа":
   print(f"{PURPLE}СПИСОК АЛЬФА ВЕРСИЙ:{COLOR_END}")
   for version in all_versions:
    if version["type"] == "old_alpha":
     filtered_versions.append(version["id"])

  elif type_choice == "бета":
   print(f"{PURPLE}СПИСОК БЕТА ВЕРСИЙ:{COLOR_END}")
   for version in all_versions:
    if version["type"] == "old_beta":
     filtered_versions.append(version["id"])

  elif type_choice == "снапшоты":
   print(f"{PURPLE}СПИСОК СНАПШОТОВ:{COLOR_END}")
   for version in all_versions:
    if version["type"] == "snapshot":
     filtered_versions.append(version["id"])

  elif type_choice == "релизы":
   print(f"{PURPLE}СПИСОК РЕЛИЗОВ:{COLOR_END}")
   for version in all_versions:
    if version["type"] == "release":
     filtered_versions.append(version["id"])

  if filtered_versions:
    for number_version, version_id in enumerate(filtered_versions, start=1):
     print(f"{GREEN}{number_version}) {version_id} {COLOR_END}")
    
    choice_versions_vanilla_minecraft = str(input(f"{GREEN}Введите номер версии для скачивания (или Enter для отмены):{COLOR_END}"))
    
    if choice_versions_vanilla_minecraft.isdigit():
     index_versions = int(choice_versions_vanilla_minecraft) - 1
        
    if 0 <= index_versions < len(filtered_versions):
     selected_version = filtered_versions[index_versions]
     print(f"{GREEN}Начинается скачивание {selected_version}...{COLOR_END}")
            
     minecraft_launcher_lib.install.install_minecraft_version(selected_version, minecraft_vanilla_folder_download)
     print(f"{PURPLE}Версия {selected_version} успешно скачана!{COLOR_END}")