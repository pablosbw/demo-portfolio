from rest_framework import serializers
from .models import Stock, StockPrice, User, Transaction, Order
from decimal import Decimal
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
