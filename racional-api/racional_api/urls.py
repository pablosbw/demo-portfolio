from django.urls import path
from .views import WithdrawCreateView, DepositCreateView, UserDetailView


user_urls = [
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]

urlpatterns = [
    *user_urls,
]
