import redis as rd
import datetime
import traceback
import time
from lxml import etree as etree_lxml
import config
import pendulum
from sortedcontainers import SortedDict
import msgpack
import json
from collections import defaultdict
from lxml import etree


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    # t.text = ' ' if t.text is None else t.text
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def xml2dict(xml: str) -> str:
    return etree_to_dict(etree.fromstring(xml))


class workerBase():
    """ Базовый воркер """

    def __init__(self, streams) -> None:
        if isinstance(streams, str):
            streams = streams.split(',')
        self.streams = {
            f'{config.STREAM_ROOT}:streams:{stream.strip()}': '0-0' for stream in streams}
        self.redis= rd.from_url(config.REDIS_URL)
        # self.redis = StrictRedis(
        #     host=redis_ip, port=redis_port, decode_responses=True)

    # def parse(self, d):
    #     """ return stream_name[0] and data_of_stream[1]"""
    #     # cid = (d[0][1][0][0]).split('-')
    #     stream_name = d[0]
    #     xml = d[1]
    #     return (stream_name, xml,) #(int(cid[0]), int(cid[1]), stream_name, xml)

    def task(self, data):
        pass

    def do(self):
        print(f'[{self.__class__.__name__}]')
        print(f'Listen: {self.streams}')
        try:
            while True:
                items = self.redis.xread(self.streams, block=0)
                for item in items:
                    rz = self.task(item)
                # if rz is None:
                #     # xtrim не удаляет minid - удалим принудительно
                #     # TODO можно переписать через xdel list(data)
                    # minid = item[1][-1][0]
                    # self.redis.xtrim(item[0], minid = minid)
                    # ids=','.join([i[0] for i in item[1]])
                    ids = [i[0] for i in item[1]]
                    stream_name = item[0]
                    self.redis.xdel(stream_name, *ids)
        except Exception as e:
            traceback.print_exc()
            # print(e)
            input("Press key for exit...")


class workerServerStatus(workerBase):
    """ Статус сервера """

    def __init__(self) -> None:
        super().__init__('server_status')

    def task(self, data):
        items = data[1]
        for item in items:
            xml = etree_lxml.fromstring(item[1]['xml'])
            d = xml.attrib
            d['t'] = datetime.datetime.fromtimestamp(
                int(item[1]['t'])/1000).strftime('%Y-%m-%d %H:%M:%S')
            self.redis.hset('server:server_status', mapping=d)
            print(d)


class workerNewsHeader(workerBase):
    """ Заголовки новостей """

    def __init__(self) -> None:
        super().__init__('news_header')

    def task(self, data):
        items = data[1]
        for item in items:
            try:
                xml = etree_lxml.fromstring(item[1][b'xml'])
                dt = xml.find('timestamp').text
                src = xml.find('source').text
                txt = xml.find('title').text
                print(f'{dt}:{src}: {txt}')
            except Exception as e:
                print(str(e))


class workerBoards(workerBase):
    def __init__(self) -> None:
        super().__init__('boards')

    def task(self, data):
        xml = etree_lxml.fromstring(data[3]['xml'])
        for i in xml:
            b = {}
            cid = i.attrib['id']
            for j in i:
                b[j.tag] = '' if j.text is None else j.text
            self.redis.hset(f'boards:{cid}', mapping=b)
        pass


class workerMarkets(workerBase):
    def __init__(self) -> None:
        super().__init__('markets')

    def task(self, data):
        d = {}
        xml = etree_lxml.fromstring(data[3]['xml'])
        for i in xml:
            d[i.attrib['id']] = '' if i.text is None else i.text
        self.redis.hset('markets', mapping=d)


