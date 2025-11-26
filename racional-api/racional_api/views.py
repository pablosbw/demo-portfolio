from .models import Transaction, User
from .serializers import DepositSerializer, UserSerializer
from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal, InvalidOperation


@extend_schema_view(
    get=extend_schema(
        summary="Get all users",
        description="Get all non deleted users",
        responses=UserSerializer(many=True),
    ),
    post=extend_schema(
        summary="Create a user",
        description="Create a new user.",
        request=UserSerializer,
        responses={201: UserSerializer},
    ),
)
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer


@extend_schema(
    summary="Retrieve, update or delete the user",
    description="Retrieve, update (partial allowed) or delete a user.",
    request=UserSerializer,
    responses={200: UserSerializer, 204: None},
)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/users/<int:pk>/
    Combined endpoint for retrieve, update and delete.
    """
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


@extend_schema(
    summary="Register a cash deposit",
    description="Creates a cash deposit order for a given user.",
    request=DepositSerializer,
    responses={201: DepositSerializer},
)
class DepositCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = DepositSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["transaction_type"] = Transaction.DEPOSIT
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user_id = data.get("user_id")
        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Response(
                {"user_id": ["Invalid user ID."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(data.get("amount")))
        except (TypeError, InvalidOperation):
            return Response({"amount": ["Invalid amount."]}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"amount": ["Amount must be greater than zero."]}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    summary="Register a cash withdrawal",
    description="Creates a cash withdrawal order for a given user.",
    request=DepositSerializer,
    responses={201: DepositSerializer},
)
class WithdrawCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = DepositSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["transaction_type"] = Transaction.WITHDRAW
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user_id = data.get("user_id")
        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Response(
                {"user_id": ["Invalid user ID."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(data.get("amount")))
        except (TypeError, InvalidOperation):
            return Response({"amount": ["Invalid amount."]}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"amount": ["Amount must be greater than zero."]}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(pk=user_id)
        if amount > user.money:
            return Response({"amount": ["Insufficient funds."]}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(
    summary="Get all transactions for a user",
    description="Given a user, gets all transactions.",
    request=DepositSerializer,
    responses={201: DepositSerializer},
)
class TransactionListView(generics.ListAPIView):
    serializer_class = DepositSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        
        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id)


