from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from user_auth_app.models import UserProfile
from .serializers import (
    UserProfileSerializer,
    RegistrationSerializer,
    LoginSerializer
    )

class UserProfileList(generics.ListCreateAPIView):
    """
    API endpoint to list all user profiles or create a new profile.
    GET:  returns a list of all UserProfile instances.
    POST: creates a new UserProfile (requires authentication).
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a specific user profile.
    GET:    retrieve a UserProfile by its ID.
    PUT/PATCH: update a UserProfile (requires authentication).
    DELETE: remove a UserProfile (requires authentication).
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class RegistrationView(APIView):
    """
    API endpoint for user registration.
    POST: registers a new user account and returns an authentication token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate input, create a new user, generate token, and respond.
        """
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account)
            data = {
                'token': token.key,
                'fullname': saved_account.username,
                'email': saved_account.email,
                'user_id': saved_account.id,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomLoginView(ObtainAuthToken):
    """
    API endpoint for user login using token authentication.
    POST: validates credentials, returns token and basic user info.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        Validate credentials with LoginSerializer, create/get token, and respond.
        """
        serializer = self.serializer_class(data=request.data, context={'request': request})

        data = {}
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key,
                'fullname': user.username,
                'email': user.email,
                'user_id': user.id
            }
            return Response(data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)