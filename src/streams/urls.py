from django.urls import path
from .views import HandlerTestView


urlpatterns = [
    path('', HandlerTestView.as_view(), name='streams'),
]
