# Проект парсинга pep

Парсер по сбору информации с документации по языку программирования Python:

* Сбор информации о PEP
    
* Сбор информации о статусах версиях Python

* Сбор ссылок на статьи о нововведениях в Python

* Скачивание актуальной документации

### Технологии

* Python

* Prettytable

* BeautifulSoup4

### Запуск проекта

1. Клонировать проект из репозитория:
`git clone git@github.com:WolfMTK/bs4_parser_pep.git`

2. Создать и активировать виртуальное окружение:

    * Для Linux: `python3 -m venv venv && . venv/bin/activate`

    * Для Windows: `python -m venv venv && . venv/Scripts/activate`

3. Установить зависимости: `pip install -r requirements.txt`

### Примеры команд

1. Помощь по командам: `python main.py -h`

2. Поиск текущих статусов PEP и запись в файл формата CSV: `python main.py pep -o file`

3. Скачивание архива с документацией: `python main.py download`

4. Поиск ссылок на страницы со статьями о нововведениях в Python и запись в файл формата CSV: `python main.py whats-new -o file`

5. Сбор информации о доступных версиях Python и запись в файл формата CSV: `python main.py latest-versions -o file`
