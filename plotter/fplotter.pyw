import time
from datetime import datetime, timedelta

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt6.QtGui import QIcon
from redis import StrictRedis
import msgpack
from finam_conf import *
import json

redis = StrictRedis(host=redis_ip, port=redis_port, decode_responses=False)

streams = "alltrades:TQBR:GAZP"
quotes = 'quotes:TQBR:GAZP'


class FmtAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [f'{v:.1f}' for v in values]


# pg.setConfigOption('useOpenGL', True)
# pg.setConfigOption('enableExperimental', True)
# pg.setConfigOption('useNumba', True)
pg.setConfigOptions(antialias=False)

app = pg.mkQApp("EMOX Plotter")

try:
    app.setWindowIcon(QIcon('res/moex.png'))
except Exception as e:
    print(e)

view = pg.GraphicsView()
l = pg.GraphicsLayout(border=(100, 100, 100))
view.setCentralItem(l)
view.show()
# view.setWindowTitle('')
view.resize(700, 780)

# l.ci.layout.setRowMaximumHeight(1, 100)
# view.setRowStretchFactor(1,1)
l.layout.setRowStretchFactor(0, 2)


# exit(0)
# Create a plot with a date-time axis
# w = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()}, clipToView=True)
w = l.addPlot(axisItems={'bottom': pg.DateAxisItem(), 'right': FmtAxisItem(
    orientation='right'), 'left': FmtAxisItem(orientation='left')})
w.showGrid(x=True, y=True)
w.showAxis('right')

# выводим цену на график
# label = pg.LabelItem(justify='right')
# vb = w.vb

# def mouseMoved(evt):
#     pos=evt[0]
#     if w.sceneBoundingRect().contains(pos):
#         mousePoint = vb.mapSceneToView(pos)
#         tm = mousePoint.x()
#         inx=qab[tm]
#         txt=f''
#         label.setText('')

#     pass

# proxy = pg.SignalProxy(w.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

l.nextRow()
w2 = l.addPlot(axisItems={'bottom': pg.DateAxisItem()})
w2.showGrid(x=True, y=True)


w2.setXLink(w)

# Plot sin(1/x^2) with timestamps in the last 100 years
# now = time.time()
# x = np.linspace(2*np.pi, 1000*2*np.pi, 8301)

trade1 = dict(x=[], y=[])
trade2 = dict(x=[], y=[])
trade3 = dict(x=[], y=[])


# массив с крупными заявками
q3qa = dict(time=[], price=[], lots=[])
q3qb = dict(time=[], price=[], lots=[])


# график крупных заявок в стакане
# max ask
c_qa = w.plot(pen=pg.mkPen(color=(255, 255, 0), width=2),
              stepMode='right', symbol=None, clipToView=True, skipFiniteCheck=True)

# max bid
c_qb = w.plot(pen=pg.mkPen(color=(255, 255, 0), width=2),
              stepMode='right', symbol=None, clipToView=True, skipFiniteCheck=True,)


# линия сделок
pn = pg.mkPen(color=(128, 128, 128))
curve1 = w.plot(pen=pn, skipFiniteCheck=True, clipToView=True)
curve1.setSkipFiniteCheck = (True)
# curve1=pg.PlotCurveItem(pen=pn,skipFiniteCheck=True, clipToView=True)

# цветные точки сделок
curve2 = w.plot(pen=None, symbol='o', symbolSize=4,
                symbolPen=None, symbolBrush=(0, 0, 200), clipToView=True, skipFiniteCheck=True,)
curve3 = w.plot(pen=None, symbol='o', symbolSize=4,
                symbolPen=None, symbolBrush=(200, 0, 0), clipToView=True, skipFiniteCheck=True,)

#pen=pg.mkPen(color=(0, 255, 0), width=1),
# спред
curve_ask = w.plot(pen='r',
                   # stepMode='right',
                   skipFiniteCheck=True, clipToView=True)
curve_bid = w.plot(pen='g',
                   # stepMode='right',
                   skipFiniteCheck=True, clipToView=True)
# цветной стакан
curve_plevela = w.plot(pen=None,
                      symbol='o', symbolSize=1,
                      symbolPen=None,symbolBrush='w',
                      skipFiniteCheck=True, clipToView=True)
