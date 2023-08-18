from bender.celery_entry import app


@app.task(bind=True)
def debug_task(self):
    # print(f'Request: {self.request!r}')
    res = 'I`m OK'
    print(res)
    return res
