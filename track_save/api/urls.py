from django.urls import path

from .views import alert_views
from .views import favorite_views
from .views import price_views
from .views import product_views
from .views import user_views

urlpatterns = [
    path("users/create/", user_views.create_user, name="create_user"),
    path("categories/", user_views.get_categories, name="get_categories"),
    path("users/<int:user_id>/", user_views.get_user_id, name="get_user"),
    path("users/", user_views.get_all_users, name="get_users"),
    path("users/update/<int:user_id>/", user_views.update_user, name="update_user"),
    path(
        "users/update_password/<int:user_id>/",
        user_views.update_password,
        name="update_password",
    ),
    path("users/delete/<int:user_id>/", user_views.delete_user, name="delete_user"),
    path(
        "users/recover_password/", user_views.recover_password, name="recover_password"
    ),
    path("users/login/", user_views.EmailLoginView.as_view(), name="email_login"),
    path("users/me/", user_views.CurrentUserView.as_view(), name="current_user"),
    path(
        "users/confirm_email/<int:user_id>/",
        user_views.confirm_email,
        name="confirm_email",
    ),
    path(
        "users/specification/create/",
        user_views.create_user_specification,
        name="create_user_spec",
    ),
    path(
        "users/specification/<int:user_id>/",
        user_views.get_user_specification_id,
        name="get_user_spec",
    ),
    path(
        "users/specification/", user_views.get_all_specifications, name="get_all_spec"
    ),
    path(
        "users/specification/update/<int:user_id>/",
        user_views.update_user_specification,
        name="update_user_spec",
    ),
    path(
        "users/specification/delete/<int:user_id>/",
        user_views.delete_user_specification,
        name="delete_user_spec",
    ),
    path("stores/create/", product_views.create_store, name="create_store"),
    path("stores/get/", product_views.get_stores, name="get_store"),
    path("stores/update/<str:name>", product_views.update_store, name="update_store"),
    path("stores/delete/<str:name>", product_views.delete_store, name="delete_store"),
    path("products/create/", product_views.create_product, name="create_product"),
    path("products/search/", product_views.search_products, name="search_products"),
    path(
        "products/<int:product_id>/",
        product_views.get_product_id,
        name="get_product",
    ),
    path("products/", product_views.get_products, name="get_products"),
    path(
        "products/best_rating/",
        product_views.list_product_stores_by_best_rating,
        name="list_product_stores_by_best_rating",
    ),
    path(
        "products/name/<str:product_name>/",
        product_views.get_product_name,
        name="get_product",
    ),
    path(
        "products/category/<str:product_category>/",
        product_views.get_product_category,
        name="get_product",
    ),
    path(
        "products/update/<int:product_id>/",
        product_views.update_product,
        name="update_product",
    ),
    path(
        "products/delete/<int:product_id>/",
        product_views.delete_product,
        name="delete_product",
    ),
    path(
        "product_stores/", product_views.list_product_stores, name="list_product_stores"
    ),
    path(
        "product_stores/create/",
        product_views.create_product_store,
        name="create_product_store",
    ),
    path(
        "product_stores/<int:product_store_id>/",
        product_views.get_product_store_by_id,
        name="get_product_store",
    ),
    path(
        "product_stores/update/<int:product_store_id>/",
        product_views.update_product_store,
        name="update_product_store",
    ),
    path(
        "product_stores/delete/<int:product_store_id>/",
        product_views.delete_product_store,
        name="delete_product_store",
    ),
    path(
        "product_stores/details/<int:ps_id>/",
        product_views.get_product_details,
        name="get_product_details",
    ),
    path("prices/", price_views.list_prices, name="list_prices"),
    path("prices/create/", price_views.create_price_view, name="create_price"),
    path("prices/<int:price_id>/", price_views.get_price, name="get_price"),
    path(
        "prices/update/<int:price_id>/",
        price_views.update_price_view,
        name="update_price",
    ),
    path(
        "prices/delete/<int:price_id>/",
        price_views.delete_price_view,
        name="delete_price",
    ),
    path("favorites/", favorite_views.list_favorites_view, name="list_favorites"),
    path(
        "favorites/create/", favorite_views.create_favorite_view, name="create_favorite"
    ),
    path(
        "favorites/<int:fav_id>/", favorite_views.get_favorite_view, name="get_favorite"
    ),
    path(
        "favorites/user/",
        favorite_views.get_favorite_view_by_user,
        name="get_favorite_by_user",
    ),
    path(
        "favorites/update/<int:fav_id>/",
        favorite_views.update_favorite_view,
        name="update_favorite",
    ),
    path(
        "favorites/delete/<int:fav_id>/",
        favorite_views.delete_favorite_view,
        name="delete_favorite",
    ),
    path("alerts/", alert_views.list_alerts_view, name="list_alerts"),
    path("alerts/create/", alert_views.create_alert_view, name="create_alert"),
    path(
        "alerts/user/",
        alert_views.get_alert_view_by_user,
        name="get_alert_view_by_user",
    ),
    path("alerts/<int:alert_id>/", alert_views.get_alert_view, name="get_alert"),
    path(
        "alerts/update/<int:alert_id>/",
        alert_views.update_alert_view,
        name="update_alert",
    ),
    path(
        "alerts/delete/<int:alert_id>/",
        alert_views.delete_alert_view,
        name="delete_alert",
    ),
    path(
        "save_terabyte/",
        product_views.get_terabyte,
        name="terabyte_save",
    ),
    path("search/", product_views.search_view, name="generic_search"),
]
