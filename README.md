# stocks-trader-engine
An engine to provide stock trading suggestions and place / sell orders to provide consistent profits.

This is work under progress. Please use the repo at your own risk.

Currently the script provides trading signal on NSE stocks based on Marubuzo strategy. That's it !

### Installation Instructions
Ensure you have `python>=3.6`

For dependent package installation, simply do
`pip install -r requirements.txt`

### Running Instructions
Get the list of stocks on NSE first
`python moneycontrol_all_stocks.py`
This will accumulate the stocks information like stockname, symbol and link to live data to `stocks.csv` file

Now, to produce the trading suggestion, simply run
`python stocks.py`
This will populate `trading_decision_today.csv` with BUY/SELL opinions using maruburoz 

Cheers !