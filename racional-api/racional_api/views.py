from .models import Transaction, User
from .serializers import DepositSerializer, UserSerializer
from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework import status

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

