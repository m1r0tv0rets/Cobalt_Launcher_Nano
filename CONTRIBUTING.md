### Документация по созданию плагинов для Cobalt Launcher Nano

**Содержание:**

1. Введение
2. Структура плагина
3. API для плагинов
    1. Методы PluginAPI
    2. Регистрация команд
    3. Хуки (banner, info)
    4. Примеры плагинов
        1. Плагин с простой командой
        2. Плагин с хуком баннера
        3. Плагин с хуком информации
        4. Плагин с использованием дополнительных библиотек
4. Установка плагинов
5. Создание плагинов на C++(Вторая часть в самом низу)
6. Советы и ограничения

---

**Введение**

Cobalt Launcher Nano поддерживает расширение функциональности через плагины. Плагины позволяют добавлять новые команды, изменять приветственный баннер или информацию, выводимую по команде инфо, а также выполнять любой пользовательский код на Python.

Плагины располагаются в папке:
```
Windows/Linux/macOS: ~/.cobalt_launcher_nano_files/plugins/
```
При запуске лаунчер автоматически загружает все файлы с расширением .py из этой папки (кроме __init__.py). Для инициализации плагина в нём должна быть определена функция register_plugin(api) или register_commands(cmd_dict).

---

**Структура плагина**

Минимальный плагин представляет собой обычный Python-файл с одной из двух функций регистрации:

1. Функция register_plugin(api)

Получает объект api класса PluginAPI, через который регистрируются команды и хуки.

```python
def register_plugin(api):
    # регистрация команды
    api.register_command("моякоманда", my_command_func)
    # регистрация хука баннера
    api.register_banner_hook(my_banner_hook)
```

2. Функция register_commands(cmd_dict) (устаревший способ)

Функция получает словарь, в который нужно добавить пары "имя команды": функция.

```python
def register_commands(commands):
    commands["моякоманда"] = my_command_func
```

Рекомендуется использовать первый способ, так как он предоставляет больше возможностей (хуки, доступ к путям).

---

**API для плагинов**

Класс PluginAPI доступен через параметр api в функции register_plugin. Он предоставляет следующие методы:

register_command(name: str, func: Callable, hidden: bool = False)

Регистрирует новую команду лаунчера.

· name – имя команды (строка без пробелов).
· func – функция, которая будет вызвана при вводе команды. Она принимает один аргумент – список строк args (аргументы, переданные после имени команды).
· hidden – если True, команда не будет показываться в общем списке команд (вывод помощь). По умолчанию False.

register_banner_hook(func: Callable)

Регистрирует функцию-хук для изменения баннера, который выводится при запуске лаунчера.

· func – функция, принимающая текущий баннер (строку) и возвращающая изменённый баннер (строку). Если возвращается None, баннер остаётся без изменений.

register_info_hook(func: Callable)

Регистрирует функцию-хук для изменения информационных строк, выводимых по команде инфо.

· func – функция, принимающая текущий список строк info_lines (list) и возвращающая изменённый список (list). Если возвращается None, список остаётся без изменений.

get_data_dir() -> str

Возвращает абсолютный путь к папке данных лаунчера (~/.cobalt_launcher_nano_files/). Удобно для хранения файлов плагина.

get_plugins_dir() -> str

Возвращает абсолютный путь к папке плагинов. Обычно совпадает с расположением самого плагина, но может быть полезно для доступа к другим плагинам.

---

**Примеры плагинов**

Плагин с простой командой

Создайте файл hello.py в папке plugins:

```python
# hello.py
def hello_command(args):
    """Приветствие пользователя"""
    if args:
        print(f"Привет, {' '.join(args)}!")
    else:
        print("Привет, мир!")

def register_plugin(api):
    api.register_command("привет", hello_command)
```

Теперь в лаунчере доступна команда привет. При вводе привет Вася выведется "Привет, Вася!".

Плагин с хуком баннера

Добавим к баннеру текущее время. Поскольку цветовые константы не гарантированно доступны из лаунчера, определим их локально:

