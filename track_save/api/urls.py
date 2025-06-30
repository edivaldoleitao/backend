from django.urls import path

from .views import list_views
from .views import price_views
from .views import product_views
from .views import user_views

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
    path("users/me/", user_views.CurrentUserView.as_view(), name="current_user"),
    path(
        "confirm_email/<int:user_id>/",
        user_views.confirm_email,
        name="confirm_email",
    ),
    path("create_product/", product_views.create_product, name="create_product"),

    path('products/search/', product_views.search_products, name='search_products'),
    path(
        "get_product/<int:product_id>/",
        product_views.get_product_id,
        name="get_product",
    ),
    path("get_products/", product_views.get_products, name="get_products"),
    path(
        "get_product_name/<str:product_name>/",
        product_views.get_product_name,
        name="get_product",
    ),
    path(
        "get_product_category/<str:product_category>/",
        product_views.get_product_category,
        name="get_product",
    ),
    path(
        "update_product/<int:product_id>/",
        product_views.update_product,
        name="update_product",
    ),
    path(
        "delete_product/<int:product_id>/",
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
    path('favorites/', list_views.list_favorites_view,  name='list_favorites'),
    path('favorites/create/', list_views.create_favorite_view, name='create_favorite'),
    path('favorites/<int:fav_id>/', list_views.get_favorite_view,    name='get_favorite'),
    path('favorites/update/<int:fav_id>/',list_views.update_favorite_view, name='update_favorite'),
    path('favorites/delete/<int:fav_id>/',list_views.delete_favorite_view, name='delete_favorite'),
]
