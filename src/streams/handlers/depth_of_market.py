from streams.tasks import task_diff_book_depth
from streams.models import TaskManagement


class DepthOfMarket:
    def __init__(self):
        pass

    def start(self, symbol: str):
        codename = f'diff_book_depth_{symbol}'.lower()
        task_management, _ = TaskManagement.objects.get_or_create(codename=codename)
        if task_management.is_working:
            # TODO LOG уже запущена
            return
        task_management.is_working = True
        task_management.save(update_fields=['is_working'])
        task_diff_book_depth.delay(symbol)

        return True

    def stop(self, symbol: str):
        codename = f'diff_book_depth_{symbol}'.lower()
        try:
            task_management = TaskManagement.objects.get(codename=codename)
            task_management.is_working = False
            task_management.save(update_fields=['is_working'])
            return True
        except TaskManagement.DoesNotExist:
            return
