from strategies.models import Strategy, StrategyResult
from decimal import Decimal
from datetime import datetime
from market_data.models import Kline
from typing import Optional


class StrategyFirstBackend:
    """ Алгоритм

    Тестирование:
    1. Получаем цену или свечу (для тестирования)
    2. Свечу надо привести к цене. Получится две цены - мин и макс. Для покупок проверяем мин, для продаж - макс.
    3. Находим точки открытия позиции:
    Пересечение ценой значения МА за предыдущую свечку. Если снизу вверх - то сигнал на покупку, сверху вниз - на продажу.
    4. Объем инструмента для входа в сделку - фиксированный, из настроек стратегии. Открываем "по рынку".
    5. Записываем в StrategyResult цены, по которым реально куплен/продан инструмент.
    6. От цены открытия сделки рассчитываем StopLoss, TakeProfit.
    7. Если позиция открывается, то ставится флаг has_long_position, has_short_position.В этом случае пересечение МА не проверяется, проверяется достижения SL, TP
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

        self.has_long_position = False
        self.has_short_position = False
        self.stop_loss = None
        self.take_profit = None

    def make_buy(self, quantity: Decimal, price: Decimal = None) -> tuple[Decimal, bool]:
        """ Покупаем инструмент
        Если price отсутствует, покупаем по рынку (не реализовано)
        Возвращаем реальную цену покупки и флаг успеха.
        """
        return price, True

    def make_sell(self, quantity: Decimal, price: Decimal = None) -> tuple[Decimal, bool]:
        """ Продаем инструмент
        """
        return price, True

    def get_stop_loss(self, buy: Decimal = None, sell: Decimal = None) -> Optional[Decimal]:
        """ Возвращает цену стоп лосса
        :param buy: - цена входа в длинную сделку
        :param sell: - цена входа в короткую сделку,
        """
        if buy:
            return buy - 10
        if sell:
            return sell + 10

    def get_take_profit(self, buy: Decimal = None, sell: Decimal = None) -> Optional[Decimal]:
        """ Возвращает цену тейк профита
        :param buy: - цена входа в длинную сделку
        :param sell: - цена входа в короткую сделку,
        """
        if buy:
            return buy + 10
        if sell:
            return sell - 10

    def check_price(self, idx: datetime, price: Decimal):
        """ Получает цену и timestamp, открывает/закрывает позицию """

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

        # получаем предыдущее значение цены
        previous_close_price = self.kline_df.loc[previous_index, 'close_price']

        # проверяем, открыта ли уже позиция
        if self.has_long_position or self.has_short_position:
            # позиция открыта. проверяем, что цена дошла до стоп лосса или тейк профита
            pass

        else:
            # позиции нет. проверяем, что цена пересекла значение МА за предыдущую свечу
            if price >= previous_ma_value > previous_close_price:
                # цена пересекла снизу вверх
                real_price, is_ok = self.make_buy(quantity=Decimal(1.0), price=previous_ma_value)
                if is_ok:
                    # self.has_long_position = True
                    self.stop_loss = self.get_stop_loss(buy=real_price)
                    self.take_profit = self.get_take_profit(buy=real_price)
                    StrategyResult.objects.create(
                        strategy_id=self.strategy.id,
                        kline=self.kline_qs.get(open_time=idx),
                        buy=real_price,
                    )

            if price <= previous_ma_value < previous_close_price:
                # цена пересекла сверху вниз
                real_price, is_ok = self.make_sell(quantity=Decimal(1.0), price=previous_ma_value)
                if is_ok:
                    # self.has_short_position = True
                    self.stop_loss = self.get_stop_loss(sell=real_price)
                    self.take_profit = self.get_take_profit(sell=real_price)
                    StrategyResult.objects.create(
                        strategy_id=self.strategy.id,
                        kline=self.kline_qs.get(open_time=idx),
                        sell=real_price,
                    )
