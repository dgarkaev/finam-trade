"""
Файл конфигурации
"""
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.
import os

# REDIS
REDIS_URL = os.getenv('REDIS_URL')
STREAM_ROOT= os.getenv('STREAM_ROOT')
# FINAM
FINAM_IP = 'tr1.finam.ru'
FINAM_PORT = 3900

# ACCOUNT
FINAM_LOGIN = os.getenv('FINAM_LOGIN')
FINAM_PASS = os.getenv('FINAM_PASS')

################################################################################################
# XML MSG FROM MOEX
#
# Обрабатывать только выбранные сообщения
moex_msg_filter_enable = True

# список обрабатываемых сообщений
moex_msgs = [
    # 4. Список возможных сообщений, передаваемых CallBack функции
    ##
    # b'candles',         # 4.1 Исторические данные
    b'server_status',   # 4.2 Состояние сервера
    # b'overnight',
    # b'client',          # 4.3 Клиентские счета
    # b'markets',         # 4.4 Доступные рынки
    # b'candlekinds',     # 4.5 Информация о доступных периодах свечей
    # b'securities',      # 4.6 Список инструментов
    # b'sec_info',        # 4.7 Информация по инструменту
    # b'sec_info_upd',    # 4.8 Обновление информации по инструменту
    b'quotations',      # 4.9 Котировки по инструменту(ам)
    b'alltrades',       # 4.10 Сделки по инструменту(ам)
    b'quotes',          # 4.11 Глубина рынка по инструменту(ам)
    # b'orders',          # 4.12 Заявка(и) клиента
    # b'trades',          # 4.13 Сделка(и) клиента
    # b'positions',       # 4.14 Позиции клиента
    # b'clientlimits',    # 4.15 Лимиты клиента на срочном рынке
    # b'portfolio_tplus',  # 4.16 Клиентский портфель Т+
    # b'marketord',       # 4.17 Возможность  рыночных заявок
    # b'ticks',           # 4.18 Тиковые данные
    # b'boards',          # 4.19 Справочник режимов торгов
    # b'pit seccode',     # 4.20 Параметры инструмента в режиме торгов
    # b'max_buy_sell_tplus client',   # 4.21 Максимальная покупка/продажа для Т+
    # b'messages',        # 4.22 Текстовые сообщения
    b'error',           # 4.23 Возможные ошибки
    # b'united_portfolio',# 4.24 Клиентский единый портфель
    # b'united_equity',   # 4.25 Актуальная оценка ликвидационной стоимости Единого портфеля
    # b'united_go',       # 4.26 Размер средств, заблокированных биржей (FORTS) под срочные позиции клиентов юниона
    # b'union',           # 4.27 Юнионы, находящиеся в управлении клиента

    # 5. Получение новостей в TXmlConnector
    ##

    # 5.2 Список возможных сообщений, передаваемых callback функции
    ##
    # b'current_server',  # 5.2.1 Идентификатор сервера
    b'news_header',     # 5.2.2 Заголовок новости
    # b'news_body',       # 5.2.3 Тело новости
]
