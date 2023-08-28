from django.apps import AppConfig


class StreamsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "streams"

    def ready(self):
        pass
        # print('grecha_start_streams_config')
        # from streams.handlers import start_stream
        # start_stream()
