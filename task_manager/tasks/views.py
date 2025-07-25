from rest_framework import (
    generics,
    status,
    permissions,
    filters
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from tasks.models import Task
from tasks.serializers import (
    UserSerializer,
    RegisterSerializer,
    TaskSerializer
)


class UserRegisterView(generics.CreateAPIView):
    """
    API endpoint that allows new users to register.

    Creates a new user instance with the provided credentials.
    Returns the created user data and a success message.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {
            "message": "User Registerd successfully",
            "user": UserSerializer(user).data
        }
        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """
    API endpoint for user authentication.

    Accepts username and password credentials.
    Returns JWT tokens (access and refresh) upon successful authentication.
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh_token = RefreshToken.for_user(user)

        response_data = {
            "user": UserSerializer(user).data,
            "refresh": str(refresh_token),
            "access": str(refresh_token.access_token),
            "message": "Login successful."
        }
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


class TaskListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating tasks.

    Requires authentication.
    Supports filtering by completion status and due date,
    and searching by task title.
    Tasks are automatically associated with the authenticated user.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_completed", "due_date"]
    search_fields = ["title"]

    def get_queryset(self):
        """
        Return only tasks belonging to the authenticated user.
        """
        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Associate the created task with the authenticated user.
        """
        serializer.save(owner=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, or deleting a specific task.

    Requires authentication.
    Only allows access to tasks owned by the authenticated user.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return only tasks belonging to the authenticated user.
        """
        return Task.objects.filter(owner=self.request.user)


class TaskCompleteView(APIView):
    """
    API endpoint for marking a task as completed.

    Requires authentication.
    Only the task owner can mark a task as completed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        """
        Update the task's completion status to True.

        Args:
            pk: Primary key of the task to be marked as completed.

        Returns:
            Success message or error if task not found.
        """
        try:
            task = Task.objects.get(pk=pk, owner=request.user)
        except task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        task.is_completed = True
        task.save()
        return Response(
            {"message": "Task marked as completed"},
            status=status.HTTP_200_OK
        )


class TaskShareView(APIView):
    """
    API endpoint for sharing a task with another user.

    Requires authentication.
    Only the task owner can share the task.
    Accepts either user_id or email to identify the user to share with.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """
        Share a task with another user.

        Args:
            pk: Primary key of the task to be shared.

        Request Body:
            user_id: ID of the user to share with, or
            email: Email of the user to share with

        Returns:
            Success message or error if task/user not found.
        """
        try:
            task = Task.objects.get(pk=pk, owner=request.user)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user_id = request.data.get("user_id")
        user_email = request.data.get("email")

        if not user_id and not user_email:
            return Response(
                {"error": "Provide either user_id or email"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if user_id:
                user_to_share = User.objects.get(pk=user_id)
            else:
                user_to_share = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        task.share_with.add(user_to_share)
        return Response(
            {"message": f"Task shared with {user_to_share.username}"},
            status=status.HTTP_200_OK
        )
