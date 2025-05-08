### О проекте

Foodgram — это платформа для любителей кулинарии, где пользователи могут:

- Делиться своими рецептами

- Сохранять понравившиеся рецепты в избранное

- Подписываться на других авторов

- Формировать список покупок для выбранных блюд

### Используемые технологии

Django
PostgreSQL
React
Nginx
Docker
GitHub Actions

### Запуск проекта через Docker-compose через bash скрипт

выделяем права скрипту
```bash
chmod +x init-backend-data.sh
```

запускаем скрипт
```bash
./init-backend-data.sh
```


### Запуск проекта через Docker-compose вручную

Запускаем сборку контейнеров проекта

```bash
docker compose up -d --build
```

Собираем статику Django

```bash
docker compose exec backend python manage.py collectstatic
```

Запуск миграций

```bash
docker compose exec backend python manage.py migrate
```

Загрузите данные

```bash
docker compose exec backend python manage.py loaddata data/domain.json
```

Создайте суперюзера

```bash
docker compose exec backend python manage.py createsuperuser
```



### Локальная установка (только backend)

Склонируйте репозиторий:

```bash
git clone https://github.com/GitIlgar/foodgram-st.git
cd foodgram-st/backend
```

Создайте и активируйте виртуальное окружение:

```bash
python -m venv env
source ./env/bin/activate  # Для Windows: env\Scripts\activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

Примените миграции:

```bash
python manage.py migrate
```

Создайте администратора:

```bash
python manage.py createsuperuser
```

Загрузите статические файлы:

```bash
python manage.py collectstatic --no-input
```

Заполните базу тестовыми данными:

```bash
python manage.py loaddata test_data.json
```

Запустите сервер:

```bash
python manage.py runserver
```

Этих действий достаточно для тестирования API через Postman. По умолчанию используется SQLite3 и режим DEBUG.

### Полноценный запуск проекта

Для работы всего сервиса потребуются:

- Фронтенд

- База данных PostgreSQL

- Nginx в качестве прокси-сервера

Предварительные шаги:

- Установите Docker

- На Linux потребуется установть Docker Compose

- Создайте файл .env в корне проекта:

```
SECRET_KEY="ваш_секретный_ключ"
DB_ENGINE=django.db.backends.postgres
DB_NAME=db
POSTGRES_USER=user
POSTGRES_PASSWORD=123456
DB_HOST=db
DB_PORT=5432
DEBUG=True
```

- Запуск контейнеров:

```bash
docker compose up -d --build
```

После сборки будут созданы 4 контейнера:

infra-nginx-1 — веб-сервер
infra-db-1 — база данных
infra-backend-1 — Django-приложение
infra-frontend-1 — React-приложение

Для проверки:

```bash
docker container ls -a
```

### Настройка приложения:

Примените миграции:

```bash
docker compose exec backend python manage.py migrate
```

Создайте администратора:

```bash
docker compose exec backend python manage.py createsuperuser
```

Импортируйте тестовые данные:

```bash
docker compose exec backend python manage.py loaddata test_data.json
```

Соберите статику:

```bash
docker compose exec backend python manage.py collectstatic --no-input
```

Доступные адреса

```bash
127.0.0.1 — главная страница

127.0.0.1/admin — админ-панель

127.0.0.1/api/docs/ — документация API
```
