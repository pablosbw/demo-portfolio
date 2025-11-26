import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from racional_api.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    """
    A base user for retrieve/update/delete tests.
    """
    return User.objects.create(
        first_name =  "string",
        last_name= "string",
        phone_number= "123456789",
        email= "test@example.com",
        is_deleted= False
    )


@pytest.fixture
def deleted_user():
    """
    A user already soft-deleted (is_deleted=True)
    to check that queryset filter works.
    """
    return User.objects.create(
        email="deleted@example.com",
        first_name="Deleted",
        last_name="User",
        phone_number= "012346578",
        is_deleted=True,
    )


@pytest.mark.django_db
def test_create_user(api_client):
    url = reverse("user-list")
    
    payload = {
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "123456789",
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.django_db
def test_list_users_excludes_soft_deleted(api_client, user, deleted_user):
    url = reverse("user-list")

    response = api_client.get(url, format="json")

    assert response.status_code == status.HTTP_200_OK

    emails = {u["email"] for u in response.data}

    assert "test@example.com" in emails
    assert "deleted@example.com" not in emails


@pytest.mark.django_db
def test_retrieve_user(api_client, user):
    url = reverse("user-detail", args=[user.pk])

    response = api_client.get(url, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == user.email


@pytest.mark.django_db
def test_retrieve_soft_deleted_user_returns_404(api_client, deleted_user):
    url = reverse("user-detail", args=[deleted_user.pk])

    response = api_client.get(url, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_patch_user_partial_update(api_client, user):
    url = reverse("user-detail", args=[user.pk])

    payload = {"first_name": "Updated"}
    response = api_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK

    user.refresh_from_db()
    assert user.first_name == "Updated"


@pytest.mark.django_db
def test_put_user_behaves_like_partial_update(api_client, user):
    """
    You overrode put() to call partial_update(), so PUT should not require all fields.
    """
    url = reverse("user-detail", args=[user.pk])

    payload = {"first_name": "PutNameOnly"}
    response = api_client.put(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK

    user.refresh_from_db()
    assert user.first_name == "PutNameOnly"
    # and other fields should still be there, unchanged
    assert user.email == "test@example.com"
    assert user.phone_number == "123456789"


@pytest.mark.django_db
def test_delete_user_soft_delete(api_client, user):
    url = reverse("user-detail", args=[user.pk])

    response = api_client.delete(url, format="json")

    # According to the schema: 204 on delete
    assert response.status_code == status.HTTP_204_NO_CONTENT

    user.refresh_from_db()
    # When deleting, is_deleted=True
    assert user.is_deleted is True


@pytest.mark.django_db
def test_deleted_user_cannot_be_retrieved_after_delete(api_client, user):
    url = reverse("user-detail", args=[user.pk])

    # First delete
    delete_response = api_client.delete(url, format="json")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Try to get again
    get_response = api_client.get(url, format="json")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
