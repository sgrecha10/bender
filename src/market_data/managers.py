import pandas as pd
from django.db import models, connections
from django.db.models.constants import OnConflict


class KlineManager(models.Manager):
    pass


class KlineQuerySet(models.QuerySet):
    def to_dataframe(self, *args) -> pd.DataFrame:
        """Возвращает DataFrame"""
        queryset = self.values_list(*args)
        df = pd.DataFrame(
            data=queryset,
            columns=[*args],
        )
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
