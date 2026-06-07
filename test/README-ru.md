# Тестовая директория MoneyPrinterTurbo

В этой директории содержатся юнит-тесты для проекта **MoneyPrinterTurbo**.

## Структура директории

- `services/`: тесты для компонентов в директории `app/services`  
  - `test_video.py`: тесты для видео-сервиса  
  - `test_task.py`: тесты для сервиса задач  
  - `test_voice.py`: тесты для сервиса синтеза речи  

## Запуск тестов

Вы можете запустить тесты, используя встроенный в Python фреймворк `unittest`:

```bash
# Запустить все тесты
python -m unittest discover -s test

# Запустить конкретный файл тестов
python -m unittest test/services/test_video.py

# Запустить конкретный тестовый класс
python -m unittest test.services.test_video.TestVideoService

# Запустить конкретный тестовый метод
python -m unittest test.services.test_video.TestVideoService.test_preprocess_video
```

## Добавление новых тестов

При добавлении тестов для других компонентов следуйте этим рекомендациям:

1. Создавайте файлы тестов с префиксом `test_` в соответствующей поддиректории.
2. Используйте `unittest.TestCase` в качестве базового класса для ваших классов тестов.
3. Называйте методы тестов с префиксом `test_`.

## Ресурсы для тестов

Помещайте любые файлы ресурсов, необходимые для тестирования, в директорию `test/resources`.
