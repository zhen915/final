# 載入必要模組
import haohaninfo
from order_Lo8 import Record
import numpy as np
from talib.abstract import SMA,EMA, WMA
#import sys
import indicator_f_Lo2,datetime
import pandas as pd


df = pd.read_excel("kbars_2330_2020-01-01-2024-06-20 1.xlsx")
df.columns  ## Index(['Unnamed: 0', 'time', 'open', 'low', 'high', 'close', 'volume','amount'], dtype='object')
df = df.drop('Unnamed: 0',axis=1)
df.columns  ## Index(['time', 'open', 'low', 'high', 'close', 'volume', 'amount'], dtype='object')
#df['time']
#type(df['time'])  ## pandas.core.series.Series
#df['time'][11]
df.head()

## 畫 KBar 圖
# df.columns = [ i[0].upper()+i[1:] for i in df.columns ]
# df.set_index( "Time" , inplace=True)
# import mplfinance as mpf
# mpf.plot(df,volume=True,addplot=[],type='candle',style='charles')
df.set_index( "time" , inplace=True)
import mplfinance as mpf
mpf.plot(df,volume=True,addplot=[],type='candle',style='charles')

df['time'] = df.index

### 轉化為字典:
KBar_dic = df.to_dict()
#type(KBar_dic)
#KBar_dic.keys()  ## dict_keys(['time', 'open', 'low', 'high', 'close', 'volume', 'amount'])
#KBar_dic['open']
#type(KBar_dic['open'])  ## dict
#KBar_dic['open'].values()
#type(KBar_dic['open'].values())  ## dict_values
KBar_open_list = list(KBar_dic['open'].values())
KBar_dic['open']=np.array(KBar_open_list)
#type(KBar_dic['open'])  ## numpy.ndarray
#KBar_dic['open'].shape  ## (1596,)
#KBar_dic['open'].size   ##  1596

KBar_dic['product'] = np.repeat('tsmc', KBar_dic['open'].size)
#KBar_dic['product'].size   ## 1596
#KBar_dic['product'][0]      ## 'tsmc'

KBar_time_list = list(KBar_dic['time'].values())
KBar_time_list = [i.to_pydatetime() for i in KBar_time_list] ## Timestamp to datetime
KBar_dic['time']=np.array(KBar_time_list)

# KBar_time_list[0]        ## Timestamp('2022-07-01 09:01:00')
# type(KBar_time_list[0])  ## pandas._libs.tslibs.timestamps.Timestamp
#KBar_time_list[0].to_pydatetime() ## datetime.datetime(2022, 7, 1, 9, 1)
#KBar_time_list[0].to_numpy()      ## numpy.datetime64('2022-07-01T09:01:00.000000000')
#KBar_dic['time']=np.array(KBar_time_list)
#KBar_dic['time'][80]   ## Timestamp('2022-09-01 23:02:00')

KBar_low_list = list(KBar_dic['low'].values())
KBar_dic['low']=np.array(KBar_low_list)

KBar_high_list = list(KBar_dic['high'].values())
KBar_dic['high']=np.array(KBar_high_list)

KBar_close_list = list(KBar_dic['close'].values())
KBar_dic['close']=np.array(KBar_close_list)

KBar_volume_list = list(KBar_dic['volume'].values())
KBar_dic['volume']=np.array(KBar_volume_list)

KBar_amount_list = list(KBar_dic['amount'].values())
KBar_dic['amount']=np.array(KBar_amount_list)





# 建立部位管理物件
OrderRecord=Record() 
# 取得回測參數、移動停損點數
# StartDate=sys.argv[1]
# EndDate=sys.argv[2]
# LongMAPeriod=int(sys.argv[3])
# ShortMAPeriod=int(sys.argv[4])
# MoveStopLoss=float(sys.argv[5])

#StartDate='20170330'
#EndDate='20170331'
LongMAPeriod=20
ShortMAPeriod=10
MoveStopLoss=30

