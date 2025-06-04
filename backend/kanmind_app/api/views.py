from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response

from kanmind_app.models import Board, Task, Comment
from .serializers import (
    BoardListSerializer, BoardCreateSerializer, BoardDetailSerializer,
    TaskListSerializer, TaskCreateUpdateSerializer,
    CommentSerializer, CommentCreateSerializer
)

class EmailCheckAPIView(APIView):
    """
    GET /api/email-check/?email=<email>
    Returns basic info if the email exists, else 404.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Validate 'email' query param, look up User by email,
        and return id, email, fullname.
        """
        email = request.query_params.get('email')
        if not email:
            return Response(
                {'email': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'email': ["This email address does not exist."]},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id':       user.id,
            'email':    user.email,
            'fullname': user.get_full_name() or user.username
        }, status=status.HTTP_200_OK)

class BoardListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/boards/           -> list boards of current user (with counts)
    POST /api/boards/           -> create new board, return list-style data
    GET  /api/boards/?id=<id>   -> same as GET detail
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Return BoardDetailSerializer if 'id' in GET query; 
        return BoardCreateSerializer for POST; else List.
        """
        if self.request.method == 'GET' and 'id' in self.request.query_params:
            return BoardDetailSerializer
        
        if self.request.method == 'POST':
            return BoardCreateSerializer

        return BoardListSerializer

    def get_queryset(self):
        """
        Return boards where user is owner or member, annotated with counts.
        """
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).annotate(
            member_count=Count('members', distinct=True),
            ticket_count=Count('tasks', distinct=True),
            tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to-do')),
            tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high'))
        )

    def list(self, request, *args, **kwargs):
        """
        If 'id' query param is present, return that board’s detail; else list.
        """
        board_id = request.query_params.get('id')
        if board_id is not None:
            board = get_object_or_404(self.get_queryset(), id=board_id)
            serializer = self.get_serializer(board)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Validate input, create board with owner=request.user, add members,
        and return list-style serialized board including counts.
        """
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        board_obj = create_serializer.save(owner=request.user)
        board_obj.members.add(request.user)

        members_data = create_serializer.validated_data.get('members', [])
        for usr in members_data:
            board_obj.members.add(usr)

        full_qs = self.get_queryset().filter(id=board_obj.id)
        board_with_counts = full_qs.first()

        output_serializer = BoardListSerializer(board_with_counts)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class BoardRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/boards/<pk>/    -> retrieve board detail
    PATCH/PUT                -> update (members only if provided)
    DELETE                   -> delete (only owner allowed)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = BoardDetailSerializer
    queryset          = Board.objects.all()

    def get_object(self):
        """
        Ensure request.user is owner or member; else raise 403.
        """
        obj = super().get_object()
        user = self.request.user

        if not (obj.owner == user or user in obj.members.all()):
            raise PermissionDenied("Not a member of this board.")

        return obj

    def perform_update(self, serializer):
        """
        Update the board title and optionally replace members with given list.
        """
        board = serializer.save()
        members_data = self.request.data.get('members', None)
        if members_data is not None:
            board.members.clear()
            for member_id in members_data:
                try:
                    usr = User.objects.get(pk=member_id)
                    board.members.add(usr)
                except User.DoesNotExist:
                    pass

    def perform_destroy(self, instance):
        """
        Only the owner may delete; else raise 403.
        """
        user = self.request.user
        
        if instance.owner != user:
            raise PermissionDenied("Only the owner is able to delete this board.")
        
        return super().perform_destroy(instance)

class TasksAssignedToMeListAPIView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    Returns all tasks where current user is the assignee.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskListSerializer

    def get_queryset(self):
        """
        Filter tasks assigned to current user, annotate comment counts.
        """
        user = self.request.user
        return Task.objects.filter(
            assignee=user
        ).annotate(
            comments_count=Count('comments')
        )

class TasksReviewingListAPIView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/
    Returns all tasks where current user is the reviewer.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskListSerializer

    def get_queryset(self):
        """
        Filter tasks where current user is reviewer, annotate comment counts.
        """
        user = self.request.user
        return Task.objects.filter(
            reviewer=user
        ).annotate(
            comments_count=Count('comments')
        )

