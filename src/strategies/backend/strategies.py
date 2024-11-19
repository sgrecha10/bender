from strategies.models import Strategy, StrategyResult
from decimal import Decimal
from datetime import datetime
from market_data.models import Kline


class StrategyFirstBackend:
    """ Алгоритм

    1. Получаем цену или свечу (для тестирования)
    2. Свечу надо привести к цене. Получится две цены - мин и макс. Для покупок проверяем мин, для продаж - макс.
    3. Находим точки открытия позиции: пересечение ценой МА. Если снизу вверх - то сигнал на покупку, сверху вниз - на продажу.
    4. Объем инструмента для входа в сделку - фиксированный, из настроек стратегии. Открываем "по рынку".
    5. Записываем в StrategyResult цены, по которым реально куплен/продан инструмент.
    6. От цены открытия сделки рассчитываем StopLoss, TakeProfit.
    7. Если позиция открывается, то ставится флаг is_long_position, is_short_position.В этом случае пересечение МА не проверяется, проверяется достижения SL, TP
    8. Новая поза открывается только после закрытия открытой.
    9. Все покупки/продажи записываем в StrategyResult

    StopLoss, TakeProfit - коэфициент к среднеквадратическому отклонению.
    """

    def __init__(self):
        self.strategy_codename = Strategy.Codename.STRATEGY_1
        self.strategy = Strategy.objects.get(codename=self.strategy_codename)
        self.moving_average = self.strategy.movingaverage_set.first()

        self.kline_qs = Kline.objects.filter(
            symbol=self.strategy.base_symbol,
            open_time__gte=self.strategy.start_time,
            open_time__lte=self.strategy.end_time,
        )
        self.kline_df = self.kline_qs.group_by_interval().to_dataframe(index='open_time_group')
        self.source_df = self.moving_average.get_source_df(self.kline_df)

        self.is_long_position = False
        self.is_short_position = False

    def check_kandle(self, idx: datetime, high_price: Decimal, low_price: Decimal):
        """ Получает свечку, вызывается при тестировании стратегии """

        # находим позицию индекса текущей свечи, если 0 то пропускаем итерацию
        if not (index_position := self.kline_df.index.get_loc(idx)):
            return

        previous_index = self.kline_df.index[index_position - 1]

        previous_ma_value = self.moving_average.get_value_by_index(
            index=previous_index,
            source_df=self.source_df,
        )

        if not previous_ma_value:
            return False

        # проверяем, что цена пересекла значение MA за предыдущую свечу
        if high_price > previous_ma_value > low_price:

            # Проверяем, пересечение снизу или сверху, открываем позицию sell or buy
            previous_close_price = self.kline_df.loc[previous_index, 'close_price']
            if previous_close_price < previous_ma_value:
                # идем вверх, покупаем
                StrategyResult.objects.create(
                    strategy_id=self.strategy.id,
                    kline=self.kline_qs.get(open_time=idx),
                    buy=previous_ma_value,
                )
            else:
                # идем вниз, продаем
                StrategyResult.objects.create(
                    strategy_id=self.strategy.id,
                    kline=self.kline_qs.get(open_time=idx),
                    sell=previous_ma_value,
                )

    def check_price(self):
        """ Получает цену, для рабочего режима """
        pass
