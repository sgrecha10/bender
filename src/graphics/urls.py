from django.urls import path
from .views import CandleView

# TODO  deprecated
urlpatterns = [
    path('candles_', CandleView.as_view(), name='candles_'),
]
