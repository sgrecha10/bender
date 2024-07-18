from django.urls import path
from .views import CandleView


urlpatterns = [
    path('candles', CandleView.as_view(), name='candles'),
]
