from rest_framework import serializers
from .models import User, Transaction

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
