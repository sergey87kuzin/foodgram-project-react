IP адрес сервера http://84.252.137.101

foodgram - проект, который позволяет обмениваться рецептами и составлять на основе выбранных список покупок

для доступа к созданию, выбору рецептов необходима идентификация.

проект учебный. работа над ним закрепила навыки работы с Django Rest Framework, Django-filters,
идентификацией пользователей

К проекту по адресу api/redoc/ подключена документация API YaMDb. В ней описаны возможные запросы
к API и структура ожидаемых ответов.

для того, чтобы развернуть приложение, необходимо из папки Infra/ выполнить команду docker-compose up:
будут сформированы необходимые контейнеры.

затем необходимо выполнить миграции командами
docker-compose exec web python3 manage.py makemigrations
docker-compose exec web python3 manage.py migrate --run-syncdb

для создания суперпользователя используйте docker-compose exec web python manage.py createsuperuser

подтянуть статику можно командой docker-compose exec web python3 manage.py collectstatic --no-input

если есть необходимость в начальном заполнении БД, выполните команду
docker-compose exec web python3 manage.py loaddata recipes3.json

образ доступен по имени 'greytres/final:latest'
