from django.urls import path
from .views import agent_use

urlpatterns = [
    path("use/", agent_use, name="chatbot_use"),
    # path("chatbot_/", agent_use, name="chatbot_use"),
]
