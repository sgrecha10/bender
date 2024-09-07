from django.db.models import TextChoices


class IntervalCodename(TextChoices):
    MINUTE_1 = '1m', 'MINUTE_1'
    MINUTE_3 = '3m', 'MINUTE_3'
    MINUTE_5 = '5m', 'MINUTE_5'
    MINUTE_15 = '15m', 'MINUTE_15'
    MINUTE_30 = '30m', 'MINUTE_30'
    HOUR_1 = '1h', 'HOUR_1'
    HOUR_2 = '2h', 'HOUR_2'
    HOUR_4 = '4h', 'HOUR_4'
    HOUR_6 = '6h', 'HOUR_6'
    HOUR_8 = '8h', 'HOUR_8'
    HOUR_12 = '12h', 'HOUR_12'
    DAY_1 = '1d', 'DAY_1'
    DAY_3 = '3d', 'DAY_3'
    WEEK_1 = '1w', 'WEEK_1'
    MONTH_1 = '1M', 'MONTH_1'
    YEAR_1 = '1Y', 'YEAR_1'


"""Разрешенные интервалы для конвертации DataFrame"""
ALLOWED_INTERVAL = [
    'MINUTE_1',
    'HOUR_1',
    'DAY_1',
    'MONTH_1',
    'YEAR_1',
]
