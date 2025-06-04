from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from kanmind_app.models import Board, Task, Comment

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer to return minimal User info:
    id, email, and computed fullname.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, user):
        """
        Return the User's full name if set, else the username.
        """
        return user.get_full_name() or user.username

class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Board instances.
    Includes computed counts and owner ID.
    """
    member_count          = serializers.IntegerField(read_only=True)
    ticket_count          = serializers.IntegerField(read_only=True)
    tasks_to_do_count     = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)
    owner_id              = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id','title','member_count','ticket_count',
            'tasks_to_do_count','tasks_high_prio_count','owner_id'
        ]

class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Board.
    Accepts a list of member user IDs (write-only).
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        allow_empty=True,
        write_only=True
    )

    class Meta:
        model  = Board
        fields = ['id', 'title', 'members']

class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Task instances.
    Includes board ID, assignee/reviewer basics, and comment count.
    """
    board           = serializers.IntegerField(source='board.id', read_only=True)
    assignee        = UserMinimalSerializer(read_only=True)
    reviewer        = UserMinimalSerializer(read_only=True)
    comments_count  = serializers.IntegerField()

    class Meta:
        model  = Task
        fields = [
            'id', 'board', 'title', 'description', 'status',
            'priority', 'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed Board data.
    Includes owner ID, list of non-owner members, and tasks with counts.
    """
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members  = serializers.SerializerMethodField()
    tasks    = serializers.SerializerMethodField()

    class Meta:
        model  = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']

    def get_members(self, board_obj):
        """
        Return serialized members excluding the owner.
        """
        qs = board_obj.members.exclude(pk=board_obj.owner_id)
        return UserMinimalSerializer(qs, many=True).data

    def get_tasks(self, board_obj):
        """
        Return serialized tasks with comment counts for this board.
        """
        qs = board_obj.tasks.annotate(comments_count=Count('comments'))
        return TaskListSerializer(qs, many=True).data

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating a Task.
    Accepts board ID, optional assignee_id, required reviewer_id.
    """
    board    = serializers.IntegerField(write_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        allow_null=True,
        required=False
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='reviewer',
        allow_null=True,
        required=True
    )

    class Meta:
        model  = Task
        fields = [
            'id', 'board', 'title', 'description', 'status',
            'priority', 'assignee_id', 'reviewer_id', 'due_date'
        ]
    
    def create(self, validated_data):
        """
        Create a new Task after validating the board exists.
        Adds created_by from request user.
        """
        board_pk = validated_data.pop('board')
        try:
            board_obj = Board.objects.get(pk=board_pk)
        except Board.DoesNotExist:
            raise NotFound(detail="Board not found.")

        validated_data['board'] = board_obj

        request_user = self.context['request'].user
        return Task.objects.create(
            created_by=request_user,
            **validated_data
        )

    def update(self, instance, validated_data):
        """
        Update an existing Task instance.
        """
        return super().update(instance, validated_data)

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Comment instances.
    Returns comment ID, creation time, author name, and content.
    """
    author = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        """
        Return the comment author's full name or username.
        """
        return obj.author.get_full_name() or obj.author.username

class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Comment.
    The Task context is passed in via serializer context.
    """
    class Meta:
        model  = Comment
        fields = ['id', 'content']

    def create(self, validated_data):
        """
        Create a new Comment linked to the context task and request user.
        """
        task   = self.context['task']
        author = self.context['request'].user
        return Comment.objects.create(
            task=task, author=author, content=validated_data['content']
        )