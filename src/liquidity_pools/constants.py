from django.db.models import TextChoices


class Interval(TextChoices):
    MINUTE_1 = '1min'
    MINUTE_3 = '3min'
    MINUTE_5 = '5min'
    MINUTE_15 = '15min'
    MINUTE_30 = '30min'
    HOUR_1 = '1H'
    HOUR_2 = '2H'
    HOUR_4 = '4H'
    HOUR_6 = '6H'
    HOUR_8 = '8H'
    HOUR_12 = '12H'
    DAY_1 = '1D'
    DAY_3 = '3D'
    WEEK_1 = '1W'
    MONTH_1 = '1M'
    YEAR_1 = '1A'


MAP_MINUTE_COUNT = {
    Interval.MINUTE_1: 1,
    Interval.MINUTE_3: 3,
    Interval.MINUTE_5: 5,
    Interval.MINUTE_15: 15,
    Interval.MINUTE_30: 30,
    Interval.HOUR_1: 60,
    Interval.HOUR_2: 60 * 2,
    Interval.HOUR_4: 60 * 4,
    Interval.HOUR_6: 60 * 6,
    Interval.HOUR_8: 60 * 8,
    Interval.HOUR_12: 60 * 12,
    Interval.DAY_1: 60 * 24,
    Interval.DAY_3: 60 * 24 * 3,
    Interval.WEEK_1: 60 * 24 * 7,
    Interval.MONTH_1: 60 * 24 * 30,
    Interval.YEAR_1: 60 * 24 * 365,
}