# 回測取報價物件
KBar_dic['MA_long']=SMA(KBar_dic,timeperiod=LongMAPeriod)
KBar_dic['MA_short']=SMA(KBar_dic,timeperiod=ShortMAPeriod)
# 開始回測
for n in range(0,len(KBar_dic['time'])-1):
    # 先判斷long MA的上一筆值是否為空值 再接續判斷策略內容
    if not np.isnan( KBar_dic['MA_long'][n-1] ) :
        ## 進場: 如果無未平倉部位 
        if OrderRecord.GetOpenInterest()==0 :
            # 多單進場: 黃金交叉: short MA 向上突破 long MA
            if KBar_dic['MA_short'][n-1] <= KBar_dic['MA_long'][n-1] and KBar_dic['MA_short'][n] > KBar_dic['MA_long'][n] :
                OrderRecord.Order('Buy', KBar_dic['product'][n+1],KBar_dic['time'][n+1],KBar_dic['open'][n+1],1)
                OrderPrice = KBar_dic['open'][n+1]
                StopLossPoint = OrderPrice - MoveStopLoss
                continue
            # 空單進場:死亡交叉: short MA 向下突破 long MA
            if KBar_dic['MA_short'][n-1] >= KBar_dic['MA_long'][n-1] and KBar_dic['MA_short'][n] < KBar_dic['MA_long'][n] :
                OrderRecord.Order('Sell', KBar_dic['product'][n+1],KBar_dic['time'][n+1],KBar_dic['open'][n+1],1)
                OrderPrice = KBar_dic['open'][n+1]
                StopLossPoint = OrderPrice + MoveStopLoss
                continue
        # 多單出場: 如果有多單部位   
        elif OrderRecord.GetOpenInterest()==1 :
            ## 結算平倉(期貨才使用, 股票除非是下市櫃)
            if KBar_dic['product'][n+1] != KBar_dic['product'][n] :
                OrderRecord.Cover('Sell', KBar_dic['product'][n],KBar_dic['time'][n],KBar_dic['close'][n],1)
                continue
            # 逐筆移動停損價位
            if KBar_dic['close'][n] - MoveStopLoss > StopLossPoint :
                StopLossPoint = KBar_dic['close'][n] - MoveStopLoss
            # 如果上一根K的收盤價觸及停損價位，則在最新時間出場
            elif KBar_dic['close'][n] < StopLossPoint :
                OrderRecord.Cover('Sell', KBar_dic['product'][n+1],KBar_dic['time'][n+1],KBar_dic['open'][n+1],1)
                continue
        # 空單出場: 如果有空單部位
        elif OrderRecord.GetOpenInterest()==-1 :
            ## 結算平倉(期貨才使用, 股票除非是下市櫃)
            if KBar_dic['product'][n+1] != KBar_dic['product'][n] :
           
                OrderRecord.Cover('Buy', KBar_dic['product'][n],KBar_dic['time'][n],KBar_dic['close'][n],1)
                continue
            # 逐筆更新移動停損價位
            if KBar_dic['close'][n] + MoveStopLoss < StopLossPoint :
                StopLossPoint = KBar_dic['close'][n] + MoveStopLoss
            # 如果上一根K的收盤價觸及停損價位，則在最新時間出場
            elif KBar_dic['close'][n] > StopLossPoint :
                OrderRecord.Cover('Buy', KBar_dic['product'][n+1],KBar_dic['time'][n+1],KBar_dic['open'][n+1],1)
                continue
                


# 繪製走勢圖加上MA以及下單點位
from chart import ChartOrder_MA
ChartOrder_MA(KBar_dic,OrderRecord.GetTradeRecord())
KBar_dic.keys()



## 計算績效:
OrderRecord.GetTradeRecord()  ## 交易紀錄清單
OrderRecord.GetProfit()       ## 利潤清單
OrderRecord.GetTotalProfit()  ## 淨利
OrderRecord.GetWinRate()      ## 勝率
OrderRecord.GetAccLoss()      ## 最大連續虧損
OrderRecord.GetMDD()          ## 最大資金回落(MDD)




# KBar_dic['product'][n+1]  ## 'tsmc'
# len(KBar_dic['product'])  ## 1596
# type(KBar_dic)  ##dict
# type(OrderRecord.GetTradeRecord())  ## list
# len(OrderRecord.GetTradeRecord()) ##1
