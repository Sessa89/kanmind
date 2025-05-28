from rest_framework import serializers
from user_auth_app.models import UserProfile
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'location']

class RegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(
        source='username',
        max_length=150,
        help_text="Full name (first and last name)",
        error_messages={
            'required': 'Enter your full name (e.g., Max Mustermann).',
            'blank':    'Enter your full name (e.g., Max Mustermann).'
        },
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='This username is already taken.'
            )
        ]
    )
    email = serializers.EmailField(
        max_length=150,
        error_messages={
            'required': 'Please enter a valid email address.',
            'blank':    'Please enter a valid email address.',
            'invalid':  'Please enter a valid email address.'
        },
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='This email is already taken.'
            )
        ]
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'required': 'Password must be at least 8 characters long.',
            'blank': 'Password must be at least 8 characters long.',
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    repeated_password = serializers.CharField(
        write_only=True,
        error_messages={
            'required': 'Passwords do not match.',
            'blank':    'Passwords do not match.'
        }
    )

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']

    def validate_fullname(self, username):
        if ' ' not in username.strip():
            raise serializers.ValidationError({'error': 'Enter your full name (e.g., Max Mustermann).'})
        
        return username

    def validate(self, data):
        if data['password'] != data.pop('repeated_password'):
            raise serializers.ValidationError({'error': 'The passwords dont match.'})
      
        return data

    def create(self, validated_data):
        account = User(
            username = validated_data['username'],
            email = validated_data['email']
        )
        account.set_password(validated_data['password'])
        account.save()
        
        return account

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                account = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("This account doesnt exist.")
        
            if not account.check_password(password):
                raise serializers.ValidationError("Log in failed. Check your entered email and password.")

        else:
            raise serializers.ValidationError("Email and password are required.")

        attrs['user'] = account
        return attrs