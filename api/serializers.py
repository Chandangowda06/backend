from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, PostalCode, Product, Cart, Address, Order, OrderItem, Delivery, Payment, ProductImage, ProductVariant

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'user_role']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_role = serializers.CharField(required=False, write_only=True)  # Optional for admin only

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password', 'user_role']

    def create(self, validated_data):
        user_role = validated_data.pop('user_role', None)  # Remove 'user_role' if not provided

        if self.context['request'].user.is_staff and user_role:  # Only admin can set 'user_role'
            user = User.objects.create_user(**validated_data, user_role=user_role)
        else:
            user = User.objects.create_user(**validated_data)  # Normal users don't get 'user_role'
        
        return user



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']




class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class PostalCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostalCode
        fields = ['code']


class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'brand']


class ProductVariantSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'unit', 'price', 'stock', 'discount_percent', 'discounted_price', 'product']

    def get_discounted_price(self, obj):
        return obj.discounted_price()

    def get_product(self, obj):
        from .serializers import ProductMiniSerializer  # avoid circular imports
        return ProductMiniSerializer(obj.product).data


  

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'brand', 'tags', 'is_active', 'created_at',
            'category', 'images', 'variants'
        ]




class CartSerializer(serializers.ModelSerializer):
    product = ProductVariantSerializer()
    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductVariantSerializer()
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price_at_order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'items', 'created_at']

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'