```python
# time_banner.py
import datetime

COLOR_GREEN = '\033[92m'
COLOR_RESET = '\033[0m'

def banner_hook(current_banner):
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    return f"{current_banner}\n{COLOR_GREEN}Текущее время: {time_str}{COLOR_RESET}"

def register_plugin(api):
    api.register_banner_hook(banner_hook)
```

Плагин с хуком информации

Добавим в раздел инфо список установленных плагинов. Используем замыкание, чтобы передать путь к папке плагинов:

```python
# plugin_info.py
import os

COLOR_CYAN = '\033[96m'
COLOR_RESET = '\033[0m'

def make_info_hook(plugins_dir):
    def hook(info_lines):
        plugins = [f for f in os.listdir(plugins_dir) if f.endswith('.py') and f != '__init__.py']
        if plugins:
            info_lines.append(f"{COLOR_CYAN}Установленные плагины:{COLOR_RESET}")
            for p in plugins:
                info_lines.append(f"  - {p[:-3]}")
        return info_lines
    return hook

def register_plugin(api):
    api.register_info_hook(make_info_hook(api.get_plugins_dir()))
```

Плагин с использованием дополнительных библиотек

Плагин может использовать любые библиотеки Python, установленные в окружении. Пример плагина, который показывает курс валют (требуется библиотека requests):

```python
# currency.py
import requests

def currency_command(args):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        rub = data['rates']['RUB']
        eur = data['rates']['EUR']
        print(f"Курс USD: {rub} RUB, {eur} EUR")
    except Exception as e:
        print(f"Ошибка получения курса: {e}")

def register_plugin(api):
    api.register_command("курс", currency_command)
```

---

**Установка плагинов**

Лаунчер имеет встроенную команду плагины, которая открывает меню для скачивания плагинов из официального репозитория (список берётся из PLUGINS_INDEX_URL). Вы можете также вручную скопировать файл .py в папку plugins – после перезапуска лаунчера он будет загружен.

Важно: После установки нового плагина лаунчер автоматически перезапускается, чтобы плагин стал доступен.

---

Создание плагинов на C++**

Лаунчер написан на Python, поэтому нативно поддерживает только Python-плагины. Однако вы можете создавать плагины на C++ в виде расширений Python (shared library), которые затем импортируются в вашем Python-плагине.

**Краткая инструкция:**

1. Напишите код на C++, используя Python C API или библиотеку pybind11 (рекомендуется).
2. Скомпилируйте его в динамическую библиотеку (.so на Linux, .pyd на Windows).
3. Поместите полученный файл в папку plugins (или в любую другую, доступную для импорта).
4. В вашем Python-плагине импортируйте этот модуль и используйте его функции.

Пример с pybind11

C++ код (mymodule.cpp):

```cpp
#include <pybind11/pybind11.h>

int add(int i, int j) {
    return i + j;
}

PYBIND11_MODULE(mymodule, m) {
    m.doc() = "пример модуля на C++";
    m.def("add", &add, "функция сложения");
}
```

Компиляция (пример для Linux):

```bash
c++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 --includes` mymodule.cpp -o mymodule.so
```

Python-плагин (cpp_plugin.py):

```python
import mymodule

def add_command(args):
    if len(args) >= 2:
        try:
            a = int(args[0])
            b = int(args[1])
            result = mymodule.add(a, b)
            print(f"Результат: {result}")
        except:
            print("Ошибка: аргументы должны быть числами")
    else:
        print("Использование: add <число1> <число2>")

def register_plugin(api):
    api.register_command("add", add_command)
