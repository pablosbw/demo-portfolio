from rest_framework import serializers
from .models import Stock, StockPrice, User, Transaction, Order, Portfolio, PortfolioComponent, Stock
from decimal import ROUND_DOWN, Decimal
from django.db.models import Sum, Q

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "money",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "money"]


class DepositSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    execution_date = serializers.DateField()
    
    class Meta:
        model = Transaction
        fields = [
            "id",
            "user_id",
            "transaction_type",
            "amount",
            "created_at",
            "updated_at",
            "execution_date"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


    def _normalize_transaction_type(self, transaction_type):
        if not transaction_type:
            return None

        o = transaction_type.lower()
        if o == "deposit":
            return Transaction.DEPOSIT
        elif o == "withdraw":
            return Transaction.WITHDRAW

        raise serializers.ValidationError("Invalid transaction type.")

    def create(self, data):
        user_id = data.pop("user_id")
        transaction_type_raw = data.pop("transaction_type", None)
        if transaction_type_raw is None:
            raise serializers.ValidationError("transaction_type is required.")

        transaction_type_norm = self._normalize_transaction_type(transaction_type_raw)
        user = User.objects.get(pk=user_id)
        amount = data.get("amount", 0)
        if transaction_type_norm == Transaction.DEPOSIT:
            user.money += amount
        elif transaction_type_norm == Transaction.WITHDRAW:
            user.money -= amount

        user.save(update_fields=["money", "updated_at"])
        return Transaction.objects.create(
            user=user,
            transaction_type=transaction_type_norm,
            **data,
        )


class StockOrderSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.filter(is_deleted=False), write_only=True
    )
    stock_id = serializers.PrimaryKeyRelatedField(
        source="stock", queryset=Stock.objects.filter(is_deleted=False), write_only=True
    )

    class Meta:
        model = Order
        fields = [
            "user_id",
            "stock_id",
            "asset_type",
            "side",
            "quantity",
            "execution_date",
            "execution_price",
            "created_at",
        ]
        read_only_fields = ["asset_type", "execution_price", "created_at"]

    def validate(self, data):
        data["asset_type"] = Order.ASSET_STOCK

        qty = data.get("quantity")
        if qty is None or qty <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")

        side = data.get("side")
        if side not in (Order.BUY, Order.SELL):
            raise serializers.ValidationError("Side must be BUY or SELL.")

        return data

    def create(self, data):
        validated_data = self.validate(data)
        
        stock = validated_data["stock"]
        stock_price = StockPrice.objects.filter(
            stock=stock,
            date__lte=validated_data["execution_date"],
        ).order_by('-date').first()
        
        user =  validated_data["user"]
        price = Decimal(str(stock_price.value))

        # Check the order type and validate funds or stock quantity
        if validated_data["side"] == Order.BUY:
            total_cost = price * validated_data["quantity"]
            if user.money < total_cost:
                raise serializers.ValidationError("Insufficient funds for this purchase.")

            user.money -= total_cost
            user.save(update_fields=["money", "updated_at"])
        elif validated_data["side"] == Order.SELL:
            totals = Order.objects.filter(
                user=user,
                stock=stock,
                execution_date__lte=validated_data["execution_date"],
            ).aggregate(
                total_bought=Sum('quantity', filter=Q(side=Order.BUY)),
                total_sold=Sum('quantity', filter=Q(side=Order.SELL)),
            )
            total_bought = totals.get('total_bought') or 0
            total_sold = totals.get('total_sold') or 0
            net_amount = total_bought - total_sold
            if net_amount < validated_data["quantity"]:
                raise serializers.ValidationError("Insufficient stock quantity to sell. Amount of stock available: {}".format(net_amount))
            
            user.money += price * validated_data["quantity"]
            user.save(update_fields=["money", "updated_at"])
            
        validated_data["execution_price"] = price
        
        # Execute the order and catch if fails to rollback money changes
        try:
            return Order.objects.create(**validated_data)
        except Exception as e:
            if validated_data["side"] == Order.BUY:
                user.money += price * validated_data["quantity"]
                user.save(update_fields=["money", "updated_at"])
            elif validated_data["side"] == Order.SELL:
                user.money -= price * validated_data["quantity"]
                user.save(update_fields=["money", "updated_at"])

            raise e


class PortfolioComponentInputSerializer(serializers.Serializer):
    symbol = serializers.SlugRelatedField(
        source="stock",
        slug_field="symbol",
        queryset=Stock.objects.filter(is_deleted=False),
    )
    weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=4,
        min_value=Decimal("0.001"),
    )


