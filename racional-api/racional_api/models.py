from django.db import models


class SoftDeleteModel(models.Model):
    # Ensure that no data is lost when erasing records
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of removing the row."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])

        return (1, {self.__class__.__name__: 1})

    class Meta:
        abstract = True


class User(SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    money = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Transaction(SoftDeleteModel):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSACTION_TYPES = [
        (DEPOSIT, "Deposit"),
        (WITHDRAW, "Withdraw"),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="transaction",
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    
    execution_date = models.DateField(default=None)
    class Meta(SoftDeleteModel.Meta):
        ordering = ["-created_at"]


class Stock(SoftDeleteModel):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=200)

class StockPrice(SoftDeleteModel):
    value = models.FloatField(default=1.0)
    date = models.DateTimeField()
    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="prices",
    )

class Portfolio(SoftDeleteModel):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="portfolios",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    TRANSACTION_TYPES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
    ]
    risk = models.CharField(max_length=20, choices=TRANSACTION_TYPES)


class PortfolioComponent(SoftDeleteModel):
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.PROTECT,
        related_name="components",
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="portfolio_components",
    )
    weight = models.DecimalField(max_digits=6, decimal_places=4)

    class Meta(SoftDeleteModel.Meta):
        unique_together = ("portfolio", "stock")


class Order(SoftDeleteModel):
    ASSET_STOCK = "STOCK"
    ASSET_PORTFOLIO = "PORTFOLIO"
    ASSET_TYPES = [
        (ASSET_STOCK, "Stock"),
        (ASSET_PORTFOLIO, "Portfolio"),
    ]

    BUY = "BUY"
    SELL = "SELL"
    SIDE_TYPES = [
        (BUY, "Buy"),
        (SELL, "Sell"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, blank=True)
    side = models.CharField(max_length=4, choices=SIDE_TYPES, blank=True)

    stock = models.ForeignKey(
        Stock,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    quantity = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )

    execution_date = models.DateField(null=True, blank=True)

    execution_price = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )

    class Meta(SoftDeleteModel.Meta):
        ordering = ["-created_at"]