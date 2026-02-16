.PHONY: install test lint run clean

# Установка зависимостей
install:
	poetry install

# Запуск тестов
test:
	poetry run pytest tests/ -v --cov=. --cov-report=html

# Линтинг
lint:
	poetry run ruff check .

# Форматирование
format:
	poetry run ruff check --fix .

# Запуск приложения
run:
	poetry run python main.py

# Очистка
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
