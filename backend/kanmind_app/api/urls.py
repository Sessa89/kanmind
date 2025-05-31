from django.urls import path
from .views import (
    EmailCheckAPIView,
    BoardListCreateAPIView, BoardRetrieveUpdateDestroyAPIView,
    TasksAssignedToMeListAPIView, TasksReviewingListAPIView,
    TaskListCreateAPIView, TaskRetrieveUpdateDestroyAPIView,
    CommentListCreateAPIView, CommentDestroyAPIView
)

urlpatterns = [
    path('boards/',          BoardListCreateAPIView.as_view(),              name='boards-list'),
    path('boards/<int:pk>/', BoardRetrieveUpdateDestroyAPIView.as_view(),   name='boards-detail'),

    path('tasks/assigned-to-me/', TasksAssignedToMeListAPIView.as_view(),   name='tasks-assigned'),
    path('tasks/reviewing/',      TasksReviewingListAPIView.as_view(),      name='tasks-reviewing'),

    path('tasks/',            TaskListCreateAPIView.as_view(),              name='tasks-list'),
    path('tasks/<int:pk>/',   TaskRetrieveUpdateDestroyAPIView.as_view(),   name='tasks-detail'),

    path('tasks/<int:task_id>/comments/',                  CommentListCreateAPIView.as_view(),   name='comments-list'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/', CommentDestroyAPIView.as_view(),      name='comments-detail'),

    path('email-check/', EmailCheckAPIView.as_view(), name='email-check'),
]