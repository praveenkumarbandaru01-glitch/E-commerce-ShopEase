from django.urls import path
from . import views

urlpatterns = [
    path("dash", views.Dashboard, name="dashboard"),
    path("products/<int:pk>/", views.ProductDetail, name="product_detail"),
]