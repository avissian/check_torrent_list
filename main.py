import logging
import os
import re
from logging import handlers
from os.path import exists

import requests
import yaml


def main():
    hashes_name = 'hashes.yml'
    msg = []
    # создаём файл с хешами, если его нет
    if not exists(hashes_name):
        with open(hashes_name, 'w') as f:
            f.write('')

    # читаем конфиг
    with open('config.yml') as f:
        config = yaml.safe_load(f)
    list_ids = []
    # читаем список раздач из файла
    with open('list.txt', 'r') as f:
        for line in f.readlines():
            id = line.rstrip().split(' ')[0]
            list_ids.extend(re.findall(r'\d+', id))

    # собираем параметры для запроса к API
    params = {'by': 'topic_id',
              'val': ','.join(list_ids)}
    if config.get('api_key'):
        params['api_key'] = config.get('api_key')
    # запрос
    response = requests.get('http://api.t-ru.org/v1/get_tor_hash', params)
    json_resp = response.json()['result']

    # читаем файл хешей
    with open(hashes_name) as f:
        hashes = yaml.safe_load(f) or {}
    # сравниваем ответ API с файлом сохранённых хешей
    for id in json_resp:
        logger.info(f'Сравниваем для id={id} {hashes.get(id)}-{json_resp[id]}')
        if hashes.get(id) != json_resp[id]:
            logger.info('отличается')
            msg.append(f'Изменился хеш раздачи https://rutracker.org/forum/viewtopic.php?t={id}')

    # если хоть один хеш не совпал
    if len(msg) > 0:
        # пробуем отправить сообщение
        params = {'chat_id': config.get('telegram_user_id'),
                  'text': '\n'.join(msg)}
        if config.get('bot_token'):
            response = requests.get(f'https://api.telegram.org/bot{config.get("bot_token")}/sendMessage', params)
        else:
            response = requests.get('https://bot.keeps.cyou/PlanB', params)

        # обновляем файл с хешами только если отправилось сообщение
        if response.status_code == 200:
            # сохраняем файл хешей (для будущих запусков)
            with open(hashes_name, 'w') as f:
                f.write(yaml.dump(json_resp))


if __name__ == '__main__':
    try:
        os.mkdir('./logs')
    except FileExistsError:
        pass

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = handlers.TimedRotatingFileHandler(filename="./logs/check.log",
                                                when='D',  # ежедневное создание нового файла
                                                backupCount=7,  # хранить 7 старых версий (7 дней)
                                                encoding="utf-8")
    formatter = logging.Formatter(u'%(filename)-10.10s[Ln:%(lineno)-4d]%(levelname)-8s[%(asctime)s]|%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Strated")
    main()
