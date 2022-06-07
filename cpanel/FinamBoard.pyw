# python -m pyqtgraph.examples
import PySimpleGUI as sg
import redis as rd
import msgpack
import time
import config

_redis = None


def redis():
    global _redis
    try:
        _redis.ping()
    except (ConnectionError, ConnectionRefusedError, AttributeError):
        _redis = rd.from_url(config.REDIS_URL)
    return _redis


redis()

sg.theme('Default1')

layout = [
    [sg.B('Connect', key='btnConnect'), sg.B('Disconnect', key='btnDisconnect'), sg.B('Server shutdown', key='btnExit'),
     sg.B('Time elapsed', key='btnTimeElapsed')],
    [sg.Text('secCode', size=(8, 1)), sg.InputText('GAZP', key='seccode')],
    [sg.Text('Channel', size=(8, 1)), sg.Combo("alltrades quotations quotes".split(
    ), key='cbChannel', default_value='quotations', readonly=True, size=(10, 1))],
    [sg.Button('Subscribe', key='btnSub'),
     sg.Button('Unsubscribe', key='btnUnsub')]
]

window = sg.Window(f'FINAM DASHBOARD', layout, icon='res/kb.ico')

stream = f'{config.STREAM_ROOT}:streams:server'

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:  # if user closes window
        break

    if event == 'btnConnect':
        s = msgpack.packb({'fn': 'connect'})
        redis().rpush(stream, s)

    if event == 'btnDisconnect':
        redis().rpush(stream, msgpack.packb({'fn': 'disconnect'}))

    if event == 'btnExit':
        redis().rpush(stream, msgpack.packb({'fn': 'exit'}))

    if event == 'btnSub':
        channel = values['cbChannel']
        redis().rpush(stream, msgpack.packb({
            'fn': 'subscribe', 'seccode': values['seccode'], 'board': 'TQBR', 'channel': channel}))

    if event == 'btnUnsub':
        channel = values['cbChannel']
        redis().rpush(stream, msgpack.packb({
            'fn': 'unsubscribe', 'seccode': values['seccode'], 'board': 'TQBR', 'channel': channel}))

    if event == 'btnTimeElapsed':
        for i in range(1000):
            _redis.rpush(stream, msgpack.packb(
                {'fn': 'dt', 't': time.time_ns()}))
        _redis.rpush(stream, msgpack.packb({'fn': 'dt_end'}))

window.close()
