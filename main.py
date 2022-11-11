import requests as req
import os
from sys import getsizeof
from re import findall
from datetime import datetime as dt

# Создание директории.
os.mkdir("tasks") if not os.path.isdir("tasks") else ...

# Загрузка данных в оперативную память
proxies = {'http': ''}
users = req.get('https://json.medrocket.ru/users', proxies=proxies).json()
todos = req.get('https://json.medrocket.ru/todos', proxies=proxies).json()

# Цикл обхода пользователей
for user in users:
    countDone, countNotDone = 0, 0
    tasksDone, tasksNotDone = str(), str()
    # Цикл обхода задач
    for todo in todos:
        # Выборка и фиксирование данных по пользователю
        if user.get('id') == todo.get('userId'):
            if todo.get('completed'):
                countDone += 1
                if len(todo.get("title")) < 46:
                    tasksDone += '- ' + todo.get("title") + '\n'
                else:
                    tasksDone += '- ' + todo.get("title")[:46] + '…\n'
            else:
                countNotDone += 1
                if len(todo.get("title")) < 46:
                    tasksNotDone += '- ' + todo.get("title") + '\n'
                else:
                    tasksNotDone += '- ' + todo.get("title")[:46] + '…\n'

    # Проверка на необходимость архивирования нынешнего отчета по пользователю
    if os.path.isfile('tasks/' + user.get('username') + '.txt'):
        try:
            with open('tasks/' + user.get('username') + '.txt') as old_file:
                old_time = findall(r'\d\d.\d\d.\d\d\d\d \d\d:\d\d', old_file.readlines()[1])[0]
        except OSError:
            print("Непредвиденная ошибка при чтении старого отчета!")
            continue

        # В случае, если архивирование необходимо и были получены нужные данные, происходит проверка на давность
        # составления актуального отчета. Если скрипт будет запущен более одного раза в минуту, возможна ситуация, когда
        # архивируемые файлы будут иметь одинаковые имена. Во избежание этого можно было бы, например, дополнить
        # форму отчета указанием секунды его составления, но таким образом мы позволим пользователю "захламлять" рабочую
        # директорию лишними отчетами (в задаче не указаны варианты использования отчетов, но я полагаю, что
        # ожидание минуты не станет критичным), тем самым ухудшая навигацию по директории.
        if old_time == dt.now().strftime("%d.%m.%Y %H:%M"):
            print(f'Для {user.get("username")} не был создан отчет на дату: {old_time}, так как на эту'
                  f' дату уже был составлен отчет. Дождитесь изменения даты хотя бы на минуту от текущей и повторите '
                  f'попытку!')
            continue

        # Трансформирование формата времени из файла отчета в формат названия архивируемых отчетов
        t_time = ('-'.join(old_time.split()[0].split('.')[::-1]) + 'T' + old_time.split()[1])

        # Блок проверки длины названия архивируемого файла. Возможна ситация, когда актуальный отчет был создан
        # для пользователя, у которого username достаточно длинный, что при добавлении префикса old и даты к никнейму,
        # общая длина имени файла превысит 255 байт, что не позволено системой.
        if not os.path.isfile(old_file_path := f'tasks/Old_{user.get("username")}_{t_time}.txt'):
            if getsizeof(old_file_path) <= 255:
                os.rename(f'tasks/{user.get("username")}.txt',
                          f'tasks/Old_{user.get("username")}_{t_time}.txt')
            else:
                print(f'Не удалось архивировать устаревший отчет для {user.get("username")},'
                      f' поскольку название устаревшего отчета слишком велико!'
                      f'Актуальный отчет не изменен!')
                continue

    # Подготовка контента для записи в актуальный отчет. В случае, если задач у пользователя нет вместо стандартного
    # шаблона заполнения задач я решил вставить одну строку f'\n## Задачи отсутствуют'. Это, на мой взгляд, малость
    # удобнее и экономит (пусть и немного) дисковое пространство.
    actual_file_content = (f'# Отчёт для {user.get("company").get("name")}.\n'
                           f'{user.get("name")} <{user.get("email")}> {dt.now().strftime("%d.%m.%Y %H:%M")}\n'
                           + (f'Всего задач: {countNotDone + countDone}\n\n'
                              f'## Актуальные задачи ({countNotDone}):\n'
                              f'{tasksNotDone}\n'
                              f'## Завершённые задачи ({countDone}):\n{tasksDone}',
                              f'\n## Задачи отсутствуют')[countNotDone + countDone == 0])

    # Попытка записи
    try:
        with open(f'tasks/{user.get("username")}.txt', 'w') as actual_file:
            actual_file.write(actual_file_content)
    except OSError:
        print('Непредвиденная ошибка записи актуального отчета!')

# В случае полностью успешной работы программы, на консоль ничего не выводится.
