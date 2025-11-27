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
        first_name="Alice",
        last_name="Investor",
        phone_number="555",
        email="alice@example.com",
        money=Decimal("10000.00"),
        is_deleted=False,
    )

@pytest.fixture
def other_user():
    return User.objects.create(
        first_name="Bob",
        last_name="Investor",
        phone_number="556",
        email="bob@example.com",
        money=Decimal("500.00"),
        is_deleted=False,
    )

@pytest.fixture
def stocks_and_prices():
    s1 = Stock.objects.create(symbol="AAA", name="AAA Corp")
    s2 = Stock.objects.create(symbol="BBB", name="BBB Inc")
    # timezone-aware midnights
    today_midnight = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_midnight = today_midnight - timedelta(days=1)
    StockPrice.objects.create(stock=s1, value=Decimal("10.00"), date=yesterday_midnight)
    StockPrice.objects.create(stock=s1, value=Decimal("11.00"), date=today_midnight)
    StockPrice.objects.create(stock=s2, value=Decimal("20.00"), date=yesterday_midnight)
    StockPrice.objects.create(stock=s2, value=Decimal("22.00"), date=today_midnight)
    return (s1, s2)

@pytest.mark.django_db
def test_create_portfolio_success(api_client, user, stocks_and_prices):
    url = reverse("portfolio-create")
    payload = {
        "user_id": user.pk,
        "name": "Balanced",
        "description": "Test portfolio",
        "risk": "HIGH",
        "components": [
            {"symbol": "AAA", "weight": "0.5"},
            {"symbol": "BBB", "weight": "0.5"},
        ],
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    assert Portfolio.objects.filter(user=user, name="Balanced").exists()
    p = Portfolio.objects.get(user=user, name="Balanced")
    assert PortfolioComponent.objects.filter(portfolio=p).count() == 2

@pytest.mark.django_db
def test_create_portfolio_nonexistent_user(api_client, stocks_and_prices):
    url = reverse("portfolio-create")
    payload = {
        "user_id": 99999,
        "name": "NoUser",
        "description": "",
        "risk": "LOW",
        "components": [
            {"symbol": "AAA", "weight": "1.0"},
        ],
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_portfolio_duplicate_components(api_client, user, stocks_and_prices):
    url = reverse("portfolio-create")
    payload = {
        "user_id": user.pk,
        "name": "DupComp",
        "description": "",
        "risk": 2,
        "components": [
            {"symbol": "AAA", "weight": "0.5"},
            {"symbol": "AAA", "weight": "0.5"},
        ],
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_portfolio_weights_not_sum_to_one(api_client, user, stocks_and_prices):
    url = reverse("portfolio-create")
    payload = {
        "user_id": user.pk,
        "name": "BadWeights",
        "description": "",
        "risk": 2,
        "components": [
            {"symbol": "AAA", "weight": "0.6"},
            {"symbol": "BBB", "weight": "0.3"},
        ],
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_get_user_portfolios(api_client, user, stocks_and_prices):
    p = Portfolio.objects.create(user=user, name="P1", description="d", risk=1)
    PortfolioComponent.objects.create(portfolio=p, stock=stocks_and_prices[0], weight=Decimal("1.0"))
    url = reverse("portfolio-list", args=[user.pk])
    resp = api_client.get(url, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.data, list)
    assert len(resp.data) >= 1

@pytest.mark.django_db
def test_update_portfolio_metadata_success(api_client, user, stocks_and_prices):
    p = Portfolio.objects.create(user=user, name="ToEdit", description="old", risk=1)
    PortfolioComponent.objects.create(portfolio=p, stock=stocks_and_prices[0], weight=Decimal("1.0"))
    url = reverse("portfolio-metadata-update", args=[p.pk])
    payload = {"name": "Edited", "description": "new", "risk": "HIGH"}
    resp = api_client.patch(url, payload, format="json")
    assert resp.status_code == status.HTTP_200_OK
    p.refresh_from_db()
    assert p.name == "Edited"
    assert p.description == "new"
    assert p.risk == "HIGH"

@pytest.mark.django_db
def test_update_portfolio_nonexistent_returns_404(api_client):
    url = reverse("portfolio-metadata-update", args=[99999])
    resp = api_client.patch(url, {"name": "X"}, format="json")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_user_portfolio_total_values(api_client, user, stocks_and_prices):
    s1, s2 = stocks_and_prices

    # create a prior BUY order (older than latest price) - user bought 10 * 10.00
    Order.objects.create(
        user=user,
        stock=s1,
        side=Order.BUY,
        quantity=Decimal("10"),
        execution_price=Decimal("10.00"),
        execution_date=date.today() - timedelta(days=2),
        asset_type=Order.ASSET_STOCK,
    )

    # deposit 1000.00
    Transaction.objects.create(
        user=user,
        transaction_type=Transaction.DEPOSIT,
        amount=Decimal("1000.00"),
        execution_date=date.today(),
    )

    url = reverse("user-portfolio-total", args=[user.pk])
    resp = api_client.get(url, format="json")
    assert resp.status_code == status.HTTP_200_OK

    # Cash should be deposit - cost_of_buy = 1000 - (10 * 10) = 900.00
    assert Decimal(resp.data["cash"]) == Decimal("900.00")

    # stocks_total uses latest price for s1 (fixture set to 11.00), value = 10 * 11 = 110.00
    assert Decimal(resp.data["stocks_total"]) == Decimal("110.00")

    # portfolio_total = cash + stocks_total = 900 + 110 = 1010.00
    assert Decimal(resp.data["portfolio_total"]) == Decimal("1010.00")

    # positions should include the AAA position with quantity 10
    positions = resp.data["positions"]
    assert any(p["symbol"] == s1.symbol and Decimal(p["quantity"]) == Decimal("10") for p in positions)
