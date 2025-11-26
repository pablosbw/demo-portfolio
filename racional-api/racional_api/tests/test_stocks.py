import pytest
from decimal import Decimal
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from racional_api.models import User, Stock, StockPrice, Order


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create(
        first_name="Buyer",
        last_name="One",
        phone_number="111222333",
        email="buyer1@example.com",
        money=Decimal("10000.00"),
        is_deleted=False,
    )


@pytest.fixture
def poor_user():
    return User.objects.create(
        first_name="Poor",
        last_name="User",
        phone_number="000",
        email="poor@example.com",
        money=Decimal("10.00"),
        is_deleted=False,
    )


@pytest.fixture
def deleted_user():
    return User.objects.create(
        first_name="Deleted",
        last_name="User",
        phone_number="000",
        email="deleted@example.com",
        money=Decimal("1000.00"),
        is_deleted=True,
    )


@pytest.fixture
def stock_and_prices():
    s = Stock.objects.create(symbol="TST", name="Test Corp")
    # create timezone-aware midnight datetimes to avoid naive-datetime warnings
    today_midnight = timezone.localtime(timezone.now()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_midnight = today_midnight - timedelta(days=1)
    StockPrice.objects.create(stock=s, value=Decimal("50.0"), date=yesterday_midnight)
    StockPrice.objects.create(stock=s, value=Decimal("55.0"), date=today_midnight)
    return s


@pytest.mark.django_db
def test_buy_stock_success(api_client, user, stock_and_prices):
    url = reverse("stock-order-create") 
    payload = {
        "user_id": user.pk,
        "stock_id": stock_and_prices.pk,
        "side": "BUY",
        "quantity": "10",
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    user.refresh_from_db()
    # price used should be today's price = 55.0
    assert float(user.money) == float(Decimal("10000.00") - Decimal("55.0") * Decimal("10"))
    assert Order.objects.filter(user=user, stock=stock_and_prices, side=Order.BUY).exists()
    order = Order.objects.filter(user=user, stock=stock_and_prices, side=Order.BUY).first()
    assert float(order.execution_price) == float(Decimal("55.0"))


@pytest.mark.django_db
def test_buy_nonexistent_stock(api_client, user):
    url = reverse("stock-order-create") 
    payload = {
        "user_id": user.pk,
        "stock_id": 99999,
        "side": "BUY",
        "quantity": "1",
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Order.objects.filter(user=user).exists()
    user.refresh_from_db()
    assert float(user.money) == float(Decimal("10000.00"))


@pytest.mark.django_db
def test_buy_with_deleted_user_fails(api_client, deleted_user, stock_and_prices):
    url = reverse("stock-order-create") 
    payload = {
        "user_id": deleted_user.pk,
        "stock_id": stock_and_prices.pk,
        "side": "BUY",
        "quantity": "1",
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("detail") in ("User not found or deleted.", None)
    assert not Order.objects.filter(user=deleted_user).exists()


@pytest.mark.django_db
def test_buy_insufficient_funds(api_client, poor_user, stock_and_prices):
    url = reverse("stock-order-create") 
    payload = {
        "user_id": poor_user.pk,
        "stock_id": stock_and_prices.pk,
        "side": "BUY",
        "quantity": "1",
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    poor_user.refresh_from_db()
    assert float(poor_user.money) == float(Decimal("10.00"))
    assert not Order.objects.filter(user=poor_user).exists()


@pytest.mark.django_db
def test_sell_without_holdings_fails(api_client, user, stock_and_prices):
    url = reverse("stock-order-create") 
    payload = {
        "user_id": user.pk,
        "stock_id": stock_and_prices.pk,
        "side": "SELL",
        "quantity": "5",
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    # money unchanged and no sell order created
    assert float(user.money) == float(Decimal("10000.00"))
    assert not Order.objects.filter(user=user, stock=stock_and_prices, side=Order.SELL).exists()


@pytest.mark.django_db
def test_sell_after_buy_succeeds(api_client, user, stock_and_prices):
    # create a prior buy earlier than execution_date
    buy_date = date.today() - timedelta(days=2)
    buy_price = StockPrice.objects.filter(stock=stock_and_prices).order_by('date').first().value
    Order.objects.create(
        user=user,
        stock=stock_and_prices,
        side=Order.BUY,
        quantity=Decimal("10"),
        execution_date=buy_date,
        execution_price=buy_price,
        asset_type=Order.ASSET_STOCK,
    )

    url = reverse("stock-order-create") 
    payload = {
        "user_id": user.pk,
        "stock_id": stock_and_prices.pk,
        "side": "SELL",
        "quantity": "4",
        "execution_date": str(date.today()),
    }

    prev_money = Decimal(user.money)
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    user.refresh_from_db()
    # today price = 55.0 (from fixture), proceed to compute delta
    price_today = Decimal("55.0")
    assert float(user.money) == float(prev_money + price_today * Decimal("4"))
    assert Order.objects.filter(user=user, stock=stock_and_prices, side=Order.SELL).exists()