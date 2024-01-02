import json
import yadisk
from colorama import Fore, Style
import colorama

from main import Logger


def main():
    colorama.init()
    settings = json.loads(open('settings.json').read())
    yadisk_token = settings['yadisk_token']

    logger = Logger()
    client = yadisk.Client(token=yadisk_token)
    if not client.check_token():
        logger.log_if_necessary('токен не валиден')
        return

    logger.log_if_necessary('отправка нового списка на сервер...', end='')
    with open('players_online.txt', 'w') as file:
        file.write('')
    if client.exists('/factorio/players_online.txt'):
        client.remove("/factorio/players_online.txt", permanently=True)
    client.upload("players_online.txt", "/factorio/players_online.txt")
    logger.log_if_necessary('готово')

    client.close()

    print(Fore.GREEN)
    print('    нажми ентер, чтобы выйти')
    input('    > ')
    print(Style.RESET_ALL)


if __name__ == '__main__':
    main()