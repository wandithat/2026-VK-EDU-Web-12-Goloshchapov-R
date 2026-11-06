# 2026-VK-EDU-Web-12-Goloshchapov-R

Учебный проект курса VK Education Web.

- **ДЗ1** — статическая верстка сайта вопросов и ответов (AskRoman) без бэкенда: папка `public/`.
- **ДЗ2** — тот же сайт на Django: views, маршрутизация, шаблонизация, пагинация, окружение для запуска (venv и Docker).

## Запуск проекта (ДЗ2, Django)

Есть два равноценных способа — выбери любой.

### Вариант А — локально через venv

1. Создай и активируй виртуальное окружение:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
2. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируй `.env.example` в `.env` и при желании поправь значения:
   ```bash
   cp .env.example .env
   ```
4. Накати миграции и запусти сервер:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
5. Открой [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### Вариант Б — через Docker Compose

1. Скопируй `.env.example` в `.env` (без него контейнер не найдёт переменные окружения):
   ```bash
   cp .env.example .env
   ```
2. Собери и запусти:
   ```bash
   docker compose up --build
   ```
3. Открой [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Код проекта смонтирован в контейнер как volume — изменения в файлах на хосте сразу видны внутри контейнера без пересборки образа. Файлы, загруженные в `media/`, хранятся в отдельном named volume и не теряются при `docker compose up --build`.

## Переменные окружения

Все нужные переменные перечислены в `.env.example` с безопасными заглушками вместо реальных секретов:

| Переменная | Назначение |
|---|---|
| `DJANGO_SECRET_KEY` | секретный ключ Django |
| `DJANGO_DEBUG` | `True`/`False`, режим отладки |
| `DJANGO_ALLOWED_HOSTS` | список разрешённых хостов через запятую |

Файл `.env` в репозиторий не коммитится (см. `.gitignore`), `.env.example` — коммитится.

## Страницы и маршруты (Django, ДЗ2)

| URL | Шаблон | Описание |
|---|---|---|
| `/` | `questions/index.html` | Список новых вопросов |
| `/hot/` | `questions/hot.html` | Список популярных вопросов |
| `/tag/<tag_name>/` | `questions/tag.html` | Список вопросов по тегу |
| `/question/<id>/` | `questions/question.html` | Страница одного вопроса со списком ответов |
| `/ask/` | `questions/ask.html` | Форма добавления вопроса |
| `/login/` | `core/login.html` | Форма входа |
| `/signup/` | `core/signup.html` | Форма регистрации |
| `/profile/` | `core/profile.html` | Форма редактирования профиля |

На этом этапе views отдают тестовые данные-заглушки, без реальной БД.

## Статическая верстка (ДЗ1)

Чистые HTML-файлы без шаблонизатора, в папке `public/` — открываются напрямую в браузере (`public/index.html`), сервер не нужен. Подробности — в истории ДЗ1.

## Структура проекта

```
AskRoman/              — настройки Django-проекта (settings.py, urls.py)
core/                  — приложение: вход, регистрация, профиль
questions/             — приложение: вопросы, ответы, пагинация
static/                — исходная статика (css/js/img), подключается STATICFILES_DIRS
staticfiles/           — результат collectstatic (не коммитится)
media/                 — загруженные пользователем файлы (не коммитится)
public/                — статическая верстка ДЗ1
requirements.txt       — зависимости Python
.env.example           — список нужных переменных окружения (без секретов)
Dockerfile             — образ для запуска Django-приложения
docker-compose.yml     — запуск сервиса web через Docker Compose
```
