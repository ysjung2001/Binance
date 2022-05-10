from logging import Filter
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters  # import modules
import telegram
#import bot_api
import time
import ccxt
import pandas as pd
import ta.momentum
import ta.trend
import ta.volatility
import ta.volume
import pprint
from binance.client import Client

###텔레그램 설정###
my_token = '5267562862:AAHjhH5u95Fh5uGDMcvWwpnirvmi6aiCEsE'
chat_id = '5267710018'
bot = telegram.Bot(token=my_token)
###바이낸스 설정###
api_key = 'O7JKt8CBROEq5GNsg5wIzeKnhXJDSyIGyaPd0L4Va3f5MAvyR9C7EL9W0sNLUlI7'
secret = 'BpwI9mDrDIjIMQA0NWgYhMeerTPTaCAgJcXSItSkI3lun8X7uvJSBrPizs263gJo'
binance = ccxt.binance(config={'apiKey': api_key, 'secret' : secret, 'options':{'defaultType':'future'}})
client = Client(api_key=api_key, api_secret=secret)
###RSI Line 설정###
rsi_Low = 35
rsi_High = 65
### 레버리지 설정 ###
markets = binance.load_markets()
symbol = "BTC/USDT"
market = binance.market(symbol)
leverage = 10
resp = binance.fapiPrivate_post_leverage({'symbol': market['id'],'leverage': leverage})
### 초기화 ###
balance_pos = binance.fetch_balance()
positions = balance_pos['info']['positions']
for position2 in positions:
        if position2["symbol"] == "BTCUSDT":
                btc_pdg = position2['entryPrice']
                amt = position2["positionAmt"]
                if float(amt) > 0 :
                        position = "Long"
                elif float(amt) < 0:
                        position = "Short"
                else :
                        position = "관망"
action = "관망"
alarm = 0


alarm_1h_down = 0
alarm_1h_up = 0
alarm_1d_down = 0
alarm_1d_up = 0
alarm_4h_down = 0
alarm_4h_up = 0

## 메인 루프 ##
while True:
    try:
### RSI 연산 ###
        btc = binance.fetch_ohlcv(symbol="BTC/USDT", timeframe='1h', since=None, limit=140)
        df = pd.DataFrame(data = btc, columns=['datetime','open','high','low','close','volume'])
        df['datetime']=pd.to_datetime(df['datetime'],unit='ms')
        rsi = ta.momentum.rsi(df['close'], window=14)
### RSI Data 저장 ###
        rsi_past = round(rsi[138],2)
        rsi_now = round(rsi[139],2)
### 1시간봉 RSI 알람 ###
        if rsi_past < rsi_Low < rsi_now :
            alarm_1h_up = 1
        else :
            alarm_1d_up = 0
        if rsi_past > rsi_High > rsi_now :
            alarm_1h_down = 1
        else : 
            alarm_1h_down = 0
### 4시간봉 RSI 알람 ###
        btc = binance.fetch_ohlcv(symbol="BTC/USDT", timeframe='4h', since=None, limit=140)
        df = pd.DataFrame(data = btc, columns=['datetime','open','high','low','close','volume'])
        df['datetime']=pd.to_datetime(df['datetime'],unit='ms')
        rsi = ta.momentum.rsi(df['close'], window=14)
        rsi_past = round(rsi[138],2)
        rsi_now = round(rsi[139],2)
        if rsi_past < rsi_Low < rsi_now :
            alarm_4h_up = 1
        else : 
            alarm_4h_up = 0
        if rsi_past > rsi_High > rsi_now :
            alarm_4h_down = 1
        else : 
            alarm_4h_down = 0
### 일봉 RSI 알람 ###
        btc = binance.fetch_ohlcv(symbol="BTC/USDT", timeframe='1d', since=None, limit=140)
        df = pd.DataFrame(data = btc, columns=['datetime','open','high','low','close','volume'])
        df['datetime']=pd.to_datetime(df['datetime'],unit='ms')
        rsi = ta.momentum.rsi(df['close'], window=14)
        rsi_past = round(rsi[138],2)
        rsi_now = round(rsi[139],2)
        if rsi_past < rsi_Low < rsi_now :
            alarm_1d_up = 1
        else : 
            alarm_1d_up = 0
        if rsi_past > rsi_High > rsi_now :
            alarm_1d_down = 1
        else : 
            alarm_1d_down =0

### 현재가 ###
        now = ccxt.binance()
        ticker = now.fetch_ticker("BTC/USDT")
        print(ticker['close'])


### 텔레그램 메시지 전송 ###
          ### Monitoring ###
        balance = binance.fetch_balance()

        balance_pos = binance.fetch_balance()
        positions = balance_pos['info']['positions']
        for position2 in positions:
            if position2["symbol"] == "BTCUSDT":
                btc_pdg = position2['entryPrice']
                amt = position2["positionAmt"]
                sik = position2['unrealizedProfit']
                if float(amt) > 0 :
                        position = "Long"
                elif float(amt) < 0:
                        position = "Short"
                else :
                        position = "관망"
                Mess_3 = '평단가:$%0.1f, Position:[%s], 미실현손익:$%0.1f' %(float(position2['entryPrice']), position, float(sik))

        
        Mess_2 = '현재가:$%d, 잔액:$%d' %(ticker['close'],balance['total']['USDT'])
        Mess_1 = '1H (↓%d↑%d) 4H (↓%d↑%d) 1D (↓%d↑%d)' %(alarm_1h_down,alarm_1h_up,alarm_4h_down,alarm_4h_up,
        alarm_1d_down,alarm_1d_up)

        pprint.pprint(str(Mess_2))
        pprint.pprint(str(Mess_3))
        pprint.pprint(str(Mess_1))

        bot.sendMessage(chat_id=chat_id, text=str(Mess_2))
        bot.sendMessage(chat_id=chat_id, text=str(Mess_3))
        bot.sendMessage(chat_id=chat_id, text=str(Mess_1))

        time.sleep(720)

## 메인 루프 예외 처리 ##
    except Exception as e:
        print("Error Occur")
        print(e)
        time.sleep(10)