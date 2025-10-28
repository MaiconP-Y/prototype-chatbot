from django.urls import path
from chatbot_api.views import webhook

urlpatterns = [
    path('webhook/', webhook),
]