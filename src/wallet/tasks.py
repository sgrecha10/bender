import requests

from bender.celery_entry import app


@app.task(
    bind=True,
    autoretry_for=(
        requests.ConnectionError,
        requests.ReadTimeout,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def debug_task(self):
    res = 'I`m OK'
    print(res)
    return res