```

Таким образом, вы получаете возможность писать высокопроизводительные части плагина на C++ и вызывать их из Python.

---

**Советы и ограничения**

· Имена команд должны быть уникальными. Если два плагина зарегистрируют команду с одинаковым именем, последняя загруженная перезапишет предыдущую (порядок загрузки – алфавитный по имени файла).
· Хуки выполняются последовательно в порядке загрузки плагинов. Будьте аккуратны с модификацией одних и тех же данных.
· Импорт лаунчера не рекомендуется – используйте предоставленное API. Прямой импорт может привести к циклическим зависимостям или сломаться при обновлении лаунчера.
· Обработка ошибок: старайтесь перехватывать исключения внутри функций плагина, чтобы не крашить лаунчер.
· Цветной вывод: вы можете использовать ANSI-коды напрямую. Для удобства определите свои константы в начале плагина:
  ```python
  COLOR_RED = '\033[91m'
  COLOR_GREEN = '\033[92m'
  COLOR_YELLOW = '\033[93m'
  COLOR_BLUE = '\033[94m'
  COLOR_MAGENTA = '\033[95m'
  COLOR_CYAN = '\033[96m'
  COLOR_RESET = '\033[0m'
  ```
### Создание плагинов на C++

Ваш C++ код, скомпилированный в бинарный модуль (.so/.pyd), будет выступать в роли основного кода плагина, а Python-обёртка будет служить для регистрации вашего плагина в лаунчере.

# Получение доступа к API лаунчера из C++

**Шаг 1: В C++ коде импортируем модуль лаунчера**

Поскольку лаунчер уже запущен и плагин загружается в его контексте, интерпретатор Python уже инициализирован. Вам не нужно создавать py::scoped_interpreter. Вместо этого вы просто импортируете главный модуль лаунчера или его части.

```cpp
#include <pybind11/embed.h>
#include <pybind11/stl.h> // Для автоматической конвертации STL контейнеров
#include <iostream>

namespace py = pybind11;

// Глобальные переменные для хранения ссылок на API
py::object launcher_module;
py::object plugin_api_class;
py::object launcher_config;

void initialize_launcher_api() {
    try {
        // Импортируем главный модуль лаунчера (предполагаем, что он называется __main__ или launcher)
        // В реальности имя модуля может отличаться, возможно, потребуется импорт по имени файла
        launcher_module = py::module_::import("__main__");
        
        // Получаем класс PluginAPI из главного модуля
        plugin_api_class = launcher_module.attr("PluginAPI");
        
        // Получаем функцию загрузки конфига
        auto load_config_func = launcher_module.attr("load_config");
        launcher_config = load_config_func();
        
        std::cout << "C++: API лаунчера успешно загружен" << std::endl;
    } catch (const py::error_already_set& e) {
        std::cerr << "C++: Ошибка импорта API лаунчера: " << e.what() << std::endl;
    }
}
```

**Шаг 2: Работа с данными лаунчера**

Теперь вы можете читать и изменять конфигурацию лаунчера прямо из C++.

```cpp
std::string get_current_version() {
    try {
        // Получаем атрибут "selected_version" из объекта конфига
        py::object version = launcher_config.attr("get")("selected_version");
        if (version.is_none()) {
            return "";
        }
        return version.cast<std::string>();
    } catch (const py::error_already_set& e) {
        std::cerr << "C++: Ошибка получения версии: " << e.what() << std::endl;
        return "";
    }
}

void set_java_memory(int gb) {
    try {
        // Модифицируем конфиг
        py::object java_args = launcher_config.attr("get")("java_args");
        std::string args_str = java_args.cast<std::string>();
        
        // Здесь ваша C++ логика по изменению аргументов
        // ...
        
        // Устанавливаем новое значение
        launcher_config.attr("__setitem__")("java_args", py::str("-Xmx" + std::to_string(gb) + "G"));
        
        // Сохраняем конфиг
        auto save_config_func = launcher_module.attr("save_config");
        save_config_func(launcher_config);
        
        std::cout << "C++: Память Java изменена на " << gb << "GB" << std::endl;
    } catch (const py::error_already_set& e) {
        std::cerr << "C++: Ошибка изменения памяти: " << e.what() << std::endl;
    }
}
```

ОБЯЗАТЕЛЬНО. Регистрация C++ команд в лаунчере

Чтобы лаунчер узнал о ваших командах, вам нужно вызвать метод register_command API из C++.

**Шаг 3: Создание C++ функций-обработчиков**

```cpp
// Функция, которая будет вызвана при вводе команды в лаунчере
void cpp_hello_command(py::list args) {
    try {
        if (args.size() > 0) {
            std::string name = args[0].cast<std::string>();
            std::cout << "Привет из C++, " << name << "!" << std::endl;
        } else {
            std::cout << "Привет из C++!" << std::endl;
        }
    } catch (const py::cast_error& e) {
        std::cerr << "Ошибка: аргумент должен быть строкой" << std::endl;
    }
}

