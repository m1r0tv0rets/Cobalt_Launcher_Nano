if command == "помощь":
  print(f"""
{SKY_BLUE}ДОСТУПНЫЕ КОМАНДЫ:{COLOR_END}

{PURPLE}НАСТРОЙКА АККАУНТОВ:{COLOR_END}
{GREEN}офф акк{COLOR_END} - Управление оффлайн аккаунтами
{GREEN}елу акк{COLOR_END} - Управление ely.by аккаунтами {RED}(В РАЗРАБОТКЕ){COLOR_END}

{PURPLE}ПРОСМОТР И УСТАНОВКА:{COLOR_END}
{GREEN}скачать ваниль{COLOR_END} - Показать и установить версии майнкрафт

{PURPLE}УСТАНОВКА И ЗАПУСК:{COLOR_END}
{GREEN}запуск ванили{COLOR_END} - Запустить ванильный Minecraft
{GREEN}запуск мод{COLOR_END} - Запустить модифицированный майнкрафт(Fabric, Forge и тд.) Minecraft 

{PURPLE}РАБОТА С ФАЙЛАМИ:{COLOR_END}
{GREEN}моды{COLOR_END} - Открыть папку модов
{GREEN}ресурспак{COLOR_END} - Открыть папку ресурспаков
{GREEN}миры{COLOR_END} - Открыть папку миров
{GREEN}скрины{COLOR_END} - Открыть папку скриншотов
{GREEN}конфиги{COLOR_END} - Открыть папку конфигов
{GREEN}схемы{COLOR_END} - Открыть папку схем Litematica
{GREEN}бэкап{COLOR_END} - Создать резервную копию (миры, ресурспаки, конфиги, моды, конфиг лаунчера)
{GREEN}конфиги лаунчера{COLOR_END} - Скопировать папку конфигов лаунчера на рабочий стол 
{GREEN}удалить лаунчер{COLOR_END} - Полностью удалить папку лаунчера

{PURPLE}МОДЫ:{COLOR_END}
{GREEN}установить мод{COLOR_END} - установка мода с Mondrinch
{GREEN}альт мод{COLOR_END} - искать моды на ru-minecraft.ru

{PURPLE}ИНФОРМАЦИЯ И ЗАМЕТКИ:{COLOR_END}
{GREEN}инфо{COLOR_END} - Полезная информация
{GREEN}новости{COLOR_END} - Новости майнкрафт
{GREEN}заметка <текст>{COLOR_END} - Добавить заметку
{GREEN}заметки{COLOR_END} - Показать все заметки

{PURPLE}РАБОТА С ЛОГАМИ:{COLOR_END}
{GREEN}лог{COLOR_END} - Скопировать последний лог на рабочий стол

{PURPLE}ПОЛЬЗОВАТЕЛЬСКИЕ РЕШЕНИЯ:{COLOR_END}
{GREEN}скачать плагин{COLOR_END} - скачать плагин для лаунчера
{GREEN}удалить плагин{COLOR_END} - удалить плагин лаунчера
""")