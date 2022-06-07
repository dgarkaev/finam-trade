from abc import abstractmethod
import time
import redis as rd

import transaq.xconnector as tc
import config
# import sqlite3
import msgpack
import inspect


class xmlStreams():
    """ Базовый класс для сообщений от биржи"""
    def __init__(self) -> None:
        self.stream_root=config.STREAM_ROOT

    def connect(self, **_):
        raise NotImplementedError()
        # raise NotImplementedError('%s.%s()' % ( self.__class__.__name__, inspect.currentframe().f_code.co_name))

    def add(self, key: str, value):
        raise NotImplementedError()

    def read(self, key: str):
        raise NotImplementedError()


class xmlStreamsRedis(xmlStreams):
    """ Очередь через Redis """

    def __init__(self) -> None:
        super().__init__()
        self.redis = rd.from_url(config.REDIS_URL)
        # self.redis = StrictRedis(
        #     host=redis_ip, port=redis_port)

    def add(self, key: str, value):
        key=f'{self.stream_root}:{key}'
        return self.redis.xadd(key, value)

    def read(self, key: str):
        key=f'{self.stream_root}:{key}'
        rz = self.redis.lpop(key)
        return rz


class xmlStreamsSqlite3(xmlStreams):
    """ Очередь через Sqlite3 """

    def __init__(self) -> None:
        ...

    def connect(self, **_):
        ...


class xmlStreamQuery(xmlStreams):
    """ Очередь через Python Query """

    def __init__(self) -> None:
        ...

########################################################################################################


class fserverL0():
    """
    Принимаем команды от биржи и складываем их в stream
    """

    def __init__(self, xmlStream: xmlStreams):
        self.xmlStream = xmlStream
#         self.redis.hset('server:server_status', 'initialize', self.initialize)
#         self.sqlite=sqlite3.connect("file::memory:?cache=shared", uri=True)
#         self.cursor = self.sqlite.cursor()
#         self.cursor.executescript("""
#         CREATE TABLE IF NOT EXISTS news_header(
#             dt default (strftime('%s.%f', 'now')), dt2 TIMESTAMP
#              DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')), xml);
#         """)

        self.transaq = tc.XmlConnector()
        self.transaq.SetUserCallback(self._ucallback)
        rz = self.transaq.InitializeEx()
        self.root = 'streams:'
        if rz is not None:
            raise Exception(rz)

    def __del__(self):
        rz = self.transaq.UnInitialize()
        if rz is not None:
            print(rz)

    def _ucallback(self, data: bytes):
        # время прихода сообщения
        t = int(time.time()*1000)
        # Чтоб узнать в какой стрим писать данные, нужно узнать заголовок.
        # Парсим заголовок xml:
        # ... нашли закрывающий тег
        idx = data.index(b'>')
        # ... если есть ' ', значит в теге есть атрибуты
        idx1 = data.find(b' ', 1, idx)
        # ... если пробел не нашли, то idx1==-1, значит команда до '>', иначе до ' '
        idx = idx1 if idx1 > 0 else idx
        # ... 1 символ это '<', значит команда со 2-го символа до ' ' или '>'
        stream = data[1:idx]
        # ... фильтруем только нужные сообщения, если фильтр включен
        # if stream == b'alltrades':
        #     breakpoint()
        # print(stream)
        if config.moex_msg_filter_enable:
            if stream not in config.moex_msgs:
                return
        #  генерируем название стрима по заголовку
        key = f"{self.root}{stream.decode('utf-8')}"
        #  пишем данные в стрим
        # self.redis.xadd(key, {'t': t, 'xml': data})
        # breakpoint()
        self.xmlStream.add(key, {'t': t, 'xml': data})

    def do_command(self):
        dt0 = 0
        ndt0 = 0

        stream_name = f'streams:server'
        while True:
            stream = self.xmlStream.read(stream_name)
            if not stream:
                continue
            stream = msgpack.unpackb(stream)
            fn = stream['fn'].lower().strip()

            # print(f"\n{datetime.datetime.now().isoformat()}")

            if fn == 'exit':
                break

            if fn == 'dt_end':
                print('Command processing delay:')
                print(f'{dt0/ndt0} s')
                dt0 = 0
                ndt0 = 0
                continue

            if fn == 'dt':
                t1 = time.time_ns()
                dt = (t1-stream['t'])/1e9
                dt0 = dt0+dt
                ndt0 = ndt0+1
                # if ndt0==100:
                #     print(f'dt={dt0/100} s')
                #     dt0=0
                #     ndt0=0
                # print(f'dt={dt} s')
                continue

            try:
                class_method = getattr(self, fn)
                class_method(**stream)
            except TypeError as e:
                print(e)
                insp = inspect.signature(class_method)
                print(f'def {fn}{insp}: ...')
            except Exception as e:
                print(e)

        print('Finam-server is closed.')


# -------------------------------------------------------------------------------------------------
strConnect = """
<command id="connect">
    <login>{usr}</login>
    <password>{psw}</password>
    <host>{ip}</host>
    <port>{port}</port>
    <language>ru</language>
    <autopos>{autopos}</autopos>
    <rqdelay>10</rqdelay>
    <utc_time>true</utc_time>
    <milliseconds>true</milliseconds>
</command>
""".strip()

strDisconnect = '<command id="disconnect"/>'

# channel=[alltrades, quotations, quotes]
# op=[subscribe,unsubscribe]
strSubUnsub = """
<command id="{op}"> 
    <{channel}> 
        <security> 
            <board>{board}</board> 
            <seccode>{seccode}</seccode> 
        </security> 
    </{channel}> 
</command>
""".strip()


# Расширяем сервер высокоуровневыми командами
class fserverL1(fserverL0):
    def __init__(self):
        super().__init__(xmlStreamsRedis())

    def str2bool(self, s: str):
        return s.lower() == 'true'
    # -----------------------------------------------------------------------------------------------

    def rawxml(self, xml):
        rz = self.transaq.SendCommand(xml)
        print(xml)
        print(rz)
    # -----------------------------------------------------------------------------------------------

    def connect(self, login=config.FINAM_LOGIN, password=config.FINAM_PASS, 
                host=config.FINAM_IP, port=config.FINAM_PORT, autopos='false', **_):
        autopos = self.str2bool(autopos)
        s = strConnect.format(usr=login, psw=password,
                              ip=host, port=port, autopos=autopos)
        self.rawxml(xml=s)

    def disconnect(self, **_):
        self.rawxml(strDisconnect)

    def subscribe(self, board, seccode, channel, **_):
        s = strSubUnsub.format(op='subscribe', board=board,
                               seccode=seccode, channel=channel)
        self.rawxml(xml=s)

    def unsubscribe(self, board, seccode, channel, **_):
        s = strSubUnsub.format(op='unsubscribe', board=board,
                               seccode=seccode, channel=channel)
        self.rawxml(xml=s)


def main():
    server = fserverL1()
    # server.connect()
    server.do_command()


if __name__ == '__main__':
    main()
