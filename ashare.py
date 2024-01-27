import json, requests
from datetime import datetime
import pandas as pd
from loguru import logger

from abc import ABC, abstractmethod

class ApiServerBase(ABC):
    # @abstractmethod
    # def query_daily_prices(self):
    #     pass

    # @abstractmethod
    # def query_hourly_prices(self):
    #     pass

    # @abstractmethod
    # def query_minute_prices(self):
    #     pass
    pass

# TODO: 'Xday','Xmonth', 'Xminute' # 'daily'(等同于'1d'), 'minute'(等同于'1m')
    
class Tencent(ApiServerBase):
    def __init__(self) -> None:
        pass

    def query_prices(self, security: str, frequency="day", end_date=datetime.now(), count=10) -> pd.DataFrame:
        '''
        腾讯日 周 月线。
        frequency in ["day", "week", "month"]
        '''

        if frequency not in ["day", "week", "month"]:
            raise RuntimeError(f"frequency error : {frequency}")

        if not isinstance(end_date, datetime):
            raise TypeError(type(end_date))
        

        # TODO: check security
        end_date_str = end_date.strftime(r'%Y-%m-%d')

        freq = frequency

        URL = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={security},{freq},,{end_date_str},{count},qfq' # TODO: qfq 前复权

        content = json.loads(requests.get(URL).content)

        if content["msg"] != "":
            raise RuntimeError(content["msg"])
            
        '''
        {
            "code": 0,
            "msg": "",
            "data": {
                "sh605577": {
                    "qfqday": [
                        [
                            "2024-01-25",
                            "27.590",
                            "30.800",
                            "30.800",
                            "27.120",
                            "285458.000"
                        ]
                    ],
        '''
        # 指数是 freq 其他的则是 qfq+freq 
        day = "day" if "qfq" + freq not in content["data"][security] else "qfq" + freq
        data = content["data"][security][day]

        '''
        ['2022-06-24', '11.510', '11.370', '11.530', '11.340', '24319.000', {'nd': '2021', 'fh_sh': '1', 'djr': '2022-06-23', 'cqr': '2022-06-24', 'FHcontent': '10派1元'}]
        ['2023-07-05', '11.270', '11.220', '11.430', '11.200', '20268.000', {'nd': '2022', 'fh_sh': '1.1', 'djr': '2023-07-04', 'cqr': '2023-07-05', 'FHcontent': '10派1.1元'}]
        '''

        # NOTE: data会格外加入一栏除权信息 需要清洗
        for i, d in enumerate(data):
            data[i] = d[:6]

        columns = ['time','open','close','high','low','volume']
        df = pd.DataFrame(
            data, 
            columns=columns,
        )

        # 除了time之外都进行浮点化
        df[columns[1:]] = df[columns[1:]].astype("float")

        df.loc[:, "time"] = pd.to_datetime(df["time"])

        df.set_index('time', inplace=True) # Whether to modify the DataFrame rather than creating a new one.
        # df.index.name = '' TODO:?

        return df

    def query_minute_prices(self, security: str, frequency="1minute", end_date=datetime.now(), count=10) -> pd.DataFrame:
        '''
        腾讯分钟线.
        frequency in [1minute, 5minute, 10minute ...]
        '''
        if not frequency.endswith("minute"): 
            raise RuntimeError(f"frequency error :{frequency}")
            
        if not frequency[0].isdigit():
            raise RuntimeError(f"frequency error {frequency}")
            
        if not isinstance(end_date, datetime):
            raise TypeError(type(end_date))
        
        # 提取前面的数字
        freq = int(''.join(c for c in frequency if c.isdigit()))

        URL = f'http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={security},m{freq},,{count}' 

        content = json.loads(requests.get(URL).content)
        data = content["data"][security]["m" + str(freq)]

        columns = ['time','open','close','high','low','volume','n1','n2']
        df = pd.DataFrame(
            data, 
            columns=columns
        )[columns[:-2]]

        df[columns[1:-2]] = df[columns[1:-2]].astype("float")

        df.loc[:, "time"] = pd.to_datetime(df["time"])

        df.set_index(['time'], inplace=True)

        return df