curve_plevelb = w.plot(pen=None,
                      symbol='o', symbolSize=1,
                      symbolPen=None,symbolBrush='w',
                      skipFiniteCheck=True, clipToView=True)

curve_ab = w.plot(pen=None,
                  symbol='o', symbolSize=4,
                  symbolPen=None,
                  skipFiniteCheck=True, clipToView=True)

curve_waprice = w.plot(pen='y', skipFiniteCheck=True, clipToView=True)
curve_halfab = w.plot(pen='w', skipFiniteCheck=True, clipToView=True)

qab = dict(t=[], ask=[], bid=[], waprice=[], halfab=[])
plevela = {'t': [], 'ask': []}
plevelb = {'t': [], 'bid': []}
# индикатор
ind1 = dict(t=[], b=[], s=[], bs=[])
curind1 = w2.plot(skipFiniteCheck=True, clipToView=True)
curind2 = w2.plot(skipFiniteCheck=True, clipToView=True)
curind3 = w2.plot(skipFiniteCheck=True, clipToView=True)


def vol_sum(d):
    global ind1
    m = d[1]
    ind1['t'].append(int(m[b't'])/1000)
    # v = float(m[b'p'])*int(m[b'q'])
    v = int(m[b'q'])
    o = int(m[b'o'])

    # lbuy = ind1['b'][-1] if ind1['b'] else 1
    # lsell = ind1['s'][-1] if ind1['s'] else 1

    # if o > 0:
    #     ind1['b'].append(lbuy+v)
    #     ind1['s'].append(lsell)
    # else:
    #     ind1['s'].append(lsell+v)
    #     ind1['b'].append(lbuy)

    l = ind1['bs'][-1] if ind1['bs'] else 0
    # l = ind1['b'][-1]/ind1['s'][-1]
    ind1['bs'].append(l+(v*o))

    pass


w.setWindowTitle(f'{streams}')
w.show()

t = '-'
t = int(time.time()*1000)-1000*60*25
# t = int(time.time()*1000)

t1 = t
t2 = int(time.time()*1000)-1000*60*15
cm = pg.colormap.get('CET-L9')  # prepare a linear color map


