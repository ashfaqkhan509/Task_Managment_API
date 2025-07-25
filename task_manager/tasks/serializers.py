from rest_framework import serializers
from django.contrib.auth.models import User
from tasks.models import Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'is_completed', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskShareSerializer(serializers.Serializer):
    """
    Serializer for sharing a task with another user.
    Accepts either user_id or email of the recipient.
    """
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("email"):
            raise serializers.ValidationError("Provide either user_id or email")
        return attrs


class TaskCompleteSerializer(serializers.ModelSerializer):
    """
    Serializer for marking a task as completed.
    Returns updated task data.
    """
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'is_completed']
        read_only_fields = ['id', 'title', 'description', 'is_completed']
