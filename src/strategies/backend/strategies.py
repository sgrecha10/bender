from datetime import datetime
from decimal import Decimal
from typing import Optional

from PIL.ImageCms import Direction

from market_data.models import Kline
from strategies.models import Strategy, StrategyResult


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
    strategy_codename = Strategy.Codename.STRATEGY_1
    moving_average_codename_1 = 'MA_1'  # поиск точки входа
    moving_average_codename_2 = 'MA_2'  # определение тренда
    standard_deviation_codename = 'SD_2'

    def __init__(self):
        self.strategy = Strategy.objects.get(codename=self.strategy_codename)
        self.moving_average_1 = self.strategy.movingaverage_set.get(codename=self.moving_average_codename_1)
        self.moving_average_2 = self.strategy.movingaverage_set.get(codename=self.moving_average_codename_2)
        self.standard_deviation = self.strategy.standarddeviation_set.get(codename=self.standard_deviation_codename)

        self.kline_df = Kline.objects.filter(
            symbol=self.strategy.base_symbol,
            open_time__gte=self.strategy.start_time,
            open_time__lte=self.strategy.end_time,
        ).group_by_interval().to_dataframe(index='open_time_group')

        moving_average_source_df_1 = self.moving_average_1.get_source_df(self.kline_df)
        moving_average_source_df_2 = self.moving_average_2.get_source_df(self.kline_df)
        standard_deviation_source_df = self.standard_deviation.get_source_df(self.kline_df)
        moving_average_source_df = moving_average_source_df_1.combine_first(moving_average_source_df_2)
        self.source_df = moving_average_source_df.combine_first(standard_deviation_source_df)

        self.has_long_position = False
        self.has_short_position = False

        self.stop_loss = None
        self.take_profit = None

        self.trend_up = False
        self.trend_down = False

    def _check_init_params(self) -> Optional[str]:
        """ Проверяем, что все необходимые данные инициализированы
        :return  если not None, то чего то не хватает
        """
        return

    def make_buy(self,
                 state: str,
                 quantity: Decimal = None,
                 price: Decimal = None,
                 deal_time: datetime = None) -> tuple[Decimal, bool]:
        """ Покупаем инструмент
        1. Если price отсутствует, покупаем по рынку (не реализовано)
        Возвращаем реальную цену покупки и флаг успеха.
        2. Если quantity отсутствует, значит тестовая сделка.
        3. Если deal_time отсутствует, значит реальная сделка.
        """
        is_ok = True  # результат реальной сделки
        if is_ok:
            StrategyResult.objects.create(
                strategy_id=self.strategy.id,
                deal_time=deal_time,
                buy=price,
                state=state,
            )
            return price, True

    def make_sell(self,
                  state: str,
                  quantity: Decimal = None,
                  price: Decimal = None,
                  deal_time: datetime = None) -> tuple[Decimal, bool]:
        """ Продаем инструмент

        Что бы сделать нормально, надо записывать в StrategyResult текущее время.
        Но при построении чарта нужно будет приводить это время к соответствующей свече.
        Потом сделаю.
        """
        is_ok = True  # результат реальной сделки
        if is_ok:
            StrategyResult.objects.create(
                strategy_id=self.strategy.id,
                deal_time=deal_time,
                sell=price,
                state=state,
            )
            return price, True

    def get_stop_loss(self, sd: Decimal, buy: Decimal = None, sell: Decimal = None):
        """ Устанавливает цену стоп лосса

        :param sd: standard_deviation_value для расчета
        :param buy: - цена входа в длинную сделку
        :param sell: - цена входа в короткую сделку,
        """
        if buy:
            self.stop_loss = buy - sd * self.strategy.stop_loss_factor
        if sell:
            self.stop_loss = sell + sd * self.strategy.stop_loss_factor

    def get_take_profit(self, sd: Decimal, buy: Decimal = None, sell: Decimal = None):
        """ Устанавливает цену тейк профита

        :param sd:
        :param buy: - цена входа в длинную сделку
        :param sell: - цена входа в короткую сделку,
        """
        if buy:
            self.take_profit = buy + sd * self.strategy.take_profit_factor
        if sell:
            self.take_profit = sell - sd * self.strategy.take_profit_factor

    def run_step(self, deal_time: datetime, price: Decimal):
        """ Получает цену и timestamp, открывает/закрывает позицию """

        # проверяем, что все инициализировано
        if error_msg := self._check_init_params():
            return error_msg

        # приводим deal_time к размеру текущего интервала kline_df
        idx = deal_time

        # находим позицию индекса текущей свечи, если 0 то пропускаем итерацию.
        # потому что надо получить МА на предыдущую свечу
        if not (index_position := self.kline_df.index.get_loc(idx)):
            return

        previous_index = self.kline_df.index[index_position - 1]

        previous_ma_value = self.moving_average_1.get_value_by_index(
            index=previous_index,
            source_df=self.source_df,
        )
        previous_sd_value = self.standard_deviation.get_value_by_index(
            index=previous_index,
            source_df=self.source_df,
        )

        # узнаем текущий тренд
        trend = self.get_trend(
            idx=previous_index,
            price=price,
        )

        # это не надо проверять тут, это надо проверять в self._check_init_params
        if not (previous_ma_value and previous_sd_value):
            return False

        # получаем предыдущее значение цены
        previous_close_price = self.kline_df.loc[previous_index, 'close_price']

        # открыта позиция в лонг
        if self.has_long_position:
            if price >= self.take_profit:
                _, is_ok = self.make_sell(
                    state=StrategyResult.State.PROFIT,
                    price=price,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_long_position = False
                    self.stop_loss = None
                    self.take_profit = None

            elif price <= self.stop_loss:
                _, is_ok = self.make_sell(
                    state=StrategyResult.State.LOSS,
                    price=price,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_long_position = False
                    self.stop_loss = None
                    self.take_profit = None

        elif self.has_short_position:
            if price <= self.take_profit:
                _, is_ok = self.make_buy(
                    state=StrategyResult.State.PROFIT,
                    price=price,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_short_position = False
                    self.stop_loss = None
                    self.take_profit = None

            elif price >= self.stop_loss:
                _, is_ok = self.make_buy(
                    state=StrategyResult.State.LOSS,
                    price=price,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_short_position = False
                    self.stop_loss = None
                    self.take_profit = None

        else:
            # Позиции нет. Проверяем, что цена пересекла значение МА за предыдущую свечу
            if price >= previous_ma_value > previous_close_price:
                # цена пересекла снизу вверх

                if self.strategy.direction_deals == Strategy.Direction.ONLY_SELL:
                    return

                if self.strategy.direction_deals == Strategy.Direction.DEFAULT and trend == 'DOWN':
                    return

                real_price, is_ok = self.make_buy(
                    state=StrategyResult.State.OPEN,
                    price=previous_ma_value,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_long_position = True
                    self.get_stop_loss(sd=previous_sd_value, buy=real_price)
                    self.get_take_profit(sd=previous_sd_value, buy=real_price)

            if price <= previous_ma_value < previous_close_price:
                # цена пересекла сверху вниз

                if self.strategy.direction_deals == Strategy.Direction.ONLY_BUY:
                    return

                if self.strategy.direction_deals == Strategy.Direction.DEFAULT and trend == 'UP':
                    return

                real_price, is_ok = self.make_sell(
                    state=StrategyResult.State.OPEN,
                    price=previous_ma_value,
                    deal_time=deal_time,
                )
                if is_ok:
                    self.has_short_position = True
                    self.get_stop_loss(sd=previous_sd_value, sell=real_price)
                    self.get_take_profit(sd=previous_sd_value, sell=real_price)

    def close_all_position(self, idx: datetime, price: Decimal = None):
        """ Закрывает все позиции
        :param idx:
        :param price: если отсутствует, то закрывает по рыночной стоимости
        """
        if self.has_long_position:
            self.make_sell(state=StrategyResult.State.UNKNOWN, price=price, deal_time=idx)
            self.has_long_position = False

        elif self.has_short_position:
            self.make_buy(state=StrategyResult.State.UNKNOWN, price=price, deal_time=idx)
            self.has_short_position = False

    def get_trend(self, idx: datetime, price: Decimal) -> str:
        """ Возвращает направление тренда
        Сравнивает текущую цену с предыдущим значением MA, если выше - растем, если ниже - падаем

        :param idx: предыдущий индекс, на который вычисляем МА
        :param price: текущая цена для сравнения
        """

        previous_ma_value = self.moving_average_2.get_value_by_index(
            index=idx,
            source_df=self.source_df,
        )
        return 'UP' if price >= previous_ma_value else 'DOWN'
