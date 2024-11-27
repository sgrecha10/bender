from django.db.models import TextChoices


class Interval(TextChoices):
    MINUTE_1 = '1m'
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
    DAY_1 = '1d'
    DAY_3 = '3d'
    WEEK_1 = '1w'
    MONTH_1 = '1M'
    YEAR_1 = '1Y'


class AllowedInterval(TextChoices):
    MINUTE_1 = '1m'
    HOUR_1 = '1h'
    DAY_1 = '1d'
    WEEK_1 = '1w'
    MONTH_1 = '1M'
    YEAR_1 = '1Y'

# """AllowedInterval"""
# items_dict = {
#     item.name: item.value for item in Interval
#     if item in [
#         Interval.MINUTE_1,
#         Interval.HOUR_1,
#         Interval.DAY_1,
#         Interval.WEEK_1,
#         Interval.MONTH_1,
#         Interval.YEAR_1,
#     ]
# }
# AllowedInterval = TextChoices('AllowedInterval', items_dict)


MAP_MINUTE_COUNT = {
    Interval.MINUTE_1: 1,
    Interval.HOUR_1: 60,
    Interval.DAY_1: 60 * 24,
    Interval.WEEK_1: 60 * 24 * 7,
    Interval.MONTH_1: 60 * 24 * 30,
    Interval.YEAR_1: 60 * 24 * 365,
}