def update():
    global curve1, streams, t, t1, t2, trade1, w, qab, q3qb, q3qa, c_qb, c_qa, ind1, curind1, curve_waprice
    global curve_halfab, curve_plevelb, curve_plevela, plevela, plevelb
    ds = redis.xrange(streams, min=t, max='+')
    ds1 = redis.xrange('spread:TQBR:GAZP', min=t1, max='+')
    #рисуем price level
    ds2 = redis.xrange('quotes:TQBR:GAZP', min=t2, max='+')
    # ds = []

    pg.QtGui.QApplication.processEvents()
    tm = tm1 = tm2 = 0
    nMin = 25
    # обработка стакана и заявок
    if len(ds2) != 0:
        for k in ds2:
            tm2 = int(k[1][b't'])
            ask = msgpack.unpackb(k[1][b'a'], strict_map_key=False)
            bid = msgpack.unpackb(k[1][b'b'], strict_map_key=False)
            for a in ask.items():
                if a[1]> 100:
                    plevela['t'].append(tm2/1000)
                    plevela['ask'].append(a[0])
            for b in bid.items():
                if b[1]> 100:
                    plevelb['t'].append(tm2/1000)
                    plevelb['bid'].append(b[0])

            pg.QtGui.QApplication.processEvents()
        ttrim = time.time()-60*15
        while plevela['t'][0] < ttrim:
            plevela['t'].pop(0)
            plevela['ask'].pop(0)
        while plevelb['t'][0] < ttrim:
            plevelb['t'].pop(0)
            plevelb['bid'].pop(0)
        curve_plevela.setData(plevela['t'], plevela['ask'])
        curve_plevelb.setData(plevelb['t'], plevelb['bid'])
        t2 = f'({tm2}'


    # обработка стакана
    if len(ds1) != 0:
        for q in ds1:
            tm1 = int(q[1][b't'])  # int(q[0].split(b'-')[0])
            # ask = msgpack.unpackb(q[1][b'a'], strict_map_key=False)
            # bid = msgpack.unpackb(q[1][b'b'], strict_map_key=False)
            a = float(q[1][b'offer'])
            b = float(q[1][b'bid'])
            hab = (a+b)/2
            tm_norm = tm1/1000
            qab['t'].append(tm_norm)

            # if len(ask) == 0:
            #     qab['a'].append(list(ask)[-1])
            # if len(bid) == 0:
            #     qab['b'].append(list(bid)[0])

            # a = list(ask)[-1]
            # b = list(bid)[0]
            qab['ask'].append(a)
            qab['bid'].append(b)
            qab['waprice'].append(float(q[1][b'waprice']))
            qab['halfab'].append(hab)

            # qab['x'].pop(0)
            # qab['a'].pop(0)
            # qab['b'].pop(0)
            pg.QtGui.QApplication.processEvents()
            # покажем самую крупную заявку из N
            # N = 5
            # bidN = {i: bid[i] for i in list(bid)[:N]}
            # bid_big = sorted(bidN.items(), key=lambda i: i[1], reverse=True)
            # for e,i in enumerate(bid_big):
            #     q3qb['time'].append(tm_norm)
            #     q3qb['price'].append(i[0])
            #     q3qb['lots'].append(5-e)
            # q3qb['time'].append(tm_norm)
            # q3qb['price'].append(bid_big[0][0])
            # q3qb['lots'].append(5-e)

            # askN = {i: ask[i] for i in list(ask)[-N:]}
            # ask_big = sorted(askN.items(), key=lambda i: i[1], reverse=True)
            # for e,i in enumerate( ask_big):
            #     q3qa['time'].append(tm_norm)
            #     q3qa['price'].append(i[0])
            #     q3qa['lots'].append(5-e)
            # q3qa['time'].append(tm_norm)
            # q3qa['price'].append(ask_big[0][0])

            pass

        t1 = f'({tm1}'
        # qab['x']['a']=qab['x']['a'][len(ds1):]
        # qab['x']['b']=qab['x']['b'][len(ds1):]
        # удалим даты выходящие за диапазон nMin минут
        ttrim = time.time()-60*nMin
        while qab['t'][0] < ttrim:
            qab['t'].pop(0)
            qab['ask'].pop(0)
            qab['bid'].pop(0)
            qab['waprice'].pop(0)
            qab['halfab'].pop(0)

        # curve_halfab.setData(qab['t'], qab['halfab'])
        curve_ask.setData(qab['t'], qab['ask'])
        curve_bid.setData(qab['t'], qab['bid'])
        curve_ab.setData(x=[qab['t'][-1], qab['t'][-1]],
                         y=[qab['ask'][-1], qab['bid'][-1]],
                         symbolBrush=['w', 'w'])
        # curve_waprice.setData(qab['t'],qab['waprice'])
        # c_qb.setData(q3qb['time'], q3qb['price'])  # ,symbolSize=q3qb['lots'])
        # c_qa.setData(q3qa['time'], q3qa['price'])  # ,symbolSize=q3qa['lots'])

    pg.QtGui.QApplication.processEvents()
    if len(ds) != 0:
        for d in ds:
            tm = int(d[1][b't'])  # int(d[0].split(b'-')[0])
            dd = d[1]

            tm_norm = tm/1000
            trade1['x'].append(tm_norm)
            trade1['y'].append(float(dd[b'p']))

            # if int(dd[b'o']) == 1:
            #     trade2['x'].append(tm_norm)
            #     trade2['y'].append(float(dd[b'p']))
            # else:
            #     trade3['x'].append(tm_norm)
            #     trade3['y'].append(float(dd[b'p']))
            pg.QtGui.QApplication.processEvents()
            # расчет индикатора объема
            vol_sum(d)

        t = f'({tm}'

        # pg.QtGui.QApplication.processEvents()
        # curve1.setData(trade1['x'], trade1['y'])
        # curve2.setData(trade2)
        # curve3.setData(trade3)
        curind1.setData(ind1['t'], ind1['bs'])
        # curind2.setData(ind1['t'],ind1['b'])
        # curind3.setData(ind1['t'],ind1['s'])
        # удалим даты выходящие за диапазон nMin минут
        ttrim = time.time()-60*nMin
        while ind1['t'][0] < ttrim:
            ind1['t'].pop(0)
            ind1['bs'].pop(0)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)


if __name__ == '__main__':
    pg.exec()