class workerAllTrades(workerBase):
    """ Лента сделок """

    def __init__(self) -> None:
        super().__init__('alltrades')

    def task(self, data):
        items = data[1]
        pipe=self.redis.pipeline()
        for item in items:

            tr = {}
            xml = etree_lxml.fromstring(item[1]['xml'])
            for trade in xml:
                tr['n'] = int(trade.find('tradeno').text)
                tr['q'] = int(trade.find('quantity').text)
                # tr['p'] = int(float(trade.find('price').text)*100)
                tr['p'] = float(trade.find('price').text)
                # объем тоже в копейках
                # tr['v'] = tr['p'] * tr['q']
                tr['o'] = 1 if trade.find('buysell').text == 'B' else -1
                # переделать на слайсинг строки datetime(int(dt[0:4]))
                dt = pendulum.from_format(trade.find(
                    'time').text, 'DD.MM.YYYY HH:mm:ss.SSS')
                t = int(dt.float_timestamp*1000)
                tr['t'] = t
                seccode = trade.find('seccode').text
                board = trade.find('board').text
                # for i in trade:
                #     if i.tag in ['tradeno','quantity']:
                #         tr[i.tag] = int(i.text)
                #         continue
                #     if i.tag == 'price':
                #         tr[i.tag] = float(i.text)
                #         continue
                #     tr[i.tag] = i.text
                # s = f'{tr["tradeno"]}, {tr["time"]}, {tr["price"]}, {tr["quantity"]}, {tr["buysell"]}'
                # print(tr)
                _id = f"{t}-*"
                pipe.xadd(f'alltrades:{board}:{seccode}', fields=tr, id=_id)
                # self.redis.xadd(f'trade:{board}:{seccode}', fields={'d':msgpack.packb(tr)}, id=_id)
        pipe.execute()

class workerSecurities(workerBase):
    def __init__(self) -> None:
        super().__init__('securities')

    def task(self, data):
        items = data[1]
        for item in items:
            # obj = xml2dict(item[1]['xml'])['securities']['security']
            xml = etree_lxml.fromstring(item[1]['xml'])
            for security in xml:
                d = {}
                d['active'] = security.attrib['active']
                for i in security:
                    if i.tag == 'opmask':
                        d[i.tag] = str(i.attrib)
                        continue
                    d[i.tag] = '' if i.text is None else i.text
                self.redis.hset(
                    f'securities:{d["board"]}:{d["seccode"]}', mapping=d)
                pass


class workerPits(workerBase):
    def __init__(self) -> None:
        super().__init__('pits')

    def task(self, data):
        items = data[1]
        # print(len(items))
        for item in items:
            pits = etree_lxml.fromstring(item[1]['xml'])
            for pit in pits:
                d = {}
                # t=time.perf_counter()
                d.update(pit.attrib)
                for e in pit:
                    if e.tag == 'opmask':
                        d[e.tag] = str(e.attrib)
                    d[e.tag] = '' if e.text is None else e.text
                self.redis.hset(
                    f'securities:{d["board"]}:{d["seccode"]}', mapping=d)
                # print(d)
                # print(time.perf_counter()-t)


class workerSecInfoUpd(workerBase):
    def __init__(self) -> None:
        super().__init__('sec_info_upd')


class workerUnion(workerBase):
    def __init__(self) -> None:
        super().__init__('union')


# class workerClient(workerBase):
#     def __init__(self) -> None:
#         super().__init__('client')
#     def task(self, data):
#         self.redis.set('client', data)


class workerPositions(workerBase):
    def __init__(self) -> None:
        super().__init__('positions')


