import logging.config
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from settings import LOGGING_CONFIG

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_RETRY_TIME = 600

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Бот отправляет сообщение в чат."""
    logger.info('Бот отправляет сообщение в чат...')
    chat_id = TELEGRAM_CHAT_ID
    bot.send_message(chat_id, message)
    logger.info('Cообщение отправленно успешно')


def get_api_answer(current_timestamp):
    """Получаем ответ от сервера API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise requests.HTTPError('Ошибка при запросе к основному API, '
                                 f'статус ответа {response.status_code}')
    return response.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    logger.debug('Проверяем ответ API на корректность.')
    if not isinstance(response, dict):
        raise TypeError('ответ API не словарь')
    elif 'homeworks' not in response:
        raise ValueError('В ответе API нет ключа homeworks')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Домашние задания приходят не в виде списка')
    homeworks = response.get('homeworks')
    return homeworks


def parse_status(homework):
    """Извлекаем статус работы из ответа API."""
    logger.debug('Извлекаем статус работы из ответа API')
    if ('homework_name' or 'status') not in homework:
        raise KeyError('Ответ от API не содержит ключа '
                       'homework_name или status')
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(
            f'Неправильный статус работы {homework_status}'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Тест переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


CASHE = {'message': None, 'error': None}


def main():  # noqa: C901
    """Основная логика работы бота."""
    logger.debug('Проверяем переменные окружения на None...')
    if not check_tokens():
        logger.critical('Работа програмы завершена,'
                        ' т.к. нет переменных окружения', exc_info=True)
        sys.exit('Работа програмы завершена')
    logger.debug('Проверка переменных окружения прошла успешно')

    logger.debug('Инициализируем бота...')
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except telegram.error.InvalidToken as error:
        message = f'Сбой при инициализации бота: {error}'
        logger.critical(f'Работа програмы завершена: {message}',
                        exc_info=True)
        sys.exit('Работа програмы завершена')
    else:
        logger.debug('Инициализация бота прошла успешно')
    current_timestamp = int(time.time())

    while True:
        try:
            logger.debug('Отправляем запрос к API')
            response = get_api_answer(current_timestamp)
            logger.debug('Ответ от API получен успешно.')
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('Пустой список заданий, ждёмс!')
            else:
                logger.debug('Извлекаем статус задания...')
                message = parse_status(homeworks[0])
                if CASHE['message'] != message:
                    CASHE['message'] = message
                    send_message(bot, message)
                else:
                    logger.debug(f'Ответ не изменился: {message}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(message)
            if CASHE['error'] != message:
                CASHE['error'] = message
                send_message(bot, message)
        else:
            current_timestamp = response.get('current_date')
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == '__main__':
    main()
