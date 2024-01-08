import numpy as np
import plotly.graph_objects as go

from logging import getLogger
from typing import NamedTuple

from quantfreedom.helper_funcs import cart_product
from quantfreedom.indicators.tv_indicators import sma_tv
from quantfreedom.enums import CandleBodyType
from quantfreedom.strategies.strategy import Strategy

logger = getLogger("info")


class IndicatorSettingsArrays(NamedTuple):
    sma_fast_length: np.array
    sma_slow_length: np.array


class SMACrossing(Strategy):
    def __init__(
        self,
        long_short: str,
        sma_fast_length: np.array,
        sma_slow_length: np.array,
    ) -> None:
        self.long_short = long_short

        cart_arrays = cart_product(
            IndicatorSettingsArrays(
                sma_fast_length=sma_fast_length,
                sma_slow_length=sma_slow_length,
            )
        )

        sma_fast_length = cart_arrays[0].astype(np.int_)
        sma_slow_length = cart_arrays[1].astype(np.int_)

        sma_bools = sma_fast_length < sma_slow_length

        self.indicator_settings_arrays: IndicatorSettingsArrays = IndicatorSettingsArrays(
            sma_fast_length=sma_fast_length[sma_bools],
            sma_slow_length=sma_slow_length[sma_bools],
        )

        if long_short == "long":
            self.set_entries_exits_array = self.long_set_entries_exits_array
            self.log_indicator_settings = self.long_log_indicator_settings
            self.entry_message = self.long_entry_message
        else:
            self.set_entries_exits_array = self.short_set_entries_exits_array
            self.log_indicator_settings = self.short_log_indicator_settings
            self.entry_message = self.short_entry_message

    #######################################################
    #######################################################
    #######################################################
    ##################      Long     ######################
    ##################      Long     ######################
    ##################      Long     ######################
    #######################################################
    #######################################################
    #######################################################

    def long_set_entries_exits_array(
        self,
        candles: np.array,
        ind_set_index: int,
    ):
        try:
            closes = candles[:, CandleBodyType.Close]

            # sma fast
            self.sma_fast_length = self.indicator_settings_arrays.sma_fast_length[ind_set_index]
            sma_fast = sma_tv(
                source=closes,
                length=self.sma_fast_length,
            )

            self.sma_fast = np.around(sma_fast, 2)

            self.prev_sma_fast = np.roll(self.sma_fast, 1)
            self.prev_sma_fast[0] = np.nan
            logger.info(f"Created sma_fast sma_fast_length= {self.sma_fast_length}")

            # sma slow
            self.sma_slow_length = self.indicator_settings_arrays.sma_slow_length[ind_set_index]
            sma_slow = sma_tv(
                source=closes,
                length=self.sma_slow_length,
            )

            self.sma_slow = np.around(sma_slow, 2)

            self.prev_sma_slow = np.roll(self.sma_slow, 1)
            self.prev_sma_slow[0] = np.nan
            logger.info(f"Created sma_slow sma_slow_length= {self.sma_slow_length}")

            # Entries
            self.entries = (self.prev_sma_fast < self.prev_sma_slow) & (self.sma_fast > self.sma_slow)
            self.cross_above_signal = np.where(self.entries, sma_fast, np.nan)
            logger.debug("Created entries and cross above signals")

            # Exits
            exits = (self.prev_sma_fast > self.prev_sma_slow) & (self.sma_fast < self.sma_slow)
            self.cross_below_signal = np.where(exits, sma_fast, np.nan)
            self.exit_prices = np.roll(np.where(exits, closes, np.nan), 1)
            logger.debug("Created exit prices and cross below signals")

        except Exception as e:
            logger.error(f"Exception long_set_entries_exits_array -> {e}")
            raise Exception(f"Exception long_set_entries_exits_array -> {e}")

    def long_log_indicator_settings(
        self,
        ind_set_index: int,
    ):
        logger.info(
            f"Indicator Settings Index= {ind_set_index}\
            \nsma_fast_length= {self.sma_fast_length}\
            \nsma_slow_length= {self.sma_slow_length}"
        )

    def long_entry_message(
        self,
        bar_index: int,
    ):
        logger.info("\n\n")
        logger.info("Entry time!!! prev_sma_fast < prev_sma_slow & sma_fast > sma_slow")
        logger.info(
            f"{self.prev_sma_fast[bar_index]} < {self.prev_sma_slow[bar_index]} & {self.sma_fast[bar_index]} > {self.sma_slow[bar_index]}"
        )
