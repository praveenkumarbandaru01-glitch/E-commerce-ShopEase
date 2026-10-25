from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from product.models import Product
from .models import CartItem, WishlistItem


@login_required
def cart(request):
    items = CartItem.objects.filter(user=request.user).select_related(
        "product",
        "product__category",
    )
    subtotal = sum((item.line_total for item in items), Decimal("0.00"))
    return render(
        request,
        "carts/cart.html",
        {"cart_items": items, "subtotal": subtotal},
    )


@login_required
@require_POST
def add_to_cart(request, product_id):
    with transaction.atomic():
        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=product_id,
        )
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": 1},
        )
        if not created:
            if item.quantity >= product.stock:
                messages.error(request, "There is not enough stock for another item.")
                return redirect("product_detail", pk=product.pk)
            item.quantity += 1
            item.save(update_fields=["quantity"])

        if product.stock == 0:
            item.delete()
            messages.error(request, "This product is out of stock.")
            return redirect("product_detail", pk=product.pk)

    messages.success(request, f"{product.name} was added to your cart.")
    return redirect("cart")


@login_required
@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        pk=item_id,
        user=request.user,
    )
    try:
        quantity = int(request.POST.get("quantity", ""))
    except (TypeError, ValueError):
        messages.error(request, "Enter a valid quantity.")
        return redirect("cart")

    if quantity < 1 or quantity > item.product.stock:
        messages.error(
            request,
            f"Choose a quantity between 1 and {item.product.stock}.",
        )
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        messages.success(request, "Cart quantity updated.")
    return redirect("cart")


@login_required
@require_POST
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect("cart")


@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related(
        "product",
        "product__category",
    )
    return render(request, "carts/wishlist.html", {"wishlist_items": items})


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    _, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product,
    )
    if created:
        messages.success(request, f"{product.name} was added to your wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    return redirect("wishlist")


@login_required
@require_POST
def remove_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item removed from your wishlist.")
    return redirect("wishlist")
