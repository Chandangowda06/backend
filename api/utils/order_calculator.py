from decimal import Decimal, ROUND_HALF_UP

def round_rupees(value):
    return value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

def calculate_order_summary(cart_items, coupon_code=None):
    subtotal = sum(
        Decimal(item.product.discounted_price()) * item.quantity
        for item in cart_items
    )

    subtotal = round_rupees(subtotal)

    # Tax (5%) - use Decimal
    tax_amount = round_rupees(subtotal * Decimal('0.05'))

    # Shipping fee
    shipping_fee = Decimal('0.00') if subtotal >= Decimal('1000.00') else Decimal('50.00')

    # Discount logic
    discount = Decimal('0.00')
    coupon = None
    if coupon_code:
        try:
            from api.models import Coupon
            coupon = Coupon.objects.get(code=coupon_code, active=True)
            if subtotal >= coupon.minimum_amount:
                discount = coupon.discount_amount
            else:
                raise ValueError('Minimum amount not reached for coupon')
        except Coupon.DoesNotExist:
            raise ValueError('Invalid coupon code')

    total_amount = round_rupees(subtotal + tax_amount + shipping_fee - discount)

    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'total_amount': total_amount,
    }
