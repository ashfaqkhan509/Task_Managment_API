from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from tasks.models import Task
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta, date
from rest_framework.settings import api_settings
from django.core import mail
from django.utils import timezone
from tasks.tasks import send_due_task_reminders


class AuthTests(APITestCase):
    """
    Test suite for user registration and login endpoints using JWT authentication.
    Covers successful and failed cases for both registration and login.
    """

    def setUp(self):
        """
        Set up test data and endpoint URLs for each test case.
        """

        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            "username": "ashfaq",
            "email": "ashfaq@example.com",
            "first_name": "Ashfaq",
            "last_name": "Khan",
            "password": "test1234",
            "confirm_password": "test1234"
        }

    def test_user_registration_success(self):
        """
        Ensure a new user can register successfully.
        Validates the response message, created username, and database entry.
        """

        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])
        self.assertTrue(User.objects.filter(username=self.user_data['username']).exists())

    def test_user_registration_duplicate_username(self):
        """
        Ensure that registering with an existing username fails with a 400 status code.
        """

        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """
        Ensure a registered user can log in successfully and receive JWT tokens.
        """

        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {
            "username": self.user_data['username'],
            "password": self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        """
        Ensure login fails with invalid credentials, returning a 401 status code.
        """

        login_data = {
            "username": "hello",
            "password": "hello"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_missing_fields(self):
        """
        Ensure login fails if username and password fields are missing.
        Returns a 400 status code.
        """

        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskCRUDTests(APITestCase):
    """
    Test suite for CRUD operations on Task model.
    Ensures that authenticated users can create, list, retrieve, update, and delete tasks.
    """

    def setUp(self):
        """
        Create a test user and authenticate using JWT.
        Prepare common URLs and initial task data.
        """
        self.user = User.objects.create_user(username="ashfaq", password="test1234")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.task_list_url = reverse('task-list-create')
        self.task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "due_date": (date.today() + timedelta(days=1)).isoformat(),
            "is_completed": False
        }

    def test_create_task(self):
        """
        Ensure an authenticated user can create a new task.
        """
        response = self.client.post(self.task_list_url, self.task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.first().title, self.task_data['title'])

    def test_list_tasks(self):
        """
        Ensure the list endpoint returns tasks owned by the authenticated user.
        """
        Task.objects.create(owner=self.user, **self.task_data)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_task(self):
        """
        Ensure an authenticated user can retrieve a specific task by ID.
        """
        task = Task.objects.create(owner=self.user, **self.task_data)
        url = reverse('task-detail', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], task.title)

    def test_update_task(self):
        """
        Ensure an authenticated user can update their own task.
        """
        task = Task.objects.create(owner=self.user, **self.task_data)
        url = reverse('task-detail', args=[task.id])
        updated_data = {**self.task_data, "title": "Updated Task"}
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated Task")

    def test_delete_task(self):
        """
        Ensure an authenticated user can delete their own task.
        """
        task = Task.objects.create(owner=self.user, **self.task_data)
        url = reverse('task-detail', args=[task.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)


class TaskFilterSearchTests(APITestCase):
    """
    Test suite for filtering and searching tasks using DRF filters.
    Includes filtering by completion status, due date, and search by title.
    """

    def setUp(self):
        """
        Create a test user, authenticate using JWT, and create multiple tasks
        with varying titles, due dates, and completion statuses.
        """
        self.user = User.objects.create_user(username="ashfaq", password="test1234")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.task_list_url = reverse('task-list-create')

        Task.objects.create(
            owner=self.user,
            title="implement testcases",
            description="unittest, integration test",
            due_date=date.today() + timedelta(days=1),
            is_completed=False
        )
        Task.objects.create(
            owner=self.user,
            title="Finish project",
            description="Complete the Django API project",
            due_date=date.today() - timedelta(days=1),
            is_completed=True
        )
        Task.objects.create(
            owner=self.user,
            title="Book tickets",
            description="Bus tickets for going to home",
            due_date=date.today() + timedelta(days=5),
            is_completed=False
        )

    def test_filter_by_is_completed(self):
        """
        Ensure tasks can be filtered by completion status (is_completed).
        """
        response = self.client.get(self.task_list_url, {'is_completed': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertTrue(task['is_completed'])

    def test_filter_by_due_date(self):
        """
        Ensure tasks can be filtered by specific due date.
        """
        target_due_date = (date.today() + timedelta(days=1)).isoformat()
        response = self.client.get(self.task_list_url, {'due_date': target_due_date})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertEqual(task['due_date'], target_due_date)

    def test_search_by_title(self):
        """
        Ensure tasks can be searched by title using the SearchFilter.
        """
        response = self.client.get(self.task_list_url, {'search': 'Finish project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertIn('finish project', task['title'].lower())


class RateLimitingTests(APITestCase):
    """
    Test suite for verifying the daily rate limit for authenticated users.
    """

    def setUp(self):
        """
        Create a test user and authenticate using JWT.
        """
        self.user = User.objects.create_user(username="testuser", password="test1234")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.url = '/api/tasks/'

        # Read the user rate limit from settings 100/day
        rate = api_settings.DEFAULT_THROTTLE_RATES.get('user', '100/day')
        self.limit = int(rate.split('/')[0])

    def test_rate_limit_enforced(self):
        """
        Ensure that a user cannot exceed the configured daily request limit.
        """
        # Make requests equal to the daily limit
        for _ in range(self.limit):
            response = self.client.get(self.url)
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Next request should trigger throttling
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TaskReminderTests(APITestCase):
    """
    Test suite for verifying the Reminder task that sned mail to
    those user whose task is duw by 24 hours.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username="ashfaq",
            email="ashfaq319535@example.com",
            password="test1234"
        )

    def test_send_due_task_reminders(self):
        # Task due within 24 hours should trigger email
        Task.objects.create(
            owner=self.user,
            title="Finish assignment",
            description="Complete the Celery task",
            due_date=timezone.now() + timedelta(hours=23),
            is_completed=False
        )

        # Task due after 2 days -> should not trigger email
        Task.objects.create(
            owner=self.user,
            title="Future task",
            description="Not due soon",
            due_date=timezone.now() + timedelta(days=2),
            is_completed=False
        )

        # Run the task manually
        send_due_task_reminders()

        # Check that only one email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Finish assignment", mail.outbox[0].subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