class workerQuotes(workerBase):
    """ Стакан """

    def __init__(self) -> None:
        super().__init__('quotes')
        self.quotes = {'buy': SortedDict(), 'sell': SortedDict()}
        # self.quotes = SortedDict()

    def task(self, data):
        # tfix = 200  # для компенсации запаздывания сдвинем стакан влево
        items = data[1]
        pipe = self.redis.pipeline()
        for item in items:

            t = int(item[1]['t'])
            xml = etree_lxml.fromstring(item[1]['xml'])
            # если пришло 38-40 значений, будем считать что это полный стакан - сбросим накопления
            # TODO может есть способ более предсказуемый?
            if len(xml) == 40:  # >37:
               self.quotes = {'buy': SortedDict(), 'sell': SortedDict()}
               # print('flash quotes array')

            for i in xml:
                # price = int(float(i.find('price').text)*100)
                price = float(i.find('price').text)
                op = 'buy' if i.find('sell') is None else 'sell'
                quantity = int(i.find(op).text)
                seccode = i.find('seccode').text
                board = i.find('board').text

                self.quotes[op][price] = quantity
                # self.quotes[price] = quantity
                if quantity == -1:
                    del self.quotes[op][price]
            # self.redis.xadd(f'quotes:{board}:{seccode}', {'b':json.dumps(self.quotes['buy']), 's': json.dumps(self.quotes['sell'])}, id=f'{t}-*')
            # self.redis.xadd(f'quotes:{board}:{seccode}', {'b': json.dumps(self.quotes['buy']), 's': json.dumps(self.quotes['sell'])}, id=f'{t}-*')
            pipe.xadd(f'quotes:{board}:{seccode}', {'t': t, 'a': msgpack.packb(
                self.quotes['buy']), 'b': msgpack.packb(self.quotes['sell'])}, id=f'{t}-*')
        pipe.execute()
        pass


class workerQuotations(workerBase):
    def __init__(self) -> None:
        super().__init__('quotations')

    def task(self, data):
        items = data[1]
        for item in items:
            xml = xml2dict(item[1][b'xml'])
            obj=xml['quotations']['quotation']
            obj['t']=item[1][b't']
            # for q in xml:
                # k={}
                # for e in q:
                #     k[e.tag] = '' if e.text is None else e.text
                # k = {e.tag: ('' if e.text is None else e.text) for e in q}
            # pipe = self.redis.pipeline()
            key1=f'{config.STREAM_ROOT}:quotations:{obj["board"]}:{obj["seccode"]}'
            key2=f'{config.STREAM_ROOT}:spread:{obj["board"]}:{obj["seccode"]}'
            self.redis.hset( key1, mapping=obj)
            q = self.redis.hgetall(key1)
            # self.redis.xadd(key2, 
            # {   't':item[1]['t'],
            #     'ask': q['offer'], 'askdepth':q['offerdepth'],
            #     'bid': q['bid'], 'biddepth':q['biddepth']
            # })
            self.redis.xadd(key2, q)
            # pipe.execute()
        return


class workerSimpleCommand(workerBase):
    """ Обработка простых команд """

    def __init__(self) -> None:
        super().__init__('candlekinds,overnight,markets, client')

    def candlekinds(self, items):
        for item in items:
            obj = xml2dict(item[1]['xml'])
            self.redis.set('candlekinds', json.dumps(obj))

    def overnight(self, data):
        pass

    def markets(self, items):
        for item in items:
            # d = {}
            obj = xml2dict(item[1]['xml'])
            # for i in xml:
            #     d[i.attrib['id']] = '' if i.text is None else i.text
            self.redis.set('markets', json.dumps(obj))

    def client(self, items):
        for item in items:
            obj = xml2dict(item[1]['xml'])
            # self.redis.hset(
            #     f"client:{obj['client']['@id']}", mapping=obj['client'])
            self.redis.set(f"client:{obj['client']['@id']}", json.dumps(obj))
            pass

    def task(self, data):
        cmd = data[0]
        if cmd == 'streams:candlekinds':
            self.candlekinds(data[1])
            return
        if cmd == 'streams:overnight':
            self.overnight(data[1])
            return
        if cmd == 'streams:markets':
            self.markets(data[1])
            return
        if cmd == 'streams:client':
            self.client(data[1])
            return


class workerOrders(workerBase):
    def __init__(self) -> None:
        super().__init__('orders')


def main():
    # Testing...
    # (workerServerStatus()).do()
    # (workerNewsHeader()).do() #+
    # (workerBoards()).do()
    # (workerMarkets()).do()
    # (workerAllTrades()).do()
    # (workerSecurities()).do()
    # (workerQuotes()).do()
    # (workerSimpleCommand()).do()
    # (workerQuotations()).do() #+
    # (workerPits()).do()
    print('main done...')


if __name__ == "__main__":
    main()
