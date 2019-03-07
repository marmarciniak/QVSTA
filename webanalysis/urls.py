from django.urls import path
from .views import *

urlpatterns = [
    path('pagedata/', PageDataView.as_view()),
]