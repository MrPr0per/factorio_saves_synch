import json
import subprocess
import sys
import time

import yadisk
from enum import Enum, auto
from colorama import Fore, Style
import colorama
import os
import datetime


class SavesUpdateModes(Enum):
    upload_save = auto()
    download_save = auto()


class PlayersUpdateModes(Enum):
    add_my_name = auto()
    del_my_name = auto()


class Settings:
    develop_mode = True

    yadisk_token = None
    factorio_exe_path = None
    factorio_saves_path = None


class Logger:
    def __init__(self, enable_logging=True, column_width=70):
        self.enable_logging = enable_logging
        self.column_width = column_width
        self.current_deep = 0

    def log_if_necessary(self, text, deep_delta=0, end='\n'):
        if not self.enable_logging: return

        if deep_delta < 0: self.current_deep += deep_delta
        print(('    ' * self.current_deep + text).ljust(self.column_width), end=end)
        sys.stdout.flush()  # без этого в терминале не отображаются строки, не заканчивающиеся переводом строки
        if deep_delta > 0: self.current_deep += deep_delta


def launch_factorio(factorio_exe_path, develop_mode):
    if develop_mode:
        process = subprocess.Popen(r'C:\Windows\system32\notepad.exe')
    else:
        process = subprocess.Popen(factorio_exe_path)
    process.wait()


def get_players_list(client: yadisk.Client, logger: Logger):
    logger.log_if_necessary('получение списка игроков онлайн...', end='')
    if client.exists('factorio/players_online.txt'):
        client.download("factorio/players_online.txt", "players_online.txt")
    players = list(map(lambda x: x.strip(), open('players_online.txt', 'r').readlines()))
    logger.log_if_necessary('готово')
    return players


def update_players_list(mode: PlayersUpdateModes, client: yadisk.Client, name: str, logger: Logger):
    logger.log_if_necessary('обновление списка игроков онлайн {', deep_delta=1)

    players = get_players_list(client, logger)

    if mode == PlayersUpdateModes.add_my_name:
        logger.log_if_necessary(f'готово: users_online = {players} + {name}')
        players.append(name)
    elif mode == PlayersUpdateModes.del_my_name:
        logger.log_if_necessary(f'готово: users_online = {players} - {name}')
        players.remove(name)
    else:
        raise Exception('указан неверный режим обновления списка игроков')

    logger.log_if_necessary('отправка нового списка на сервер...', end='')
    with open('players_online.txt', 'w') as file:
        file.write('\n'.join(players))
    if client.exists('/factorio/players_online.txt'):
        client.remove("/factorio/players_online.txt", permanently=True)
    client.upload("players_online.txt", "/factorio/players_online.txt")
    logger.log_if_necessary('готово')
    logger.log_if_necessary('} ок', deep_delta=-1)


def get_newest_local_save(factorio_saves_path):
    newest_save_filepath = None
    newest_save_datetime = None
    for filename in os.listdir(path=factorio_saves_path):
        filepath = os.path.join(factorio_saves_path, filename)

        save_datetime = os.path.getmtime(filepath)
        save_datetime = datetime.datetime.fromtimestamp(save_datetime)

        if newest_save_datetime is None or save_datetime > newest_save_datetime:
            newest_save_filepath = filepath
            newest_save_datetime = save_datetime

    # время в UTC
    newest_save_datetime += datetime.timedelta(seconds=time.timezone)
    tz = datetime.timezone(datetime.timedelta(seconds=0))
    newest_save_datetime = newest_save_datetime.replace(tzinfo=tz)

    return newest_save_filepath, newest_save_datetime


