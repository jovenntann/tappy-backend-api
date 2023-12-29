# DRF
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

# Permissions
from domain.user.permissions.groups import IsAdminOrHumanResource

# Serializers
from .serializers import ReadUserSerializer, \
    CreateUserSerializer, PaginateReadUserSerializer, \
    PaginateQueryReadUserSerializer

# Services
from domain.user.services.user import get_users, create_user

# Memphis
from asgiref.sync import async_to_sync
from domain.memphis.services.producer import create_message

# Library: drf-yasg
from drf_yasg.utils import swagger_auto_schema

import logging
logger = logging.getLogger(__name__)


class UsersAPIView(APIView):

    permission_classes = (IsAdminOrHumanResource,)

    @staticmethod
    @swagger_auto_schema(
        responses={
            200: PaginateReadUserSerializer()
        },
        operation_id="users_list",
        tags=["user-management.users"],
        query_serializer=PaginateQueryReadUserSerializer()
    )
    def get(request):
        logger.info(f"authenticated: {request.user}")
        users = get_users()
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(users, request)
        user_serializer = ReadUserSerializer(result_page, many=True)
        return paginator.get_paginated_response(user_serializer.data)

    @staticmethod
    @swagger_auto_schema(
        request_body=CreateUserSerializer,
        operation_description="description",
        operation_id="users_create",
        tags=["user-management.users"],
        responses={
            200: ReadUserSerializer()
        }
    )
    def post(request, pk=None, *args, **kwargs):
        logger.info(f"authenticated: {request.user}")
        user_serializer = CreateUserSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user = create_user(user_serializer.validated_data['username'], user_serializer.validated_data['password'], user_serializer.validated_data['first_name'], user_serializer.validated_data['last_name'], user_serializer.validated_data['email'])
        user_serializer = ReadUserSerializer(user)

        message = {
            "event": "user_created",
            "data": {
                "user_id": user.id
            }
        }

        async_to_sync(create_message)(message)

        return Response(user_serializer.data)