class Sina(ApiServerBase):

    # sina新浪全周期获取函数，分钟线 5m,15m,30m,60m
    def query_prices(self, security: str, frequency="5m", end_date=datetime.now(), count=10) -> pd.DataFrame:
        '''
        frequency必须是5的倍数
        '''
        if not frequency.endswith("m"): 
            raise RuntimeError(f"frequency error :{frequency}")
            
        if not frequency[0].isdigit():
            raise RuntimeError(f"frequency error {frequency}")
            
        if not isinstance(end_date, datetime):
            raise TypeError(type(end_date))

        # 提取前面的数字
        mfreq = int(''.join(c for c in frequency if c.isdigit()))

        if mfreq % 5 != 0:
            raise RuntimeError(f"frequency must be multiple of five but found :{frequency}")

        URL = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={security}&scale={mfreq}&ma=5&datalen={count}'

        content = json.loads(requests.get(URL).content)
        '''
        这边其实还有两列数据 暂时用不上
        "ma_price5": 29.488,
        "ma_volume5": 331320
        '''
        data = content

        columns = ['day','open','close','high','low','volume']
        df = pd.DataFrame(
            data, 
            columns=columns
        )

        df[columns[1:]] = df[columns[1:]].astype("float")
        df.loc[:, "day"] = pd.to_datetime(df["day"])
        df.set_index(['day'], inplace=True)

        return df
# TODO: decorator check security

def security_checker(func):

    def wrapper(self, security: str, *args, **kwargs):
        # 检查 security 是否符合要求，这里假设 security 必须是字符串类型
        if not isinstance(security, str):
            raise TypeError("The 'security' parameter must be a string.")

        while True:
            if any(security.endswith(end) for end in [".XSHG", ".XSHE"]):
                break
            
            if any(security.startswith(start) for start in ["sh", "sz"]):
                break
            
            raise RuntimeError(f"security format error : {security}")

        #证券代码编码兼容处理 
        code = security.replace('.XSHG', '').replace('.XSHE', '')
        code = 'sh' + code if ('XSHG' in security) else 'sz' + code if ('XSHE' in security) else security

        # 调用原始函数
        result = func(self, code, *args, **kwargs)
        
        return result
    
    return wrapper


class Api:
    def __init__(self) -> None:
        self._tencent = Tencent()
        self._sina = Sina()

    @security_checker
    def query_prices_untilnow(self, security: str, frequency='60minute', count=10) -> pd.DataFrame:
        '''
        tx支持: 1minute 5minute 10minute... 1day 1week 1month
        xl支持:         5minute 10minute... 1day 1week 1month
        '''

        n    = int(''.join(c for c in frequency if c.isdigit()))
        freq = ''.join(c for c in frequency if c.isalpha())
        
        if freq not in ["minute", "day", "week", "month"]:
            raise RuntimeError(f"frequency error : {frequency}")
        
        if freq == "minute":

            try:
                return self._tencent.query_minute_prices(security, frequency, count=count)
            except Exception as e:
                logger.info(f"found exception {e}, try next api")
                
            try:
                return self._sina.query_prices(security, frequency=str(n)+"m", count=count)
            except Exception as e:
                logger.error(f"backup api failed with {e}")
                raise e

        elif freq in ["day", "week", "month"]:

            if n != 1:
                raise RuntimeError("only support 1 day/week/month")

            try:
                return self._tencent.query_prices(security, frequency=freq, count=count)
            except Exception as e:
                logger.info(f"found exception {e}, try next api")
                
            try:
                # 日线1d=240m   周线1w=1200m  1月=7200m
                if freq == "1day":
                    freq = "240m"

                elif freq == "1week":
                    freq = "1200m"
                    
                elif freq == "1month":
                    freq = "7200m"

                else:
                    raise RuntimeError(f"unhandled {freq}")
                
                return self._sina.query_prices(security, frequency=freq, count=count)

            except Exception as e:
                logger.error(f"backup api failed with {e}")
                raise e

        else:
            raise RuntimeError(f"unhandled freq : {freq}")

    @security_checker
    def query_data_region(self, security: str, start: datetime, end: datetime) -> pd.DataFrame:
        '''
        以每日价格查询数据范围. 最大可回查590天
        NOTE: 目前仍不完备 可能出现起始时间不在start的问题? 不过这种情况只是假设
        '''
        if type(start) != datetime or type(end) != datetime:
            raise TypeError

        assert end.date() <= datetime.now().date()

        days = (datetime.now() - start).days + 200

        data = self.query_prices_untilnow(security, "1day", count=days)

        df = data.query('index >= @start and index <= @end')
        if df.index[0] > start:
            logger.warning("exceed the limit of API(590 count), adjusted the start time")

        return df 


api = Api()
            

if __name__ == "__main__":
    # print(api.query_prices_untilnow("sh605577", "1minute", count=3))
    # print(api.query_prices_untilnow("sh605577", "5minute", count=3))
    # print(api.query_prices_untilnow("sh605577", "1day", count=3))
    # print(api.query_prices_untilnow("sh605577", "1week", count=3))
    # print(api.query_prices_untilnow("sh605577", "1month", count=3))

    print(api.query_data_region("sh605577", start=datetime(2022, 3, 9), end=datetime(2023, 5, 8)))
    # print(api.query_data_region("sh605577", start=datetime(2021, 3, 9), end=datetime.now()))