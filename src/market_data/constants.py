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


INTERVAL_DURATION = {
    IntervalCodename.MINUTE_1.name: 1,
    IntervalCodename.MINUTE_3.name: 3,
    IntervalCodename.MINUTE_5.name: 5,
    IntervalCodename.MINUTE_15.name: 15,
    IntervalCodename.MINUTE_30.name: 30,
    IntervalCodename.HOUR_1.name: 60,
    IntervalCodename.HOUR_2.name: 120,
    IntervalCodename.HOUR_4.name: 240,
    IntervalCodename.HOUR_6.name: 360,
    IntervalCodename.HOUR_8.name: 480,
    IntervalCodename.HOUR_12.name: 720,
    IntervalCodename.DAY_1.name: 1440,
    IntervalCodename.DAY_3.name: 4320,
    IntervalCodename.WEEK_1.name: 10080,
    IntervalCodename.MONTH_1.name: 43200,  # 30d
    IntervalCodename.YEAR_1.name: 525600,
}


"""Разрешенные интервалы для конвертации DataFrame"""
ALLOWED_INTERVAL = [
    'MINUTE_1',
    'HOUR_1',
    'DAY_1',
    'MONTH_1',
    'YEAR_1',
]
