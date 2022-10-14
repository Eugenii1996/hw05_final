# Yatube social network

### Разработчик:

 - [Мирошниченко Евгений](https://github.com/Eugenii1996)

### О проекте:

Проект Yatube представляет собой социальную сеть, в которой пользователи имеют возможность создать учетную запись, публиковать записи, подписываться на любимых авторов и отмечать понравившиеся записи.  
Стек технологий:
 - Django 2.2.16
 - Gunicorn 20.0.4

### Клонировать репозиторий c GitHub:

```bash
git clone git@github.com:Eugenii1996/hw05_final.git
```

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
