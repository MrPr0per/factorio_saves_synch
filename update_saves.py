import json
import yadisk
from colorama import Fore, Style
import colorama

from main import update_saves, SavesUpdateModes, Logger


def main():
    colorama.init()
    settings = json.loads(open('settings.json').read())
    yadisk_token = settings['yadisk_token']
    factorio_saves_path = settings['factorio_saves_path']

    logger = Logger()
    client = yadisk.Client(token=yadisk_token)
    if not client.check_token():
        logger.log_if_necessary('токен не валиден')
        return

    update_saves(SavesUpdateModes.upload_save, client, factorio_saves_path, logger)
    update_saves(SavesUpdateModes.download_save, client, settings['factorio_saves_path'], logger)

    client.close()

    print(Fore.GREEN)
    print('    нажми ентер, чтобы выйти')
    input('    > ')
    print(Style.RESET_ALL)


if __name__ == '__main__':
    main()