// Функция для сложения двух чисел (демонстрация производительности)
int cpp_add(py::list args) {
    if (args.size() >= 2) {
        try {
            int a = args[0].cast<int>();
            int b = args[1].cast<int>();
            return a + b;
        } catch (const py::cast_error& e) {
            std::cerr << "Ошибка: аргументы должны быть числами" << std::endl;
        }
    }
    return 0;
}
```

**Шаг 4: Создание pybind11 модуля с "фабрикой" для API**

В предыдущем примере мы создавали простой модуль. Теперь мы создадим модуль, который предоставляет C++ функции Python-обёртке.

```cpp
// my_cpp_plugin.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>

namespace py = pybind11;

// Объявляем функции, которые будут вызваны из Python
void cpp_hello_command(py::list args) {
    if (args.size() > 0) {
        std::cout << "C++ Hello, " << args[0].cast<std::string>() << "!" << std::endl;
    } else {
        std::cout << "C++ Hello, World!" << std::endl;
    }
}

int cpp_add(py::list args) {
    if (args.size() >= 2) {
        return args[0].cast<int>() + args[1].cast<int>();
    }
    return 0;
}

// Функция, которая принимает объект API и регистрирует команды
// Она будет вызвана из Python с параметром api
void register_with_api(py::object api) {
    try {
        // Создаём Python-функции-обёртки вокруг наших C++ функций
        // Это нужно, чтобы адаптировать сигнатуру: наша C++ функция принимает py::list,
        // а лаунчер ожидает функцию, принимающую список строк.
        
        // Вариант 1:直接用 py::cpp_function
        py::object hello_wrapper = py::cpp_function([](py::args args) {
            cpp_hello_command(args);
        });
        
        py::object add_wrapper = py::cpp_function([](py::args args) {
            int result = cpp_add(args);
            py::print("Результат сложения из C++:", result);
        });
        
        // Регистрируем команды через API лаунчера
        api.attr("register_command")("cpp_hello", hello_wrapper);
        api.attr("register_command")("cpp_add", add_wrapper);
        
        // Можно также получить путь к папке данных лаунчера
        std::string data_dir = api.attr("get_data_dir")().cast<std::string>();
        std::cout << "C++: Папка данных лаунчера: " << data_dir << std::endl;
        
        py::print("C++ модуль успешно зарегистрировал команды!");
    } catch (const py::error_already_set& e) {
        py::print("Ошибка в register_with_api:", e.what());
    }
}

// Определяем модуль
PYBIND11_MODULE(my_cpp_plugin_core, m) {
    m.doc() = "C++ ядро плагина для Cobalt Launcher Nano";
    
    // Экспортируем функцию регистрации, которую вызовет Python-обёртка
    m.def("register_with_api", &register_with_api, "Регистрирует команды в лаунчере");
    
    // Можно также экспортировать отдельные функции для прямого вызова из Python
    m.def("hello", &cpp_hello_command);
    m.def("add", &cpp_add);
}
```

**4. Python-обёртка для C++ модуля**

Теперь создадим Python-файл, который будет выступать в роли моста. Этот файл нужно положить в папку plugins.

```python
# my_cpp_plugin.py
import sys
import os

# Добавляем путь к папке с скомпилированным .so/.pyd файлом
# Предполагаем, что бинарный файл лежит в той же папке, что и этот скрипт
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

