from .models import Order, Portfolio, Transaction, User, Stock
from .serializers import DepositSerializer, PortfolioCreateSerializer, PortfolioInvestSerializer, PortfolioMetadataSerializer, StockOrderSerializer, UserSerializer
from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Q


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

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        stocks_id = Stock.objects.filter(is_deleted=False).values_list('pk', flat=True)
        stock_quantities = {}
        for stock_id in stocks_id:
            totals = Order.objects.filter(user=user, stock_id=stock_id, is_deleted=False).aggregate(
                total_bought=Sum('quantity', filter=Q(side=Order.BUY)),
                total_sold=Sum('quantity', filter=Q(side=Order.SELL)),
            )
            total_bought = totals.get('total_bought') or 0
            total_sold = totals.get('total_sold') or 0
            net_amount = total_bought - total_sold

            if net_amount > 0:
                stock_name = Stock.objects.get(pk=stock_id).symbol
                stock_quantities[stock_name] = str(net_amount)

        if stock_quantities:
            return Response(
                {"detail": f"User has associated stock orders and cannot be deleted. You have the following stocks with remaining quantities: {stock_quantities}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if user.money > 0:
            return Response(
                {"detail": "User has remaining money and cannot be deleted. Total money remaining: " + str(user.money)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_deleted = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        if not user_id:
            return Transaction.objects.none()

        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id).order_by('-created_at')


@extend_schema(
    summary="Register a BUY or SELL order for a Stock",
    description=(
        "Creates an order of type BUY or SELL for a user on a specific stock. "
        "This endpoint handles only stock trades (not portfolios)."
    ),
    request=StockOrderSerializer,
    responses={201: StockOrderSerializer},
)
class StockOrderCreateView(generics.CreateAPIView):
    serializer_class = StockOrderSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Response(
                {"detail": "User not found or deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    summary="Create a portfolio",
    description=(
        "Crea un portafolio seleccionando entre los stocks disponibles. "
        "Los pesos de los componentes deben sumar 1."
    ),
    request=PortfolioCreateSerializer,
    responses={201: PortfolioCreateSerializer},
)
class PortfolioCreateView(generics.CreateAPIView):
    queryset = Portfolio.objects.filter(is_deleted=False)
    serializer_class = PortfolioCreateSerializer


@extend_schema(
    summary="Get all portfolios of a user",
    description="Given a user, gets all portfolios.",
    request=PortfolioCreateSerializer,
    responses={201: PortfolioCreateSerializer},
)
class PortfolioListView(generics.ListAPIView):
    serializer_class = PortfolioCreateSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if not user_id:
            return Transaction.objects.none()

        if not User.objects.filter(pk=user_id, is_deleted=False).exists():
            return Portfolio.objects.none()
        return Portfolio.objects.filter(user_id=user_id, is_deleted=False)


@extend_schema(
    summary="Edit portfolio metadata",
    description=(
        "Edita la información de un portafolio existente: nombre, descripción y nivel de riesgo. "
        "Este endpoint **no** modifica la composición (stocks/pesos) del portafolio."
    ),
    request=PortfolioMetadataSerializer,
    responses={200: PortfolioMetadataSerializer},
)
class PortfolioMetadataUpdateView(generics.RetrieveUpdateAPIView):
    # TODO: Implement portfolio composition modification.
    """
    GET    /api/portfolios/<id>/  Obtiene los metadatos del portafolio
    PUT    /api/portfolios/<id>/  Reemplaza los metadatos (name, description, risk)
    PATCH  /api/portfolios/<id>/  Actualiza los metadatos parcialmente
    """
    queryset = Portfolio.objects.filter(is_deleted=False)
    serializer_class = PortfolioMetadataSerializer

@extend_schema(
    summary="Invest an amount of money into a portfolio",
    description=(
        "Recibe un usuario, un portafolio y un monto a invertir. "
        "Distribuye el monto entre las acciones del portafolio según sus pesos, "
        "y crea órdenes de compra (BUY) por cada acción correspondiente. "
        "Las órdenes creadas quedan asociadas al portafolio."
    ),
    request=PortfolioInvestSerializer,
    responses={201: PortfolioInvestSerializer},
)
class PortfolioInvestView(generics.CreateAPIView):
    serializer_class = PortfolioInvestSerializer
    queryset = Order.objects.none()

