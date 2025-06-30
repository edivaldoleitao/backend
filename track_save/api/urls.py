from django.urls import path

from .views import product_views, user_views


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
    path(
        "confirm_email/<int:user_id>/",
        user_views.confirm_email,
        name="confirm_email",
    ),
    path("create_product/", product_views.create_product, name="create_product"),
    path("products/search/", product_views.search_products, name="search_products"),
    path("get_product/<int:product_id>/", product_views.get_product_id, name="get_product"),
    path("get_products/", product_views.get_products, name="get_products"),
    path("get_product_name/<str:product_name>/", product_views.get_product_name, name="get_product"),
    path("get_product_category/<str:product_category>/", product_views.get_product_category, name="get_product"),
    path("update_product/<int:product_id>/", product_views.update_product, name="update_product"),
    path("delete_product/<int:product_id>/", product_views.delete_product, name="delete_product"),
    path("stores/create/", product_views.create_store, name="create_store"),
    path("stores/get/", product_views.get_stores, name="get_store"),
    path("stores/update/<str:name>", product_views.update_store, name="update_store"),
    path("stores/delete/<str:name>", product_views.delete_store, name="delete_store"),
]
