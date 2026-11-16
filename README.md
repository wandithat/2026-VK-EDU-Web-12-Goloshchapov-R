# 2026-VK-EDU-Web-12-Goloshchapov-R

Учебный проект курса VK Education Web. ДЗ1 — статическая верстка сайта вопросов и ответов (AskRoman), без бэкенда.

## Как открыть верстку

Верстка представляет собой обычные HTML-файлы без шаблонизатора и без сборки — сервер не нужен.

1. Склонируйте репозиторий.
2. Откройте `public/index.html` в браузере.

Все стили и скрипты подключены локально из `public/static/`, интернет не требуется.

## Страницы

| Файл | Описание |
|---|---|
| `public/base.html` | Общий layout (header/main/sidebar/footer), на основе которого сделаны остальные страницы |
| `public/index.html` | Список вопросов |
| `public/question.html` | Страница одного вопроса со списком ответов |
| `public/ask.html` | Форма добавления вопроса |
| `public/login.html` | Форма входа |
| `public/signup.html` | Форма регистрации |
| `public/profile.html` | Страница настроек профиля |

Страницы `hot.html` и `tag.html` не реализованы — по заданию они прорабатываются в ДЗ2.

## Структура

```
public/
├── base.html
├── index.html
├── question.html
├── ask.html
├── login.html
├── signup.html
├── profile.html
└── static/
    ├── css/      — Bootstrap и собственные стили
    ├── js/       — Bootstrap JS
    └── img/      — favicon, аватарки-заглушки
```