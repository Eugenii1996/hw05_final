# Социальная сеть Yatube

### Разработчик:

 - [Мирошниченко Евгений](https://github.com/Eugenii1996)

### О проекте:

Проект Yatube представляет собой социальную сеть, в которой пользователи имеют возможность создать учетную запись, публиковать записи, подписываться на любимых авторов и отмечать понравившиеся записи.  
Стек технологий:
 - Python 3
 - Django
 - Unittest
 - SQLite3
 - Git
 - Pytest

### Клонирование репозитория и переход в него в командной строке:

```bash
git clone git@github.com:Eugenii1996/hw05_final.git
```

```bash
cd hw05_final
```

### Cоздать и активировать виртуальное окружение:

Виртуальное окружение должно использовать Python 3.7

```bash
pyhton -m venv venv
```

* Если у вас Linux/MacOS

    ```bash
    source venv/bin/activate
    ```

* Если у вас windows

    ```bash
    source venv/scripts/activate
    ```

### Установка зависимостей из файла requirements.txt:

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt

После клонирования необходимо установить окружение находясь в корневой директории:

```bash
pyhton -m venv venv
```

Активировать виртуальное окружение (для Windows):

```bash
source venv/Scripts/activate
```

Далее нужно обновить менеджер пакетов pip и установить зависимости:

```bash
pip install -r requirements.txt
```

### Создание миграций:

При активированном виртуальном окружении выполнить команды:

```bash
python manage.py makemigrations
```
```bash
python manage.py migrate
```

### Запуск сервера разработчика:

Из корневой директории при активированном виртуальном окружении выполнить команду:
```bash
python manage.py runserver
```