class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/tasks/         -> list tasks current user can see (owner/member/assignee/reviewer)
    POST /api/tasks/         -> create new task on given board (if authorized)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Use TaskCreateUpdateSerializer for POST; else TaskListSerializer.
        """
        if self.request.method == 'POST':
            return TaskCreateUpdateSerializer
        return TaskListSerializer

    def get_queryset(self):
        """
        Return tasks where user is board owner/member/assignee/reviewer, annotated.
        """
        user = self.request.user
        return Task.objects.filter(
            Q(board__owner=user) |
            Q(board__members=user) |
            Q(assignee=user) |
            Q(reviewer=user)
        ).annotate(
            comments_count=Count('comments', distinct=True)
        )

    def create(self, request, *args, **kwargs):
        """
        Validate board existence and membership, then create task.
        Returns TaskListSerializer data with comments_count.
        """
        board_id = request.data.get('board')
        if board_id is None:
            raise ValidationError({"board": ["This field is required."]})

        try:
            board_obj = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound(detail="Board not found.")

        user = request.user
        if not (board_obj.owner == user or user in board_obj.members.all()):
            raise PermissionDenied(detail="You have to be a member of this board in order to add a task.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignee_user = serializer.validated_data.get('assignee', None)
        if assignee_user and not (assignee_user == board_obj.owner or assignee_user in board_obj.members.all()):
            raise PermissionDenied(detail="Assignee has to be a member of this board.")

        reviewer_user = serializer.validated_data.get('reviewer', None)
        if reviewer_user and not (reviewer_user == board_obj.owner or reviewer_user in board_obj.members.all()):
            raise PermissionDenied(detail="Reviewer has to be a member of this board.")

        task_obj = serializer.save()

        task_with_counts = Task.objects.filter(pk=task_obj.pk).annotate(
            comments_count=Count('comments', distinct=True)
        ).first()
        output_serializer = TaskListSerializer(task_with_counts)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/tasks/<pk>/     -> retrieve task data
    PATCH/PUT                -> update task (only if user is board owner or member)
    DELETE                   -> delete task (only if user is board owner or member)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskCreateUpdateSerializer
    queryset          = Task.objects.all()

    def get_object(self):
        """
        Ensure request.user is allowed to modify this task.
        """
        obj = super().get_object()
        user = self.request.user
        if not (obj.board.owner == user or user in obj.board.members.all()):
            raise permissions.PermissionDenied("Not authorized to modify this task.")
        return obj

class CommentListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/tasks/<task_id>/comments/        -> list comments on task (if authorized)
    POST /api/tasks/<task_id>/comments/        -> create comment (if authorized)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Use CommentCreateSerializer for POST; else CommentSerializer.
        """
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        """
        Return comments for the given task if user is board member/owner.
        """
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, pk=task_id)
        user = self.request.user
        if not (task.board.owner == user or user in task.board.members.all()):
            raise PermissionDenied("Not permitted to view comments.")
        return task.comments.all().order_by('created_at')

    def create(self, request, *args, **kwargs):
        """
        Validate task exists, membership, then create comment.
        Return serialized Comment with status 201.
        """
        task_id = self.kwargs['task_id']

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound(detail="Task not found.")

        user = request.user

        if not (task.board.owner == user or user in task.board.members.all()):
            raise PermissionDenied("You have to be a member of this board in order to add a comment.")

        create_serializer = CommentCreateSerializer(data=request.data, context={'task': task, 'request': request})
        create_serializer.is_valid(raise_exception=True)

        comment_obj = create_serializer.save()

        output_serializer = CommentSerializer(comment_obj)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class CommentDestroyAPIView(generics.DestroyAPIView):
    """
    DELETE /api/tasks/<task_id>/comments/<comment_id>/
    Deletes specified comment if current user is the author.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = None
    lookup_url_kwarg  = 'comment_id'
    lookup_field = 'pk'

    def get_queryset(self):
        """
        Return queryset of comments belonging to the specified task.
        """
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.comments.all()

    def destroy(self, request, *args, **kwargs):
        """
        Ensure request.user is author, then delete comment.
        """
        comment = self.get_object()
        if comment.author != request.user:
            raise PermissionDenied("Not allowed to delete this comment.")
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)