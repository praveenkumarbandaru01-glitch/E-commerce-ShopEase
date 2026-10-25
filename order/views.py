from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from carts.models import CartItem
from product.models import Product
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart_items = list(
        CartItem.objects.filter(user=request.user)
        .select_related("product", "product__category")
    )
    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart")

    if request.method == "POST":
        address = request.POST.get("shipping_address", "").strip()
        payment_method = request.POST.get("payment_method", "")
        if not address:
            messages.error(request, "Enter a delivery address to place your order.")
        elif payment_method != Order.PaymentMethod.CASH_ON_DELIVERY:
            messages.error(request, "Please choose cash on delivery.")
        else:
            with transaction.atomic():
                locked_items = list(
                    CartItem.objects.filter(user=request.user)
                    .select_related("product")
                    .order_by("product_id")
                )
                if not locked_items:
                    messages.info(request, "Your cart is empty.")
                    return redirect("cart")

                locked_products = {
                    product.pk: product
                    for product in Product.objects.select_for_update().filter(
                        pk__in=[item.product_id for item in locked_items]
                    )
                }
                for item in locked_items:
                    product = locked_products.get(item.product_id)
                    if product is None or product.stock < item.quantity:
                        available = product.stock if product else 0
                        messages.error(
                            request,
                            f"Only {available} of "
                            f"{item.product.name} are available. "
                            "Update your cart and try again.",
                        )
                        return redirect("cart")

                order = Order.objects.create(
                    user=request.user,
                    shipping_address=address,
                    payment_method=payment_method,
                )
                for item in locked_items:
                    product = locked_products[item.product_id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=item.quantity,
                        unit_price=product.price,
                    )
                    product.stock -= item.quantity
                    product.save(update_fields=["stock"])
                CartItem.objects.filter(user=request.user).delete()

            messages.success(request, f"Order #{order.pk} placed successfully.")
            return redirect("order_detail", order_id=order.pk)

    items = CartItem.objects.filter(user=request.user).select_related(
        "product",
        "product__category",
    )
    total = sum((item.line_total for item in items), Decimal("0.00"))
    return render(
        request,
        "order/checkout.html",
        {
            "cart_items": items,
            "total": total,
            "shipping_address": request.POST.get("shipping_address", ""),
        },
    )


@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
    )
    return render(request, "order/history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=order_id,
        user=request.user,
    )
    progress_statuses = [
        (value, label)
        for value, label in Order.Status.choices
        if value != Order.Status.CANCELLED
    ]
    current_index = next(
        (
            index
            for index, (value, _) in enumerate(progress_statuses)
            if value == order.status
        ),
        -1,
    )
    tracking_steps = [
        {"label": label, "completed": index <= current_index}
        for index, (_, label) in enumerate(progress_statuses)
    ]
    return render(
        request,
        "order/detail.html",
        {
            "order": order,
            "tracking_steps": tracking_steps,
            "is_cancelled": order.status == Order.Status.CANCELLED,
        },
    )


@login_required
@require_POST
def cancel_order(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update().prefetch_related("items"),
            pk=order_id,
            user=request.user,
        )
        if order.status not in (Order.Status.PLACED, Order.Status.CONFIRMED):
            messages.error(
                request,
                "This order can no longer be cancelled online.",
            )
            return redirect("order_detail", order_id=order.pk)

        order_items = list(order.items.all())
        product_ids = [item.product_id for item in order_items if item.product_id]
        products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=product_ids
            )
        }
        for item in order_items:
            product = products.get(item.product_id)
            if product:
                product.stock += item.quantity
                product.save(update_fields=["stock"])

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])

    messages.success(request, f"Order #{order.pk} was cancelled.")
    return redirect("order_detail", order_id=order.pk)
