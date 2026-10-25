from django.contrib import admin
from .models import CartItem, WishlistItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "created_at")
    list_select_related = ("user", "product")
    search_fields = ("user__username", "product__name")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_select_related = ("user", "product")
    search_fields = ("user__username", "product__name")
