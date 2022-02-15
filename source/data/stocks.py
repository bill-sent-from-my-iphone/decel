import yfinance as yf

'''
    Decel offers a rich and comprehensive stock integration, which is
    basically just a wrapper for the yfinance module.

    NOTE: Certain periods/intervals may be blocked by yahoo API for being too intensive
          When in doubt, if you think you may be asking for too much data, you probably are

    Stocks can be specified in a number of ways:
        Ticker: (ex: AAPL)
        Period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        Interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
'''

def get_or(*args):
    for arg in args:
        if arg:
            return arg
    return None


def tick(ticker, period=None, interval=None, p=None, i=None):
    rp = get_or(period, p, '3mo')
    ri = get_or(interval, i, '1h')

    # Below comments are from yfinance pip module and are unchanged

    data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers = ticker,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            period = rp,

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval = ri,

            # group by ticker (to access via data['SPY'])
            # (optional, default is 'column')
            group_by = 'ticker',
            auto_adjust = True,
        )

    for index, row in data.iterrows():
        pass
        #raise Exception(row)

    return data