class PortfolioCreateSerializer(serializers.ModelSerializer):
    components = PortfolioComponentInputSerializer(many=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.filter(is_deleted=False), write_only=True
    )
    
    class Meta:
        model = Portfolio
        fields = ["id", "user_id","name", "description", "risk", "components"]
        read_only_fields = ["id"]

    def validate_components(self, components):
        if not components:
            raise serializers.ValidationError("Portfolio must have at least one component.")

        stock_ids = [c["stock"].id for c in components]
        if len(stock_ids) != len(set(stock_ids)):
            raise serializers.ValidationError("Each stock can appear only once in the portfolio.")

        total_weight = sum((c["weight"] for c in components), Decimal("0"))
        if total_weight != Decimal("1.0"):
            raise serializers.ValidationError(
                f"Weights must sum to 1. Current sum is {total_weight}."
            )

        return components

    def create(self, validated_data):
        components_data = validated_data.pop("components")

        portfolio = Portfolio.objects.create(**validated_data)

        PortfolioComponent.objects.bulk_create(
            [
                PortfolioComponent(
                    portfolio=portfolio,
                    stock=comp_data["stock"],
                    weight=comp_data["weight"],
                )
                for comp_data in components_data
            ]
        )

        return portfolio


class PortfolioMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ["id", "name", "description", "risk"]
        read_only_fields = ["id"]

class PortfolioInvestSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.filter(is_deleted=False),
        write_only=True,
    )
    portfolio_id = serializers.PrimaryKeyRelatedField(
        source="portfolio",
        queryset=Portfolio.objects.filter(is_deleted=False),
        write_only=True,
    )
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    execution_date = serializers.DateField(required=False)

    def validate(self, attrs):
        user = attrs["user"]
        portfolio = attrs["portfolio"]

        if user.money < attrs["amount"]:
            raise serializers.ValidationError("User does not have enough money to invest that amount.")

        components = PortfolioComponent.objects.filter(
            portfolio=portfolio,
            is_deleted=False,
        ).select_related("stock")

        if not components.exists():
            raise serializers.ValidationError("Portfolio has no components defined.")

        attrs["_components"] = list(components)
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        portfolio = validated_data["portfolio"]
        amount = validated_data["amount"]
        execution_date = validated_data.get("execution_date") or date.today()
        components = validated_data["_components"]

        total_weight = sum((c.weight for c in components), Decimal("0"))
        if total_weight <= 0:
            raise serializers.ValidationError("Total weight of portfolio components must be greater than 0.")

        orders = []
        remaining_amount = amount

        for index, component in enumerate(components):
            # Normalize weight in case total_weight != 1 exactly
            weight_fraction = component.weight / total_weight

            # Last component gets whatever is left to avoid rounding leftovers
            if index < len(components) - 1:
                alloc = (amount * weight_fraction).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
                remaining_amount -= alloc
            else:
                alloc = remaining_amount

            stock_price = StockPrice.objects.filter(
                stock=component.stock,
                date__lte=execution_date,
            ).order_by('-date').first()
            price = Decimal(str(stock_price.value)) if stock_price else Decimal("0")
            if price <= 0:
                continue

            # Quantity with 4 decimal places
            quantity = (alloc / price).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
            if quantity <= 0:
                continue

            order = Order.objects.create(
                user=user,
                asset_type=Order.ASSET_STOCK,
                side=Order.BUY,
                stock=component.stock,
                portfolio=portfolio,
                quantity=quantity,
                execution_price=price,
                execution_date=execution_date,
            )
            orders.append(order)

        user.money -= amount
        user.save(update_fields=["money"])

        return {
            "user_id": user.id,
            "portfolio_id": portfolio.id,
            "amount_invested": amount,
            "orders": orders,
        }

    def to_representation(self, instance):
        return {
            "user_id": instance["user_id"],
            "portfolio_id": instance["portfolio_id"],
            "amount_invested": str(instance["amount_invested"]),
            "orders": [
                {
                    "order_id": o.id,
                    "symbol": o.stock.symbol,
                    "quantity": str(o.quantity),
                    "execution_price": str(o.execution_price),
                    "value": str(o.quantity * o.execution_price),
                }
                for o in instance["orders"]
            ],
        }


class PositionSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4)
    price = serializers.DecimalField(max_digits=18, decimal_places=4)
    value = serializers.DecimalField(max_digits=18, decimal_places=4)


class PortfolioTotalSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    cash = serializers.DecimalField(max_digits=18, decimal_places=2)
    stocks_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    portfolio_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    positions = PositionSerializer(many=True)
