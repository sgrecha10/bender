import pandas as pd
from django.db import models, connections
from django.db.models import F, Max, Window
from django.db.models.constants import OnConflict
from django.db.models.functions import Trunc, FirstValue

from .constants import Interval


class KlineManager(models.Manager):
    pass


class KlineQuerySet(models.QuerySet):
    def group_by_interval(self, interval: str = Interval.MINUTE_1.value) -> models.QuerySet:
        """Группирует минутные свечи в нужный interval"""
        interval = str(interval)
        if interval == Interval.HOUR_1.value:
            kind = 'hour'
        elif interval == Interval.DAY_1.value:
            kind = 'day'
        elif interval == Interval.WEEK_1.value:
            kind = 'week'
        elif interval == Interval.MONTH_1.value:
            kind = 'month'
        elif interval == Interval.YEAR_1.value:
            kind = 'year'
        else:
            kind = 'minute'

        return self.annotate(
            open_time_group=Trunc(
                expression='open_time',
                kind=kind,
                output_field=models.DateTimeField(),
            ),
            open_price_tmp=models.Window(
                expression=FirstValue('open_price'),
                partition_by='open_time_group',
                order_by='open_time',
            ),
            high_price_tmp=Window(
                expression=Max('high_price'),
                partition_by='open_time_group',
            ),
            low_price_tmp=models.Window(
                expression=models.Min('low_price'),
                partition_by='open_time_group',
            ),
            close_price_tmp=models.Window(
                expression=FirstValue('close_price'),
                partition_by='open_time_group',
                order_by='-open_time',
            ),
            volume_tmp=models.Window(
                expression=models.Sum('volume'),
                partition_by='open_time_group',
            ),
        ).values('open_time_group').annotate(
            open_price=models.F('open_price_tmp'),
            high_price=F('high_price_tmp'),
            low_price=F('low_price_tmp'),
            close_price=F('close_price_tmp'),
            volume=models.F('volume_tmp'),
        ).distinct('open_time_group')

    def to_dataframe(self, index: str = None) -> pd.DataFrame:
        """Возвращает DataFrame"""
        annotation_fields = self.query.annotation_select.keys()
        queryset = self.values_list(*annotation_fields)
        df = pd.DataFrame(
            data=queryset,
            columns=[*annotation_fields],
        )
        if index:
            df.set_index(index, inplace=True, drop=True)
        return df

    def _batched_insert(
        self,
        objs,
        fields,
        batch_size,
        on_conflict=None,
        update_fields=None,
        unique_fields=None,
    ):
        """
        === Overridden for bulk_create(update_conflicts=True) returns ids.
        """
        connection = connections[self.db]
        ops = connection.ops
        max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
        inserted_rows = []
        bulk_return = connection.features.can_return_rows_from_bulk_insert
        for item in [objs[i : i + batch_size] for i in range(0, len(objs), batch_size)]:
            if bulk_return and (on_conflict is None or on_conflict == OnConflict.UPDATE):
                inserted_rows.extend(
                    self._insert(
                        item,
                        fields=fields,
                        using=self.db,
                        on_conflict=on_conflict,
                        update_fields=update_fields,
                        unique_fields=unique_fields,
                        returning_fields=self.model._meta.db_returning_fields,
                    )
                )
            else:
                self._insert(
                    item,
                    fields=fields,
                    using=self.db,
                    on_conflict=on_conflict,
                    update_fields=update_fields,
                    unique_fields=unique_fields,
                )
        return inserted_rows
