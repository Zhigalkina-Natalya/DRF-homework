import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name: str, description: str = ""):
    """Создаёт продукт в Stripe."""
    return stripe.Product.create(name=name, description=description)


def create_stripe_price(product_id: str, unit_amount: int, currency: str = "rub"):
    """Создаёт цену (в копейках) для продукта."""
    return stripe.Price.create(
        product=product_id,
        unit_amount=unit_amount * 100,  # цена * 100
        currency=currency,
    )


def create_checkout_session(price_id: str, success_url: str, cancel_url: str, metadata: dict = None):
    """Создаёт сессию оплаты и возвращает URL на Stripe Checkout."""
    session = stripe.checkout.Session.create(
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {},
    )
    return session


def retrieve_session(session_id: str):
    """Опционально: получить статус сессии."""
    return stripe.checkout.Session.retrieve(session_id)
