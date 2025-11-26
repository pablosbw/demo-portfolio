from .models import Transaction, User
from .serializers import DepositSerializer, UserSerializer
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status


@extend_schema(
    summary="Create, update or delete the user",
    description="Create, update (partial allowed) or delete a user.",
    request=UserSerializer,
    responses={200: UserSerializer, 204: None},
)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/users/<int:pk>/
    Combined endpoint for Create, update and delete.
    """
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

