from django.urls import path
from .views import WithdrawCreateView, DepositCreateView, UserDetailView, UserListCreateView


user_urls = [
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]

transaction_urls = [
    path("transactions/deposit/", DepositCreateView.as_view(), name="deposit-create"),
    path("transactions/withdraw/", WithdrawCreateView.as_view(), name="withdrawal-create"),
]

urlpatterns = [
    *user_urls,
    *transaction_urls, 
]