try:
    # Импортируем скомпилированный C++ модуль
    import my_cpp_plugin_core
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"{COLOR_RED}Ошибка загрузки C++ ядра: {e}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}Убедитесь, что файл my_cpp_plugin_core.so/.pyd находится в {plugin_dir}{COLOR_RESET}")
    CORE_AVAILABLE = False

def register_plugin(api):
    """Функция, вызываемая лаунчером при загрузке плагина"""
    if not CORE_AVAILABLE:
        print(f"{COLOR_RED}C++ плагин не загружен: отсутствует скомпилированный модуль{COLOR_RESET}")
        return
    
    try:
        # Вызываем C++ функцию, передавая ей объект API лаунчера
        my_cpp_plugin_core.register_with_api(api)
        
        # Альтернативно, можно зарегистрировать Python-обёртки, которые вызывают C++ функции
        # def python_hello_wrapper(args):
        #     my_cpp_plugin_core.hello(args)
        # api.register_command("py_cpp_hello", python_hello_wrapper)
        
        print(f"{COLOR_GREEN}C++ плагин успешно инициализирован!{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Ошибка инициализации C++ плагина: {e}{COLOR_RESET}")

# Для обратной совместимости
def register_commands(commands):
    """Старый способ регистрации (если нужно)"""
    if CORE_AVAILABLE:
        commands["cpp_hello_direct"] = lambda args: my_cpp_plugin_core.hello(args)
```

**Важные нюансы при работе с C++ и pybind11

Политики возврата значений (Return Value Policies) 

Когда ваша C++ функция возвращает данные, нужно указать, кто владеет памятью.**

```cpp
// Если функция возвращает указатель на внутренние данные
m.def("get_data", &SomeClass::getData, py::return_value_policy::reference);

// Если функция создаёт новый объект
m.def("create_data", &createData, py::return_value_policy::take_ownership);
```

**Конвертация STL контейнеров**

Используйте #include <pybind11/stl.h> для автоматической конвертации между std::vector/std::map и Python списками/словарями.

```cpp
#include <pybind11/stl.h>

std::vector<std::string> get_mod_list() {
    return {"mod1.jar", "mod2.jar"};
}

// В pybind11 модуле
m.def("get_mod_list", &get_mod_list); // автоматически конвертируется в list
```

Обработка исключений 

Пробрасывайте исключения правильно:

```cpp
try {
    // какой-то код
} catch (const std::exception& e) {
    // Пробрасываем как Python исключение
    throw py::value_error(e.what());
}
```

Взаимодействие с GIL (Global Interpreter Lock)

Если вы работаете с потоками, нужно аккуратно управлять GIL:

```cpp
// В длительной C++ операции, не требующей Python
{
    py::gil_scoped_release release;
    // Длительная операция
    heavy_computation();
}
// GIL автоматически восстанавливается при выходе из блока

// Когда нужно снова вызвать Python
{
    py::gil_scoped_acquire acquire;
    py::print("Вернулись в Python");
}
```

**6. Полный пример C++ плагина для лаунчера**

Вот законченный пример плагина, который:

1. Получает доступ к конфигурации лаунчера
2. Регистрирует команды
3. Использует производительные C++ вычисления

```cpp
// advanced_cpp_plugin.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/embed.h>
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <numeric>

namespace py = pybind11;

// ============ Полезные функции на C++ ============
std::vector<std::string> filter_mods(const std::vector<std::string>& mods, const std::string& pattern) {
    std::vector<std::string> result;
    std::copy_if(mods.begin(), mods.end(), std::back_inserter(result),
                 [&pattern](const std::string& mod) {
                     return mod.find(pattern) != std::string::npos;
                 });
    return result;
}

long long calculate_total_downloads(const std::vector<int>& downloads) {
    return std::accumulate(downloads.begin(), downloads.end(), 0LL);
}

// ============ Интеграция с лаунчером ============
py::object launcher_config;
py::object plugin_api;

