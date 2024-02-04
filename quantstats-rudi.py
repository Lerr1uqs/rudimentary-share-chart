import quantstats as qs
import tushare as ts
import pandas as pd

# extend pandas functionality with metrics, etc.
qs.extend_pandas()

# fetch the daily returns for a stock
# stock = qs.utils.download_returns('META', proxy="http://192.168.110.1:7890")
stock = ts.get_hist_data("601058").sort_values(by="date",ascending=True)
stock.index = pd.to_datetime(stock.index)
# stock

# show sharpe ratio
qs.stats.sharpe(stock)

# or using extend_pandas() :)
print(stock.sharpe())

# 计算每日相对于前一天的回报率 
stock['returns'] = (stock["close"] - stock["close"].shift(1)) / stock["close"].shift(1)

# qs.reports.html(stock, "SPY")
qs.reports.html(returns=stock['returns'], output="report.html") 

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# 定义端口号
port = 8000

# 创建HTTP服务器，并指定启动页为report.html
handler = SimpleHTTPRequestHandler
handler.extensions_map.update({
    '.html': 'text/html',
    '.js': 'application/javascript',
})

# 启动HTTP服务器
httpd = TCPServer(('localhost', port), handler)
print(f"Server started at http://localhost:{port}/report.html")
print("Press Ctrl+C to stop the server.")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    httpd.server_close()

'''
open           
high           
close          
low            
volume         
price_change   
p_change       
ma5            
ma10           
ma20           
v_ma5          
v_ma10         
v_ma20         
turnover       
'''