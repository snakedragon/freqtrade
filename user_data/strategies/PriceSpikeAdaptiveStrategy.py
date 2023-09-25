# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union
import sys
sys.path.append("/home/al/source/freqtrade")

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class PriceSpikeStrategy(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # 一轮波峰波谷的移动距离平均值， 大于这个值，可以买入，小于这个值，不买入。
    buy_move_distance_round = DecimalParameter(0.001, 0.006, default=0.003, decimals=3, space='buy',optimize=True, load=True)
    # 如果一个方向上，连续移动n个klines，可以开始进入信号评估
    buy_move_klines_entry = IntParameter(2, 4, default=3, space='buy',optimize=True, load=True)
    # 在一个方向上，buy_move_klines_entry满足的情况下， 移动距离为 平均移动距离的 0.2-0.6，可以进入信号评估
    buy_move_distance_entry = DecimalParameter(0.2, 0.6, default=0.3, decimals=1, space='buy',optimize=True, load=True)


    @property
    def plot_config(self):
        return {
            # Main plot indicators (Moving averages, ...)
            'main_plot': {
                'tema': {},
                'sar': {'color': 'white'},
            },
            'subplots': {
                # Subplots - each dict defines one additional plot
                "MACD": {
                    'macd': {'color': 'blue'},
                    'macdsignal': {'color': 'orange'},
                },
                "RSI": {
                    'rsi': {'color': 'red'},
                }
            }
        }

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str],
                 side: str, **kwargs) -> float:
        return 100.0
    

    def calcualte_peak_vally_stats(self,dataframe: DataFrame,metadata:dict)-> DataFrame:
            up_distance = []
            down_distance = []

            up_index_interval = []
            down_index_interval = []

            peak_df = dataframe.loc[(dataframe['peak_vally_bar']==1),:]
            vally_df = dataframe.loc[(dataframe['peak_vally_bar']==-1),:]

            start_index = peak_df.index[0] if peak_df.index[0] < vally_df.index[0] else vally_df.index[0]
            peak_first = (peak_df.index[0] < vally_df.index[0])

            if peak_first:
                for i, peak_idx in enumerate(peak_df.index):
                    peak_close_value = peak_df[peak_idx,'close']
                    if i+1 > len(vally_df.index):
                        break
                    vally_idx = vally_df.index[i]
                    if vally_idx < peak_idx:
                        raise ValueError("vally idx must follow the peak idx in peak first  data mode!")
                    vally_close_value = vally_df[vally_idx,'close']
                    down_distance.append(2.0*abs(vally_close_value-peak_close_value)/(vally_close_value+peak_close_value))
                    down_index_interval.append(vally_idx-peak_idx)

                    if i+1>len(peak_df.index):
                        break
                    next_peak_idx = peak_df.index[i+1]
                    next_peak_close_value = peak_df[next_peak_idx,'close']
                    up_distance.append(2.0*abs(next_peak_close_value-vally_close_value)/(next_peak_close_value+vally_close_value))
                    up_index_interval.append(next_peak_idx-vally_idx)
            else:
                for i, vally_idx in enumerate(vally_df.index):
                    vally_close_value = vally_df[vally_idx,'close']
                    if i+1 > len(peak_df.index):
                        break
                    peak_idx = peak_df.index[i]
                    if vally_idx > peak_idx:
                        raise ValueError("vally idx must follow the peak idx in vally first data mode!")
                    peak_close_value = peak_df[peak_idx,'close']
                    up_distance.append(2.0*abs(vally_close_value-peak_close_value)/(peak_close_value+vally_close_value))
                    up_index_interval.append(peak_idx-vally_idx)
                    if i+1>len(vally_df.index):
                        break
                    next_vally_idx = vally_df.index[i+1]
                    next_vally_close_value = vally_df[next_vally_idx,'close']
                    down_distance.append(2.0*abs(next_vally_close_value-peak_close_value)/(next_vally_close_value+peak_close_value))
                    down_index_interval.append(next_vally_idx-peak_idx)
                    

            up_distance_avg = np.mean(up_distance)
            down_distance_avg = np.mean(down_distance)
            up_down_distance_avg = np.mean(up_distance+down_distance)
            up_klines_avg = np.mean(up_index_interval)
            down_klines_avg = np.mean(down_index_interval)
            up_down_klines_avg = np.mean(up_index_interval + down_index_interval)

            stats = {
                'up_avg': up_distance_avg,
                'down_avg': down_distance_avg,
                'up_down_avg': up_down_distance_avg,
                'up_kl_avg': up_klines_avg,
                'down_kl_avg': down_klines_avg,
                'up_down_kl_avg': up_down_klines_avg
            }

            return stats


    def detect_klines_peak_vally_bar(self,dataframe: DataFrame, metadata:dict)-> DataFrame:
        """
        detect peak and vally bar use the 'close' value , 
        if peak, mark as value 1, peak means current_bar > left_bar && current_bar > left_bar
        vally marked as value -1, vally means current_bar < left_bar && current_bar < left_bar
        """
        dataframe['peak_vally_bar'] = 0
        dataframe['high_close_avg'] = (0.2*dataframe['close'] + 0.8*dataframe['high'])

        dataframe.loc[
            (   
                (dataframe['date'].values < dataframe['date'].values[-2]) &   # values before last two shift
                (dataframe['high_close_avg'] > dataframe['high_close_avg'].shift(1)) &  # high_close 大于左一
                (dataframe['high_close_avg'] > dataframe['high_close_avg'].shift(2)) &  # high_close 大于左二
                (dataframe['high_close_avg'] > dataframe['high_close_avg'].shift(-1)) & # high_close 大于右一
                (dataframe['high_close_avg'] > dataframe['high_close_avg'].shift(-2)) &   # high_close 大于右2
                (dataframe['high_close_avg'].shift(1) > dataframe['high_close_avg'].shift(2)) & 
                (dataframe['high_close_avg'].shift(-1) > dataframe['high_close_avg'].shift(-2))
            ),
            'peak_vally_bar'] = 1

        dataframe.loc[
            (
                (dataframe['date'].values < dataframe['date'].values[-2]) &   # 取值后2之前
                (dataframe['high_close_avg'] < dataframe['high_close_avg'].shift(1)) &  # high_close 小于左一
                (dataframe['high_close_avg'] < dataframe['high_close_avg'].shift(2)) &  # high_close 小于左二
                (dataframe['high_close_avg'] < dataframe['high_close_avg'].shift(-1)) & # high_close 小于右一
                (dataframe['high_close_avg'] < dataframe['high_close_avg'].shift(-2)) &   # high_close 小于右2
                (dataframe['high_close_avg'].shift(1) < dataframe['high_close_avg'].shift(2)) & 
                (dataframe['high_close_avg'].shift(-1) < dataframe['high_close_avg'].shift(-2))
            ),
            'peak_vally_bar'
        ] = -1

        return dataframe
        


    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # Momentum Indicators
        # ------------------------------------
        # EMA - Exponential Moving Average
        dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)
        # dataframe['ema21'] = ta.EMA(dataframe, timeperiod=21)
        # dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        # dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        dataframe = self.detect_klines_peak_vally_bar(dataframe,metadata)

    
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """

        stats = self.calcualte_peak_vally_stats(dataframe,metadata)

        up_avg = stats['up_avg']
        down_avg = stats['down_avg']
        up_down_avg = stats['up_down_avg']
        up_kl_avg = stats['up_kl_avg']
        down_kl_avg = stats['down_kl_avg']
        up_down_kl_avg = stats['up_down_kl_avg']


        dataframe.loc[
            (
                # (dataframe['close'] >= dataframe['ema5']) &                     # 站上3周期平均线
                (dataframe['close'] >= dataframe['open']) &                     # k-0 bar 上涨
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &    # k-1 bar 上涨
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &    # k-2 bar 上涨
                (dataframe['close'].shift(3) < dataframe['open'].shift(3)) &    # k-3 bar 下跌
                (dataframe['close'] > dataframe['close'].shift(1)) &            # close价格上升
                (dataframe['close'].shift(1) > dataframe['close'].shift(2)) &   # close价格上升
                ((dataframe['close']-dataframe['open'].shift(2)) < 0.0075*self.price_spike_threshold_buy.value*dataframe['close']) &  # 上涨不能太快
                ((dataframe['close']-dataframe['open'].shift(2)) > 0.001*self.price_spike_threshold_buy.value*dataframe['close']) &  # 上涨不能太慢
                (dataframe['volume'] > 0)                                      # 有成交量
            ),
            'enter_long'] = 1


        dataframe.loc[
            (
                # (dataframe['close'] < dataframe['ema5']) &                      # 落入3周期平均线
                (dataframe['close'] < dataframe['open']) &                      # k-0 bar 下跌
                (dataframe['close'].shift(1) < dataframe['open'].shift(1)) &    # k-1 bar 下跌
                (dataframe['close'].shift(2) < dataframe['open'].shift(2)) &    # k-2 bar 下跌
                (dataframe['close'].shift(3) > dataframe['open'].shift(3)) &    # k-3 bar 上涨
                (dataframe['close'] < dataframe['close'].shift(1)) &            # close价格下跌
                (dataframe['close'].shift(1) < dataframe['close'].shift(2)) &   # close价格下跌
                ((dataframe['close']-dataframe['open'].shift(1)) > 0.0075*self.price_spike_threshold_buy.value*dataframe['close']) &  # 下跌不能太快
                ((dataframe['close']-dataframe['open'].shift(1)) < 0.001*self.price_spike_threshold_buy.value*dataframe['close']) &  # 下跌不能太慢
                (dataframe['volume'] > 0)                                      # 有成交量
            ),
            'enter_short'] = 1


        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        # dataframe.loc[
        #     (
        #         (qtpylib.crossed_above(dataframe['rsi'], self.sell_rsi.value)) &  # Signal: RSI crosses above sell_rsi
        #         (dataframe['tema'] > dataframe['bb_middleband']) &  # Guard: tema above BB middle
        #         (dataframe['tema'] < dataframe['tema'].shift(1)) &  # Guard: tema is falling
        #         (dataframe['volume'] > 0)  # Make sure Volume is not 0
        #     ),
        #     'exit_long'] = 1
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)
        """
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['rsi'], self.buy_rsi.value)) &  # Signal: RSI crosses above buy_rsi
                (dataframe['tema'] <= dataframe['bb_middleband']) &  # Guard: tema below BB middle
                (dataframe['tema'] > dataframe['tema'].shift(1)) &  # Guard: tema is raising
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_short'] = 1
        """
        return dataframe
    