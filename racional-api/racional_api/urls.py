from django.urls import path
from .views import WithdrawCreateView, DepositCreateView, UserDetailView, UserListCreateView


user_urls = [
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]

urlpatterns = [
    *user_urls,
]
