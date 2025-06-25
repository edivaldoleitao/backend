from django.urls import path

from .views import product_views

# from .views.user_views import create_user, get_categories, get_user
from .views import user_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("create_user/", user_views.create_user, name="create_user"),
    path("categories/", user_views.get_categories, name="get_categories"),
    path("get_user/<int:user_id>/", user_views.get_user_id, name="get_user"),
    path("get_users/", user_views.get_all_users, name="get_users"),
    path("update_user/<int:user_id>/", user_views.update_user, name="update_user"),
    path(
        "update_password/<int:user_id>/",
        user_views.update_password,
        name="update_password",
    ),
    path("delete_user/<int:user_id>/", user_views.delete_user, name="delete_user"),
    path("recover_password/", user_views.recover_password, name="recover_password"),
    path("login/", user_views.EmailLoginView.as_view(), name="email_login"),
    path('users/me/', user_views.CurrentUserView.as_view(), name='current_user'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(
        "confirm_email/<int:user_id>/",
        user_views.confirm_email,
        name="confirm_email",
    ),
]
