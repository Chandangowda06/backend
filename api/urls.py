from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AddToCartAPIView, CartListAPIView, CheckoutAPIView, PlaceOrderAPIView, PostalCodeViewSet, RegisterView, UserOrdersAPIView, UserViewSet, CategoryViewSet, ProductViewSet,
    CartViewSet, AddressViewSet, OrderViewSet, DeliveryViewSet, PaymentViewSet, ValidatePostalCodeView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'postal-codes', PostalCodeViewSet, basename='postalcode')

urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='register'),
    path('validate-postal/', ValidatePostalCodeView.as_view(), name='validate-postal'),
    path('cart/add/', AddToCartAPIView.as_view(), name='add-to-cart'),
    path('cart/checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('cart/', CartListAPIView.as_view(), name='view-cart'),
    path('order/place/', PlaceOrderAPIView.as_view(), name='place-order'),
    path('orders/', UserOrdersAPIView.as_view(), name='user-orders'),
    path('', include(router.urls)),
]

