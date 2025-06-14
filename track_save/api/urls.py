from django.urls import path
# from .views.user_views import create_user, get_categories, get_user
from .views import user_views, product_views

urlpatterns = [
    path('create_user/', user_views.create_user),
    path('categories/', user_views.get_categories),
    path('get_user/<int:user_id>/', user_views.get_user_id),
    path('get_users/', user_views.get_all_users),
    path('update_user/', user_views.update_user),
    path('change_password/', user_views.update_password),
    path('delete_user/', user_views.delete_user),
]
