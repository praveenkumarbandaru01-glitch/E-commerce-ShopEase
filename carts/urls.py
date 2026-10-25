from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart, name="cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("remove/<int:item_id>/", views.remove_cart_item, name="remove_cart_item"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path(
        "wishlist/add/<int:product_id>/",
        views.add_to_wishlist,
        name="add_to_wishlist",
    ),
    path(
        "wishlist/remove/<int:item_id>/",
        views.remove_wishlist_item,
        name="remove_wishlist_item",
    ),
]