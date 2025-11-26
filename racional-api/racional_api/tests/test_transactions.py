import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from racional_api.models import Transaction, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    """Create a test user with initial money."""
    return User.objects.create(
        first_name="John",
        last_name="Doe",
        phone_number="123456789",
        email="user@example.com",
        money=1000.00,
        is_deleted=False
    )


@pytest.fixture
def user_no_money():
    """Create a test user with no money."""
    return User.objects.create(
        first_name="Jane",
        last_name="Smith",
        phone_number="987654321",
        email="poor@example.com",
        money=0.00,
        is_deleted=False
    )


@pytest.mark.django_db
def test_create_deposit(api_client, user):
    """Test creating a deposit transaction."""
    url = reverse("deposit-create")

    payload = {
        "user_id": user.pk,
        "amount": 500.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["transaction_type"] == Transaction.DEPOSIT
    assert float(response.data["amount"]) == 500.00
    assert Transaction.objects.filter(user=user, transaction_type=Transaction.DEPOSIT).exists()


@pytest.mark.django_db
def test_create_withdrawal(api_client, user):
    """Test creating a withdrawal transaction."""
    url = reverse("withdraw-create")
    
    payload = {
        "user_id": user.pk,
        "amount": 200.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["transaction_type"] == Transaction.WITHDRAW
    assert float(response.data["amount"]) == 200.00
    assert Transaction.objects.filter(user=user, transaction_type=Transaction.WITHDRAW).exists()


@pytest.mark.django_db
def test_deposit_with_invalid_user(api_client):
    """Test deposit with non-existent user."""
    url = reverse("deposit-create")
    
    payload = {
        "user_id": 9999,
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    print(response.data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_withdrawal_with_invalid_user(api_client):
    """Test withdrawal with non-existent user."""
    url = reverse("withdraw-create")
    
    payload = {
        "user_id": 9999,
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_deposit_missing_amount(api_client, user):
    """Test deposit without amount field."""
    url = reverse("deposit-create")
    
    payload = {
        "user_id": user.pk,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_withdrawal_missing_amount(api_client, user):
    """Test withdrawal without amount field."""
    url = reverse("withdraw-create")
    
    payload = {
        "user_id": user.pk,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_deposit_missing_user_id(api_client):
    """Test deposit without user_id field."""
    url = reverse("deposit-create")
    
    payload = {
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_withdrawal_missing_user_id(api_client):
    """Test withdrawal without user_id field."""
    url = reverse("withdraw-create")
    
    payload = {
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_list_user_transactions(api_client, user):
    """Test listing all transactions for a user."""
    # Create some transactions
    Transaction.objects.create(
        user=user,
        transaction_type=Transaction.DEPOSIT,
        amount=500.00,
        execution_date=date.today()
    )
    Transaction.objects.create(
        user=user,
        transaction_type=Transaction.WITHDRAW,
        amount=100.00,
        execution_date=date.today()
    )

    url = reverse("transaction-list", args=[user.pk])
    response = api_client.get(url, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 2


@pytest.mark.django_db
def test_transaction_ordering(api_client, user):
    """Test that transactions are ordered by creation date (newest first)."""
    t1 = Transaction.objects.create(
        user=user,
        transaction_type=Transaction.DEPOSIT,
        amount=100.00,
        execution_date=date.today()
    )
    t2 = Transaction.objects.create(
        user=user,
        transaction_type=Transaction.WITHDRAW,
        amount=50.00,
        execution_date=date.today()
    )

    url = reverse("transaction-list", args=[user.pk])
    response = api_client.get(url, format="json")

    # Newest first (t2 should come before t1)
    assert response.data[0]["id"] == t2.pk
    assert response.data[1]["id"] == t1.pk


@pytest.mark.django_db
def test_deposit_with_decimal_amount(api_client, user):
    """Test deposit with decimal precision."""
    url = reverse("deposit-create")
    
    payload = {
        "user_id": user.pk,
        "amount": 123.45,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert float(response.data["amount"]) == 123.45


@pytest.mark.django_db
def test_withdrawal_with_decimal_amount(api_client, user):
    """Test withdrawal with decimal precision."""
    url = reverse("withdraw-create")
    
    payload = {
        "user_id": user.pk,
        "amount": 75.99,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert float(response.data["amount"]) == 75.99


@pytest.mark.django_db
def test_soft_deleted_user_cannot_transact(api_client, user):
    """Test that soft-deleted users cannot create transactions."""
    user.delete()  # Soft delete
    
    url = reverse("deposit-create")
    payload = {
        "user_id": user.pk,
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    # Soft-deleted users are filtered out, so serializer validation fails
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    url = reverse("withdraw-create")
    payload = {
        "user_id": user.pk,
        "amount": 100.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")

    # Soft-deleted users are filtered out, so serializer validation fails
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_withdraw_more_than_balance(api_client, user):
    """Attempt to withdraw more than the user's balance should fail."""
    url = reverse("withdraw-create")
    # user has 1000.00 from fixture
    payload = {
        "user_id": user.pk,
        "amount": 2000.00,
        "execution_date": str(date.today()),
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert float(user.money) == 1000.00

