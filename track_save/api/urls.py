from django.urls import path
# from .views.user_views import create_user, get_categories, get_user
from .views import user_views, product_views

urlpatterns = [
    path('create_user/', user_views.create_user, name='create_user'),
    path('categories/', user_views.get_categories, name='get_categories'),
    path('get_user/<int:user_id>/', user_views.get_user_id, name='get_user'),
    path('get_users/', user_views.get_all_users, name='get_users'),
    path('update_user/<int:user_id>/', user_views.update_user, name='update_user'),
    path('update_password/<int:user_id>/', user_views.update_password, name='update_password'),
    path('delete_user/<int:user_id>/', user_views.delete_user, name='delete_user'),
    path('recover_password/', user_views.recover_password, name='recover_password'),
]
