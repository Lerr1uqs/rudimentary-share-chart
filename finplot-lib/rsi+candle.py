# 在window下面跑哦
import pandas as pd
import akshare as ak
import numpy as np
import finplot as fplt
import warnings
warnings.simplefilter(action="ignore", category=Warning)

df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20230101", end_date='20231101', adjust="")
df = df.iloc[:, 0:6]
df.日期 = pd.to_datetime(df.日期)
# 列名记得这样定义好
df.columns = ['Time', 'Open', 'Close', 'High', 'Low', 'Volume']


# df.set_index('date', inplace=True)

def Boll(data: pd.DataFrame, n, m):
    mid = data.Close.rolling(n).mean()
    upper = mid + m * data.Close.rolling(n).std()
    lower = mid - m * data.Close.rolling(n).std()
    return mid, upper, lower


def BollSignal(df: pd.DataFrame):
    data = df.copy()
    # 右移一位 [0, 1, 2] -> [NaN, 1, 2]
    data['close_lag1'] = data.Close.shift()
    data['lower_lag1'] = data.lower.shift()
    data['upper_lag1'] = data.upper.shift()
    # 收盘价相对于昨天穿越了下边界
    # 这里的0.99和1.01是为了图像不重叠 最后是画图处理的
    data['buy_signal'] = data.query('Close>lower and close_lag1<lower_lag1').Low * 0.99
    data['sell_signal'] = data.query('Close<upper and close_lag1>upper_lag1').High * 1.01
    return data['buy_signal'], data['sell_signal']


df['mid'], df['upper'], df['lower'] = Boll(df, 20, 2)

# df = df.dropna()

df['buySignal'], df['sellSignal'] = BollSignal(df)

# row代表从上往下有几个视图
# 这里一个是candlestick 一个是volume
ax, ax2, ax3 = fplt.create_plot("pingan bank", rows=3)
fplt.candlestick_ochl(df, ax=ax)
fplt.plot(df['Time'], df['mid'], ax=ax, legend='ma20')
fplt.plot(df['Time'], df['upper'], ax=ax, legend='upper')
fplt.plot(df['Time'], df['lower'], ax=ax, legend='lower')
fplt.plot(df['Time'], df['buySignal'], ax=ax, color='r', style='^', legend='buy mark')
fplt.plot(df['Time'], df['sellSignal'], ax=ax, color='g', style='v', legend='sell mark')
# 因为成交量要根据涨跌绘制红色和绿色 所以必须要Open和Close
fplt.volume_ocv(df[['Time', 'Open', 'Close', 'Volume']], ax=ax3)

def plot_rsi(df: pd.DataFrame, close_cln_name: str, ax, period=14):

    close = df[close_cln_name]

    delta = close.diff()
    gain = delta.where(delta > 0, other=0)
    loss = -delta.where(delta < 0, other=0)

    gain_avg = gain.rolling(window=period, min_periods=1).mean()
    loss_avg = loss.rolling(window=period, min_periods=1).mean()

    rsi = (gain_avg / (loss_avg + gain_avg)) * 100

    # close['rsi'] = rsi
    fplt.plot(df['Time'], rsi, ax=ax, legend='RSI', color="red")
    # fplt.set_y_range(0, 100, ax=ax)
    fplt.add_band(30, 70, ax=ax, color="grey")

plot_rsi(df, "Close", ax2)
# restore view (X-position and zoom) if we ever run this example again
fplt.autoviewrestore()

fplt.show()