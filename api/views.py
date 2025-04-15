from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response

from api.utils.order_calculator import calculate_order_summary

from .permissions import IsAdminOrReadOnly
from .models import Category, OrderItem, PostalCode, Product, Cart, Address, Order, Delivery, Payment, ProductVariant
from .serializers import (
    CategorySerializer, PostalCodeSerializer, UserSerializer, RegisterSerializer, ProductSerializer, 
    CartSerializer, AddressSerializer, OrderSerializer, 
    DeliverySerializer, PaymentSerializer
)
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name']



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'category__name']
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'created_at']



class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)



class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)



class DeliveryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Delivery.objects.all()
        return Delivery.objects.filter(order__user=self.request.user)



class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)



class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user_id": user.id, "username": user.username})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

class PostalCodeViewSet(viewsets.ModelViewSet):
    queryset = PostalCode.objects.all()
    serializer_class = PostalCodeSerializer
    permission_classes = [permissions.IsAdminUser]


class ValidatePostalCodeView(APIView):
    def post(self, request):
        user_postal_code = request.data.get('postal_code')
        print(user_postal_code)
        if not user_postal_code:
            return Response({"error": "Postal code is required"}, status=status.HTTP_400_BAD_REQUEST)

        if PostalCode.objects.filter(code=user_postal_code).exists():
            return Response({"message": "Service available in your area"}, status=status.HTTP_200_OK)
        
        return Response({"message": "Service not available in your area"}, status=status.HTTP_404_NOT_FOUND)


class AddToCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(ProductVariant, id=product_id)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({'message': 'Item added to cart successfully'}, status=200)


class CartListAPIView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)




class UserOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
class DeliveryStatusUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        delivery = get_object_or_404(Delivery, id=pk, delivery_person=request.user)
        new_status = request.data.get('delivery_status')

        if new_status not in dict(Delivery.DELIVERY_STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=400)

        delivery.delivery_status = new_status
        if new_status == 'delivered':
            delivery.delivered_at = timezone.now()
            delivery.save()
            # Also update payment
            delivery.order.payment.payment_status = 'paid'
            delivery.order.payment.save()
        else:
            delivery.save()

        return Response({'message': 'Delivery status updated'}, status=200)
    


class CheckoutAPIView(APIView):
    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=400)

        
        coupon_code = request.data.get('coupon_code')

        address = get_object_or_404(Address, user=request.user)

        try:
            summary = calculate_order_summary(cart_items, coupon_code)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        return Response({
            **summary,
            'coupon_code': coupon_code,
            'address': AddressSerializer(address).data,
        })
    

class PlaceOrderAPIView(APIView):
    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=400)

        # address_id = request.data.get('address_id')
        coupon_code = request.data.get('coupon_code')
        note = request.data.get('note', '')

        address = get_object_or_404(Address, user=request.user)

        try:
            summary = calculate_order_summary(cart_items, coupon_code)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        order = Order.objects.create(
            user=request.user,
            note=note,
            coupon_code=coupon_code,
            discount_amount=summary['discount'],
            tax_amount=summary['tax_amount'],
            shipping_fee=summary['shipping_fee'],
            total_amount=summary['total_amount']
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_order=item.product.discounted_price()
            )

        Payment.objects.create(
            order=order,
            payment_method='cod',
            payment_status='pending',
            amount_paid=summary['total_amount']
        )

        delivery_persons = User.objects.filter(user_role='Delivery_Person')
        if delivery_persons.exists():
            Delivery.objects.create(order=order, delivery_person=delivery_persons.first())

        cart_items.delete()

        return Response({'message': 'Order placed successfully'}, status=201)
