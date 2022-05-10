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
MS_count =0
MD_count =0
amount_trade = 0.01
yunsok = 0

## 메인 루프 ##
while True:
    try:
### RSI 연산 ###
        btc = binance.fetch_ohlcv(symbol="BTC/USDT", timeframe='15m', since=None, limit=140)
        df = pd.DataFrame(data = btc, columns=['datetime','open','high','low','close','volume'])
        df['datetime']=pd.to_datetime(df['datetime'],unit='ms')
        rsi = ta.momentum.rsi(df['close'], window=14)
### RSI Data 저장 ###
        rsi_past = round(rsi[138],2)
        rsi_now = round(rsi[139],2)
### 현재가 ###
        now = ccxt.binance()
        ticker = now.fetch_ticker("BTC/USDT")
        print(ticker['close'])
### 매수/매도조건 ###
        MS_JG = rsi_past<rsi_Low and rsi_Low < rsi_now and yunsok < 5
        MD_JG = rsi_past>rsi_High and rsi_High>rsi_now and yunsok < 5
### No Position ###
        if position == "관망":
          ### RSI Data 비교 ###
                if MS_JG :
                        action = "매수"
                        order = binance.create_market_buy_order(symbol="BTC/USDT",amount=amount_trade)
                        MS_count = 1
                        position = "Long" 
                        alarm = 1
                        yunsok = 1
                elif MD_JG :
                        action = "매도"
                        order = binance.create_market_sell_order(symbol="BTC/USDT",amount=amount_trade)
                        MD_count = 1
                        position = "Short"
                        alarm = 1 
                        yunsok = 1    
                else :
                        action = "관망 유지"
                        position = "관망"
                        alarm = 0
### Long Position ###
        elif position == "Long":
                if MS_JG :
                        action = "추가 매수"
                        order = binance.create_market_buy_order(symbol="BTC/USDT",amount=amount_trade)
                        MS_count = MS_count + 1
                        position = "Long" 
                        alarm = 1
                        yunsok = yunsok + 1
                elif MD_JG :
                        action = "매수 포지션 정리 + 매도"
                        order = binance.create_market_sell_order(symbol="BTC/USDT",amount=amount_trade*MS_count)
                        MS_count = 0
                        order = binance.create_market_sell_order(symbol="BTC/USDT",amount=amount_trade)
                        MD_count = 1
                        position = "Short"
                        alarm = 1     
                        yunsok = 1
                else :
                        action = "관망 유지"
                        position = "Long"
                        alarm = 0
### Short Position ###
        elif position == "Short":
                if MS_JG :
                        action = "매도 포지션 정리 + 매수"
                        order = binance.create_market_buy_order(symbol="BTC/USDT",amount=amount_trade*MD_count)
                        MD_count = 0
                        order = binance.create_market_buy_order(symbol="BTC/USDT",amount=amount_trade)
                        MS_count = 1
                        position = "Long" 
                        alarm = 1
                        yunsok = 1
                elif MD_JG :
                        action = "추가 매도"
                        order = binance.create_market_sell_order(symbol="BTC/USDT",amount=amount_trade)
                        MD_count = MD_count +1
                        position = "Short"
                        alarm = 1 
                        yunsok = yunsok + 1    
                else :
                        action = "관망 유지"
                        position = "Short"
                        alarm = 0
### 텔레그램 메시지 전송 ###
          ### Monitoring ###
        Mess_1 = 'Action : ' + action 
        balance = binance.fetch_balance()
        #Mess_4 = 'USDT 잔액 : %f' %(balance['USDT'])
        #pprint.pprint(str(Mess_1))
        pprint.pprint(balance['USDT'])
        pprint.pprint(alarm)
        pprint.pprint(action)
        pprint.pprint(MS_count)
        pprint.pprint(MD_count)
        pprint.pprint(position)
        pprint.pprint(yunsok)
        #bot.sendMessage(chat_id=chat_id, text=str(Mess_1))
        #bot.sendMessage(chat_id=chat_id, text=balance['USDT'])
        #bot.sendMessage(chat_id=chat_id, text=ticker['close'])
        balance_pos = binance.fetch_balance()
        positions = balance_pos['info']['positions']
        for position2 in positions:
            if position2["symbol"] == "BTCUSDT":
                btc_pdg = position2['entryPrice']
                Mess_3 = '@@평단가@@ : ' + position2['entryPrice']
                amt = position2["positionAmt"]
                sik = position2['unrealizedProfit']
                if float(amt) > 0 :
                        position = "Long"
                elif float(amt) < 0:
                        position = "Short"
                else :
                        position = "관망"

          ### Event ###
          ### 매수 매도 이벤트 텔레그램 전송 ###
        if alarm ==1:
          bot.sendMessage(chat_id=chat_id, text=str(Mess_1))
          bot.sendMessage(chat_id=chat_id, text=str(Mess_3))
          alarm = 0
        
        Mess_2 = 'RSI:%0.2f->%0.2f, 잔액:$%d, 수익:%0.2f' %(rsi_past,rsi_now, balance['total']['USDT'],float(sik))
        print(ticker['close'])
        pprint.pprint(str(Mess_2))
        pprint.pprint(str(Mess_3))
        bot.sendMessage(chat_id=chat_id, text=str(Mess_2))
          ### 대화형 ###
        #df.to_excel("220329.xlsx")
        time.sleep(720)
## 메인 루프 예외 처리 ##
    except Exception as e:
        print("Error Occur")
        print(e)
        time.sleep(10)