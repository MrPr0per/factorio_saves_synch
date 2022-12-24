import subprocess
import time

import yadisk
from enum import Enum, auto
from colorama import Fore, Style
import os
import datetime

# ПРЕДУПРЕЖДЕНИЕ: в сохранении файла нельзя использовать слово date и квадратные скобки []!
name = 'your_name'
factorio_launch_path = r'C:\Games\Factorio\bin\x64\factorio.exe'
factorio_saves_path = r'C:\Users\admin\AppData\Roaming\Factorio\saves'
yadisk_token = 'your_token'


class UpdateModes(Enum):
    add_my_name = auto()
    del_my_name = auto()

    upload_save = auto()
    download_save = auto()


def colored(text, color):
    return color + text + Style.RESET_ALL


def launch_factorio():
    if develop_mode:
        note = subprocess.Popen(r'C:\Windows\system32\notepad.exe')
    else:
        note = subprocess.Popen(factorio_launch_path)
    note.wait()


def get_players_list():
    if logging: print('получение списка игроков онлайн...'.ljust(column_width), end='')
    ycloud_manager.download("/factorio/players_online.txt", "players_online.txt")
    with open('players_online.txt', 'r') as file:
        players = list(map(lambda x: x.strip(), file.readlines()))
    if logging: print('готово')
    return players


def update_players_list(mode):
    if logging: print('обновление списка игроков онлайн {')
    if logging: print('получение списка...'.ljust(column_width), end='')
    ycloud_manager.download("/factorio/players_online.txt", "players_online.txt")
    with open('players_online.txt', 'r') as file:
        players = list(map(lambda x: x.strip(), file.readlines()))
    if mode == UpdateModes.add_my_name:
        if logging: print(f'готово: users_online = {players} + {name}')
        players.append(name)
    elif mode == UpdateModes.del_my_name:
        if logging: print(f'готово: users_online = {players} - {name}')
        players.remove(name)
    else:
        raise Exception('указан неверный режим обновления списка игроков')
    if logging: print('отправка нового списка на сервер...'.ljust(column_width), end='')
    with open('players_online.txt', 'w') as file:
        file.write('\n'.join(players))
    ycloud_manager.remove("/factorio/players_online.txt", permanently=True)
    ycloud_manager.upload("players_online.txt", "/factorio/players_online.txt")
    if logging: print('готово')
    if logging: print('} ок')


def get_newest_local_save():
    newest_file = None
    tz = datetime.timezone(datetime.timedelta(seconds=0))
    for f in os.listdir(path=factorio_saves_path):
        path = f'{factorio_saves_path}/{f}'
        if 'date=' in f:
            d = f[f.find('[') + 1:f.find(']')]
            d = datetime.datetime.strptime(d, "%Y-%m-%d %H-%M-%S")
        else:
            d = os.path.getctime(path)
            d = time.ctime(d)
            d = datetime.datetime.strptime(d, '%a %b %d %H:%M:%S %Y')
            d += datetime.timedelta(seconds=time.timezone)
        if newest_file is None or d > newest_file[1]:
            newest_file = [path, d]
    newest_file[1] = newest_file[1].replace(tzinfo=tz)
    return newest_file


def get_newest_yadisk_save():
    if logging: print('получение даты последнего сохранения на диске...'.ljust(column_width), end='')
    files = ycloud_manager.get_files()
    for f in files:
        path = f['path']
        filename = path[path.rfind('/') + 1:]
        if path.startswith('disk:/factorio/') and path.endswith('.zip'):
            if 'date=' in filename:
                d = filename[filename.find('[') + 1:filename.find(']')]
                d = datetime.datetime.strptime(d, "%Y-%m-%d %H-%M-%S")
                tz = datetime.timezone(datetime.timedelta(seconds=0))
                d = d.replace(tzinfo=tz)
            else:
                d = ycloud_manager.get_meta(path)['created']
            if logging: print('готово')
            return path, d
    if logging: print('на диске нет сохранений')
    return None, None


def update_saves(mode):
    if logging: print('обновление сохранений {')
    local_path, local_date = get_newest_local_save()
    disk_path, disk_date = get_newest_yadisk_save()
    if mode == UpdateModes.download_save:
        if logging: print('скачивание сохраниения...'.ljust(column_width), end='')
        if disk_date is not None and local_date < disk_date:
            filename = disk_path[disk_path.rfind('/') + 1:]
            if 'date=' not in filename:
                new_filename = f'{filename[:filename.find(".")]} (date=[{disk_date.strftime("%Y-%m-%d %H-%M-%S")}]){filename[filename.find("."):]}'
            else:
                new_filename = filename
            ycloud_manager.download(disk_path, rf"{factorio_saves_path}\{new_filename}")
            if logging: print('готово')
        else:
            if logging: print('скачивание не требуется')
    elif mode == UpdateModes.upload_save:
        if logging: print('отгрузка сохраниения, не закрывайте программу...'.ljust(column_width), end='')
        if disk_date is None or local_date > disk_date:
            if disk_date is not None:
                old_disk_filename = disk_path[disk_path.rfind('/') + 1:]
                ycloud_manager.remove(f"/factorio/{old_disk_filename}", permanently=True)
            filename = local_path[local_path.rfind('/') + 1:]
            if 'date=' not in filename:
                new_filename = f'{filename[:filename.find(".")]} (date=[{local_date.strftime("%Y-%m-%d %H-%M-%S")}]){filename[filename.find("."):]}'
            else:
                new_filename = filename
            ycloud_manager.upload(local_path, f'disk:/factorio/{new_filename}')
            if logging: print('готово')
        else:
            if logging: print('отгрузка не требуется')
    else:
        raise Exception('указан неверный режим обновления списка игроков')
    if logging: print('} ок')


develop_mode = False
logging = True
column_width = 50
ycloud_manager = yadisk.YaDisk(token=yadisk_token)

if logging: print('start')
players = get_players_list()
if len(players) > 0:  # если кто то сейчас играет
    print(Fore.GREEN)
    print(f'    в данный момент играют: {players}')
    print(f'    запусти хамачи и нажми тут ентер (чтобы запустить факторио и синхронизировать данные)')
    print(f'    (и не забудь сохраниться перед выходом из игры)')
    input(f'    > ')
    print(Style.RESET_ALL)
else:
    print(Fore.GREEN)
    print(f'    в данный момент никто не играет')
    print(Style.RESET_ALL)
    update_saves(UpdateModes.download_save)

update_players_list(UpdateModes.add_my_name)
launch_factorio()
update_players_list(UpdateModes.del_my_name)
update_saves(UpdateModes.upload_save)
if logging: print('end')

print(Fore.GREEN)
print('    нажми ентер, чтобы выйти')
input('    > ')
print(Style.RESET_ALL)