def get_newest_yadisk_save(client: yadisk.Client, logger: Logger):
    logger.log_if_necessary('получение даты и времени последнего сохранения на диске...', end='')

    if not client.exists('disk:/factorio/save_datetime.txt'):
        logger.log_if_necessary('на диске нет файла save_datetime.txt')
        return None, None

    client.download('disk:/factorio/save_datetime.txt', 'save_datetime.txt')

    save_datetime = datetime.datetime.strptime(open('save_datetime.txt', 'r').read(), "%Y-%m-%d %H:%M:%S.%f")
    tz = datetime.timezone(datetime.timedelta(seconds=0))
    save_datetime = save_datetime.replace(tzinfo=tz)

    files = client.get_files()
    for f in files:
        path = f['path']
        if path.startswith('disk:/factorio/') and path.endswith('.zip'):
            logger.log_if_necessary('готово')
            return path, save_datetime
    logger.log_if_necessary('на диске нет сохранений')
    return None, None


def update_saves(mode: SavesUpdateModes, client: yadisk.Client, factorio_saves_path, logger: Logger):
    logger.log_if_necessary('обновление сохранений {', deep_delta=1)
    local_filepath, local_datetime = get_newest_local_save(factorio_saves_path)
    yadisk_filepath, yadisk_datetime = get_newest_yadisk_save(client, logger)

    if mode == SavesUpdateModes.download_save:
        if yadisk_datetime is None or yadisk_datetime <= local_datetime:
            logger.log_if_necessary('скачивание не требуется')
        else:
            logger.log_if_necessary('скачивание сохраниения...', end='')
            filename = yadisk_filepath[yadisk_filepath.rfind('/') + 1:]
            client.download(yadisk_filepath, os.path.join(factorio_saves_path, filename))
            logger.log_if_necessary('готово')
    elif mode == SavesUpdateModes.upload_save:
        if yadisk_datetime is not None and local_datetime <= yadisk_datetime:
            logger.log_if_necessary('отгрузка не требуется')
        else:
            logger.log_if_necessary('отгрузка сохранения, не закрывайте программу...', end='')

            # отгружаем файл с датой и временем
            with open('save_datetime.txt', 'w') as f:
                f.write(local_datetime.strftime("%Y-%m-%d %H:%M:%S.%f"))
            if client.exists('factorio/save_datetime.txt'):
                client.remove('factorio/save_datetime.txt', permanently=True)
            client.upload('save_datetime.txt', 'factorio/save_datetime.txt')

            # отгружаем сам файл сохранения
            if yadisk_filepath is not None:
                client.remove(yadisk_filepath, permanently=True)
            local_filename = os.path.basename(local_filepath)
            client.upload(local_filepath, f'disk:/factorio/{local_filename}', timeout=9999)

            logger.log_if_necessary('готово')
    else:
        raise Exception(f'указан неверный режим обновления списка игроков: {mode}')
    logger.log_if_necessary('} ок', deep_delta=-1)


def main():
    # инициализация
    colorama.init()
    open('players_online.txt', 'w').close()
    open('save_datetime.txt', 'w').close()
    develop_mode = False
    settings = json.loads(open('settings.json').read())
    yadisk_token = settings['yadisk_token']
    factorio_exe_path = settings['factorio_exe_path']
    factorio_saves_path = settings['factorio_saves_path']
    name = f'{settings["name"]} ({datetime.datetime.now()})'

    logger = Logger()
    client = yadisk.Client(token=yadisk_token)
    if not client.check_token():
        logger.log_if_necessary('токен не валиден')
        return

    logger.log_if_necessary('start')
    players = get_players_list(client, logger)
    if len(players) > 0:  # если кто-то сейчас играет
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
        update_saves(SavesUpdateModes.download_save, client, factorio_saves_path, logger)

    update_players_list(PlayersUpdateModes.add_my_name, client, name, logger)
    launch_factorio(factorio_exe_path, develop_mode)
    update_players_list(PlayersUpdateModes.del_my_name, client, name, logger)
    update_saves(SavesUpdateModes.upload_save, client, factorio_saves_path, logger)
    client.close()
    logger.log_if_necessary('end')

    print(Fore.GREEN)
    print('    нажми ентер, чтобы выйти')
    input('    > ')
    print(Style.RESET_ALL)


if __name__ == '__main__':
    main()
