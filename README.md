# Bender Rodriguez

## Установка
1. Создать .env
```
COMPOSE_PROJECT_NAME=bender
```
2. Собрать проект
```
docker compose build
docker compose up -d

[//]: # (docker exec -it bender ./manage.py migrate)
docker compose run --rm django ./manage.py migrate

```

## PostgresDB
```
docker restart bender_postgres
```
```
docker exec -i bender_postgres su postgres -c "dropdb -U bender bender"
```
```
docker exec -i bender_postgres su postgres -c "createdb -U bender -O bender bender"
```

## Linters
```
docker-compose run -T --rm django isort . --df --check-only
docker-compose run -T --rm django black -S -l 79 --target-version py38 . --check --diff
docker-compose run -T --rm django flake8
```
