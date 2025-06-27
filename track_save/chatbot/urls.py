from django.urls import path
from .views import agent_use, agent_upgrade

urlpatterns = [
    path("use/", agent_use, name="chatbot_use"),
    path("upgrade/", agent_upgrade, name="agent_upgrade"),
]
