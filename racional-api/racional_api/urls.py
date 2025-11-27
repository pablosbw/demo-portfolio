from django.urls import path
from .views import PortfolioCreateView, PortfolioInvestView, PortfolioListView, PortfolioMetadataUpdateView, StockOrderCreateView, TransactionListView, UserPortfolioTotalView, WithdrawCreateView, DepositCreateView, UserDetailView, UserListCreateView


user_urls = [
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path(
        "users/<int:user_id>/portfolio/total/",
        UserPortfolioTotalView.as_view(),
        name="user-portfolio-total",
    ),
]

transaction_urls = [
    path("transactions/deposit/", DepositCreateView.as_view(), name="deposit-create"),
    path("transactions/withdraw/", WithdrawCreateView.as_view(), name="withdraw-create"),
    path("users/<int:user_id>/transactions/", TransactionListView.as_view(), name="transaction-list"),
]

orders_urls = [
    path("orders/stocks/", StockOrderCreateView.as_view(), name="stock-order-create"),
]

portfolios_urls = [
    path("portfolios/", PortfolioCreateView.as_view(), name="portfolio-create"),
    path("portfolios/<int:pk>/", PortfolioMetadataUpdateView.as_view(), name="portfolio-metadata-update"),
    path("users/<int:user_id>/portfolios/", PortfolioListView.as_view(), name="portfolio-list"),
    path( "portfolios/invest/", PortfolioInvestView.as_view(), name="portfolio-invest",
    ),

]

urlpatterns = [
    *user_urls,
    *transaction_urls, 
    *orders_urls,
    *portfolios_urls
]
