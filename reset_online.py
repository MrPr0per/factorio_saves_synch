import yadisk

yadisk_token = '_'


def load_settings():
    global yadisk_token
    with open('settings.txt', 'r') as file:
        for line in file.readlines():
            var, value = map(lambda x: x.strip(), line.split('='))
            value = eval(value)
            if var == 'yadisk_token':
                yadisk_token = value


load_settings()
ycloud_manager = yadisk.YaDisk(token=yadisk_token)
print('отправка нового списка на сервер...', end=' ')
with open('players_online.txt', 'w') as file:
    file.write('')
ycloud_manager.remove("/factorio/players_online.txt", permanently=True)
ycloud_manager.upload("players_online.txt", "/factorio/players_online.txt")
print('готово')
