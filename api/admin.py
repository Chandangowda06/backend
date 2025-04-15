from django.contrib import admin
from .models import *


admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Delivery)
admin.site.register(Payment)
admin.site.register(PostalCode)
admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(Coupon)