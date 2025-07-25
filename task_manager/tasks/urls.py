from django.urls import path
from tasks import views


urlpatterns = [
    # Authenthication
    path('auth/register/', views.UserRegisterView.as_view(), name="register"),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),

    # Task API
    path('tasks/', views.TaskListCreateView.as_view(), name="task-list-create"),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name="task-detail"),
    path('tasks/<int:pk>/complete/', views.TaskCompleteView.as_view(), name="task-complete"),
    path('tasks/<int:id>/share/', views.TaskShareView.as_view(), name="share-task")
]