void initialize(py::object api) {
    plugin_api = api;
    
    try {
        // Получаем доступ к конфигу
        auto main_module = py::module_::import("__main__");
        auto load_config = main_module.attr("load_config");
        launcher_config = load_config();
        
        py::print("C++: Плагин инициализирован, конфиг загружен");
    } catch (const py::error_already_set& e) {
        py::print("C++: Ошибка инициализации:", e.what());
    }
}

void cmd_filter_mods(py::list args) {
    if (args.size() < 2) {
        py::print("Использование: cpp_filter_mods <паттерн>");
        return;
    }
    
    std::string pattern = args[0].cast<std::string>();
    
    // Здесь бы мы получили список модов из лаунчера
    // Для примера используем тестовые данные
    std::vector<std::string> mods = {"optifine.jar", "jei.jar", "waila.jar"};
    
    auto filtered = filter_mods(mods, pattern);
    
    py::print("Найдено модов:", filtered.size());
    for (const auto& mod : filtered) {
        py::print(" -", mod);
    }
}

void cmd_show_stats(py::list args) {
    // Показываем статистику из конфига
    try {
        std::string version = launcher_config.attr("get")("selected_version").cast<std::string>();
        std::string java_args = launcher_config.attr("get")("java_args").cast<std::string>();
        
        py::print("Текущая версия Minecraft:", version);
        py::print("Аргументы Java:", java_args);
        
        // Анализируем аргументы Java через C++ регулярные выражения
        std::regex memory_pattern("-Xmx(\\d+)G");
        std::smatch matches;
        if (std::regex_search(java_args, matches, memory_pattern)) {
            int memory_gb = std::stoi(matches[1].str());
            py::print("Выделено памяти:", memory_gb, "GB");
            
            if (memory_gb < 4) {
                py::print("Рекомендуется увеличить память для производительности!");
            }
        }
    } catch (const std::exception& e) {
        py::print("Ошибка анализа:", e.what());
    }
}

// ============ Регистрация модуля ============
PYBIND11_MODULE(cpp_launcher_plugin, m) {
    m.doc() = "Продвинутый C++ плагин для Cobalt Launcher";
    
    // Функция инициализации, принимающая API
    m.def("init", &initialize, "Инициализирует плагин с API лаунчера");
    
    // Команды для регистрации
    m.def("filter_mods", &cmd_filter_mods);
    m.def("show_stats", &cmd_show_stats);
    
    // Полезные утилиты
    m.def("calculate_total_downloads", &calculate_total_downloads);
    
    // Константы
    m.attr("VERSION") = "1.0.0";
    m.attr("AUTHOR") = "C++ Developer";
}
```

И соответствующий Python-мост:

```python
# cpp_launcher_plugin.py
import os
import sys

plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

try:
    import cpp_launcher_plugin
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"\033[91mОшибка загрузки C++ ядра: {e}\033[0m")
    CORE_AVAILABLE = False

def register_plugin(api):
    if not CORE_AVAILABLE:
        return
    
    try:
        # Инициализируем C++ часть с API
        cpp_launcher_plugin.init(api)
        
        # Регистрируем команды
        api.register_command("cpp_filter", lambda args: cpp_launcher_plugin.filter_mods(args))
        api.register_command("cpp_stats", lambda args: cpp_launcher_plugin.show_stats(args))
        
        print(f"\033[92mC++ плагин v{cpp_launcher_plugin.VERSION} загружен\033[0m")
    except Exception as e:
        print(f"\033[91mОшибка: {e}\033[0m")
```

**7. Компиляция и установка**

Для компиляции используйте команду (пример для Linux):

```bash
c++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 --includes` advanced_cpp_plugin.cpp -o cpp_launcher_plugin.so
```

Для Windows:

```bash
cl /EHsc /MD advanced_cpp_plugin.cpp /I\path\to\pybind11\include /I\path\to\python\include /link /OUT:cpp_launcher_plugin.pyd
```

**Скомпилированный файл (.so/.pyd) поместите в папку ~/.cobalt_launcher_nano_files/plugins/ рядом с Python-обёрткой.**
