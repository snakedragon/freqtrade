# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

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

    # Optimal timeframe for the strategy.
    timeframe = '1m'

    # Can this strategy go short?
    can_short: bool = True

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "10": 0.015,
        "5": 0.03,
        "3": 0.045,
        "2": 0.06,
        "1": 0.08,
        "0": 0.15
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.03
    # Trailing stoploss
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.05

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 10

    # Strategy parameters
    price_spike_threshold_buy = DecimalParameter(0.5, 6.0, default=0.6, decimals=1, space='buy', optimize=True)
    price_spike_threshold_sell = DecimalParameter(-6.0, -0.5, default=-0.6, decimals=1, space='sell', optimize=True)

    # Optional order type mapping.
    order_types = {
        'entry': 'market',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

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

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
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
    