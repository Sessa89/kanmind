from rest_framework import serializers
from django.contrib.auth.models import User
from kanmind_app.models import Board, Task, Comment

class UserMinimalSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, user):
        return user.get_full_name() or user.username

class BoardListSerializer(serializers.ModelSerializer):
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
    assignee       = UserMinimalSerializer(read_only=True)
    reviewer       = UserMinimalSerializer(read_only=True)
    comments_count = serializers.IntegerField()

    class Meta:
        model  = Task
        fields = [
            'id', 'board', 'title', 'description',
            'status', 'priority', 'assignee',
            'reviewer', 'due_date', 'comments_count'
        ]

class BoardDetailSerializer(serializers.ModelSerializer):
    owner   = UserMinimalSerializer(read_only=True)
    members = UserMinimalSerializer(many=True, read_only=True)
    tasks   = TaskListSerializer(many=True, read_only=True)

    class Meta:
        model  = Board
        fields = ['id', 'title', 'owner', 'members', 'tasks']

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
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
            'id', 'board', 'title', 'description',
            'status', 'priority',
            'assignee_id', 'reviewer_id',
            'due_date'
        ]

    def create(self, validated_data):
        request_user = self.context['request'].user

        return Task.objects.create(
            created_by=request_user,
            **validated_data
        )
    
        # return super().create(validated_data)

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        return obj.author.get_full_name() or obj.author.username


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comment
        fields = ['id', 'content']

    def create(self, validated_data):
        task   = self.context['task']
        author = self.context['request'].user
        return Comment.objects.create(
            task=task, author=author, content=validated_data['content']
        )