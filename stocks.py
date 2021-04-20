import pandas as pd
import mplfinance as mpf
from dateutil import parser
import requests,time,math,csv
from bs4 import BeautifulSoup
import numpy as np
from datetime import date
from tqdm import tqdm

url = 'https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={}'
moneycontrolAPI = 'https://www.moneycontrol.com/tech_charts/bse/his/{}.csv'

history_days = 10

max_variance_perc = 0.50
max_range_perc = 10
min_range_perc = 0.75

f =  open(str(date.today())+".csv", "w")
writer = csv.writer(f)
writer.writerow(['StockName','StockUrl','Status','Buy At','StopLoss'])

trade_decision = open("trade_decision_today.csv", "w")
decision_writer = csv.writer(trade_decision)
decision_writer.writerow(['StockName', 'Decision', 'Buy At/Sell At', 'Stop Loss', 'Open', 'High', 'Low', 'CURR', 'LiveURL'])
        
        
def live_marubuzo(open_val, high_val, low_val, curr_val):
    if (open_val < curr_val):
        if((abs(high_val - curr_val)/curr_val)*100 < max_variance_perc and \
           (abs(low_val - open_val)/open_val)*100 < max_variance_perc and \
           (abs(high_val - low_val)/low_val)*100 <= max_range_perc and \
           (abs(high_val - low_val)/low_val)*100 >= min_range_perc ):
            return 1
        else:
            return np.nan
    else:
        if((abs(high_val - open_val)/open_val)*100 < max_variance_perc and \
               (abs(low_val - curr_val)/curr_val)*100 < max_variance_perc and \
               (abs(high_val - low_val)/low_val)*100 <= max_range_perc and \
               (abs(high_val - low_val)/low_val)*100 >= min_range_perc ):
                return -1
        else:
            return np.nan
            

# from moneycontrol api, wont include current day values as data is frm csv files of moneycontrol server
def read_history_stock(shortname,stockname,buildChart):
    requestUrl = moneycontrolAPI.format(shortname)
    data = requests.get(requestUrl,headers={'Cache-Control': 'no-cache'})
    data =  data.text.splitlines()[-history_days:] #added the braces here to limit to last day
    df = pd.DataFrame([sub.split(",") for sub in data])
    df.columns = ["Date", "Open", "High", "Low","Close","Volume","A","B","C","D"]

    df['Date'] = df['Date'].apply(lambda x: parser.parse(x))
    df = df[["Date", "Open", "High", "Low","Close","Volume"]]
    df.set_index('Date', inplace=True)

    df['Open'] = df['Open'].apply(lambda x: float(x))
    df['High'] = df['High'].apply(lambda x: float(x))
    df['Low'] = df['Low'].apply(lambda x: float(x))
    df['Close'] = df['Close'].apply(lambda x: float(x))
    df['Volume'] = df['Volume'].apply(lambda x: float(x))

    #print(data)
    days_of_marubuzo = [ live_marubuzo(value['Open'],value['High'],value['Low'],value['Close']) for index,value in df.iterrows() ]
    #print(days_of_marubuzo)
    
    if np.isnan(days_of_marubuzo[-1]):
        return

    #writer.writerow([stockname,requestUrl,'BUY/SELL', df.iloc[[-1]]['Close'][0] , df.iloc[[-1]]['Low'][0] ])
    #f.flush()

    if buildChart == True:
        marubuzo = mpf.make_addplot(days_of_marubuzo, markersize=5)
        mpf.plot(df,volume=True,addplot=marubuzo,type='candle',mav=4,title=stockname)


# NSE vals only considered
def read_live_stock(livelink, shortname, stockname):
    response = requests.get(livelink)
    soup = BeautifulSoup(response.content, 'lxml')
    
    open_val = float(soup.find('td',{'class':'nseopn bseopn'}).get_text(strip=True).replace(',',''))
    high_val = float(soup.find('div',{'class':'FR nseHP'}).get_text(strip=True).replace(',',''))
    low_val = float(soup.find('div',{'class':'FL nseLP'}).get_text(strip=True).replace(',',''))
    curr_val = float(soup.find('div',{'class':'pcstkspr nsestkcp bsestkcp futstkcp optstkcp'}).get_text(strip=True).replace(',',''))
    
    trade_signal = live_marubuzo(open_val, high_val, low_val, curr_val)
    
    if not np.isnan(trade_signal):
        if (trade_signal == 1):
            print("Buy ", stockname)
            decision_writer.writerow([stockname, 'BUY', curr_val, open_val, open_val, high_val, low_val, curr_val, livelink])
        else:
            print("Sell ", stockname)
            decision_writer.writerow([stockname, 'SELL', curr_val, 'nan', open_val, high_val, low_val, curr_val, livelink])

    trade_decision.flush()



stocks = pd.read_csv('stocks.csv')

for index, row in tqdm(stocks.iterrows()):
    shortname = row['Shortname'].lower()
    stockname = row['Company']
    livelink = row['Link']
    try:
        #read_history_stock(shortname, stockname, False)
        read_live_stock(livelink, shortname, stockname)
    except Exception as e:
        print('Skipping stock '+stockname+' due to '+str(e))
