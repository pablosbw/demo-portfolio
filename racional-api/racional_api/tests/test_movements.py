import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from racional_api.models import (
    User,
    Stock,
    StockPrice,
    Portfolio,
    PortfolioComponent,
    Transaction,
    Order,
)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create(
        first_name="Mov",
        last_name="User",
        phone_number="000",
        email="mov@example.com",
        money=Decimal("1000.00"),
        is_deleted=False,
    )

@pytest.fixture
def stocks_and_prices():
    s1 = Stock.objects.create(symbol="MOV1", name="Mov One")
    s2 = Stock.objects.create(symbol="MOV2", name="Mov Two")
    today_midnight = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    StockPrice.objects.create(stock=s1, value=Decimal("10.00"), date=today_midnight - timedelta(days=1))
    StockPrice.objects.create(stock=s1, value=Decimal("12.00"), date=today_midnight)
    StockPrice.objects.create(stock=s2, value=Decimal("20.00"), date=today_midnight)
    return s1, s2

@pytest.mark.django_db
def test_user_last_movements_includes_transactions_and_orders(api_client, user, stocks_and_prices):
    s1, s2 = stocks_and_prices

    # Create transactions
    t_dep = Transaction.objects.create(
        user=user,
        transaction_type=Transaction.DEPOSIT,
        amount=Decimal("500.00"),
        execution_date=date.today(),
    )
    t_wd = Transaction.objects.create(
        user=user,
        transaction_type=Transaction.WITHDRAW,
        amount=Decimal("100.00"),
        execution_date=date.today(),
    )

    o1 = Order.objects.create(
        user=user,
        asset_type=Order.ASSET_STOCK,
        side=Order.BUY,
        stock=s1,
        quantity=Decimal("5"),
        execution_price=Decimal("12.00"),
        execution_date=date.today(),
    )

    # Create a portfolio and an associated portfolio BUY order
    p = Portfolio.objects.create(user=user, name="P1", description="", risk=1)
    PortfolioComponent.objects.create(portfolio=p, stock=s2, weight=Decimal("1.0"))
    o2 = Order.objects.create(
        user=user,
        asset_type=Order.ASSET_PORTFOLIO,
        side=Order.BUY,
        portfolio=p,
        quantity=Decimal("1"),
        execution_price=Decimal("100.00"),
        execution_date=date.today(),
    )

    # Request movements (use direct path)
    url = f"/api/users/{user.pk}/movements/?limit=10"
    resp = api_client.get(url, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.data, list)
    assert len(resp.data) >= 4
    types = [m["type"] for m in resp.data]
    assert "TRANSACTION" in types
    assert "ORDER" in types

    tx_amounts = [Decimal(str(m["amount"])) for m in resp.data if m["type"] == "TRANSACTION"]
    assert Decimal("500.00") in tx_amounts or Decimal("100.00") in tx_amounts

    order_movements = [m for m in resp.data if m["type"] == "ORDER"]
    assert any(m.get("symbol") == s1.symbol and m.get("subtype") == Order.BUY for m in order_movements)
    assert any(m.get("portfolio_id") == p.pk and m.get("subtype") == Order.BUY for m in order_movements)

@pytest.mark.django_db
def test_user_last_movements_limit_and_ordering(api_client, user, stocks_and_prices):
    s1, _ = stocks_and_prices
    Transaction.objects.create(user=user, transaction_type=Transaction.DEPOSIT, amount=Decimal("100.00"), execution_date=date.today())
    o = Order.objects.create(user=user, asset_type=Order.ASSET_STOCK, side=Order.BUY, stock=s1, quantity=Decimal("1"), execution_price=Decimal("10.00"), execution_date=date.today())
    t_last = Transaction.objects.create(user=user, transaction_type=Transaction.WITHDRAW, amount=Decimal("50.00"), execution_date=date.today())

    url = f"/api/users/{user.pk}/movements/?limit=2"
    resp = api_client.get(url, format="json")
    assert resp.status_code == status.HTTP_200_OK
    # limit applied
    assert len(resp.data) == 2
    # latest movement should be the last created (withdraw)
    assert resp.data[0]["type"] == "TRANSACTION"
    assert Decimal(str(resp.data[0]["amount"])) == Decimal("50.00")
