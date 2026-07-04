# FastAPI_template

Это шаблон использования FastAPI для создания restAPI

Для установки необходимо выполнить следующие команды

`pip install -r requirements.txt`

`fastapi dev`

Для загрузки тестовых данных написать 

`python seed.py`

для защиты маршрута нужно добавить `username=Depends(auth_handler.auth_wrapper)` в входные аргументы маршрута

после можно открывать автоматическую документацию

`127.0.0.1:8000/docs`