from django.shortcuts            import get_object_or_404
from django.db.models           import Count, Q
from django.contrib.auth.models import User
from rest_framework             import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views       import APIView
from rest_framework.response    import Response

from kanmind_app.models     import Board, Task, Comment
from .serializers import (
    BoardListSerializer, BoardCreateSerializer, BoardDetailSerializer,
    TaskListSerializer, TaskCreateUpdateSerializer,
    CommentSerializer, CommentCreateSerializer
)

class EmailCheckAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
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
                {'email': ["This email address doesn't exist."]},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id':       user.id,
            'email':    user.email,
            'fullname': user.get_full_name() or user.username
        }, status=status.HTTP_200_OK)

class BoardListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET' and 'id' in self.request.query_params:
            return BoardDetailSerializer
        
        if self.request.method == 'POST':
            return BoardCreateSerializer

        return BoardListSerializer

    def get_queryset(self):
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
        board_id = request.query_params.get('id')
        if board_id is not None:
            board = get_object_or_404(self.get_queryset(), id=board_id)
            serializer = self.get_serializer(board)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = BoardDetailSerializer
    queryset          = Board.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        # if not (obj.owner == user or user in obj.members.all()):
        #     raise permissions.PermissionDenied("Not a member of this board.")

        if not (obj.owner == user or user in obj.members.all()):
            raise PermissionDenied("Not a member of this board.")

        return obj

    def perform_update(self, serializer):
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
        user = self.request.user

        # if instance.owner != user:
        #     raise permissions.PermissionDenied("Only the owner is able to delete this board.")
        
        if instance.owner != user:
            raise PermissionDenied("Only the owner is able to delete this board.")
        
        return super().perform_destroy(instance)

class TasksAssignedToMeListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskListSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            assignee=user
        ).annotate(
            comments_count=Count('comments')
        )

class TasksReviewingListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskListSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            reviewer=user
        ).annotate(
            comments_count=Count('comments')
        )

class TaskListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskCreateUpdateSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(board__owner=user) | Q(board__members=user)
        ).annotate(
            comments_count=Count('comments')
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = TaskCreateUpdateSerializer
    queryset          = Task.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if not (obj.board.owner == user or user in obj.board.members.all()):
            raise permissions.PermissionDenied("Not authorized to modify this task.")
        return obj

class CommentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = CommentSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, pk=task_id)
        user = self.request.user
        if not (task.board.owner == user or user in task.board.members.all()):
            raise permissions.PermissionDenied("Not permitted to view comments.")
        return task.comments.all().order_by('created_at')

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        serializer.context.update({'task': task})
        serializer.save()

class CommentDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class  = CommentSerializer
    lookup_url_kwarg  = 'comment_id'

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.comments.all()

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            raise permissions.PermissionDenied("Not allowed to delete this comment.")
        return super().destroy(request, *args, **kwargs)






#class IsBoardMemberOrOwner(permissions.BasePermission):
#    def has_object_permission(self, req, view, obj):
#        return req.user == obj.owner or obj.members.filter(pk=req.user.pk).exists()

#class IsTaskMember(permissions.BasePermission):
#    def has_object_permission(self, req, view, obj):
#        return req.user == obj.board.owner or obj.board.members.filter(pk=req.user.pk).exists()

#class IsCommentAuthor(permissions.BasePermission):
#    def has_object_permission(self, req, view, obj):
#        return req.user == obj.author

#class TaskAssignedListAPIView(generics.ListAPIView):
#    serializer_class = TaskBaseSerializer
#    permission_classes = [permissions.IsAuthenticated]
#
#    def get_queryset(self):
#        return Task.objects.filter(assignee=self.request.user).annotate(comments_count=Count('comments'))