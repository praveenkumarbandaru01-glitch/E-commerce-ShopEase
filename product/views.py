from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from .models import Category, Product


def get_storefront_context(request):
    categories = Category.objects.all()
    products = Product.objects.select_related("category")

    selected_category = request.GET.get("category", "").strip()
    search_query = request.GET.get("q", "").strip()

    if selected_category:
        products = products.filter(category__name=selected_category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    return {
        "categories": categories,
        "products": products,
        "selected_category": selected_category,
        "search_query": search_query,
        "total_products": Product.objects.count(),
        "available_products": Product.objects.filter(stock__gt=0).count(),
        "low_stock": Product.objects.filter(stock__gt=0, stock__lte=5).count(),
    }


def Dashboard(request):
    return render(
        request,
        "product/dashboard.html",
        get_storefront_context(request),
    )


def ProductDetail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        pk=pk,
    )
    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
    )
    is_in_wishlist = (
        request.user.is_authenticated
        and product.wishlist_items.filter(user=request.user).exists()
    )
    return render(
        request,
        "product/detail.html",
        {
            "product": product,
            "related_products": related_products,
            "is_in_wishlist": is_in_wishlist,
        },
    )
