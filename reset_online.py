import yadisk

yadisk_token = 'your_token'

ycloud_manager = yadisk.YaDisk(token=yadisk_token)
print('отправка нового списка на сервер...', end=' ')
with open('players_online.txt', 'w') as file:
    file.write('')
ycloud_manager.remove("/factorio/players_online.txt", permanently=True)
ycloud_manager.upload("players_online.txt", "/factorio/players_online.txt")
print('готово')
