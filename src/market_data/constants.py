from django.db.models import TextChoices


class Interval(TextChoices):
    MINUTE_1 = '1min'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1D'
    DAY_3 = '3d'
    WEEK_1 = '1W'
    MONTH_1 = '1M'
    YEAR_1 = '1A'


class AllowedInterval(TextChoices):
    MINUTE_1 = '1min'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1D'
    WEEK_1 = '1W'
    MONTH_1 = '1M'
    YEAR_1 = '1A'


MAP_MINUTE_COUNT = {
    Interval.MINUTE_1: 1,
    Interval.HOUR_1: 60,
    Interval.HOUR_2: 60 * 2,
    Interval.HOUR_4: 60 * 4,
    Interval.HOUR_6: 60 * 6,
    Interval.HOUR_8: 60 * 8,
    Interval.HOUR_12: 60 * 12,
    Interval.DAY_1: 60 * 24,
    Interval.WEEK_1: 60 * 24 * 7,
    Interval.MONTH_1: 60 * 24 * 30,
    Interval.YEAR_1: 60 * 24 * 365,
}
