from email import charset
from operator import mod
from uuid import UUID
from django.test import tag
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes as _permission_classes
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from generics import permissions
from generics import exceptions
from generics import mixins
from . import serializers
from . import models
from . import utils
from . import functions
import datetime
import pytz
from django.db.models import F
from .import configurations
from projects import models as prg_model
from django.apps import apps
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
import jwt

from rest_framework_simplejwt.tokens import RefreshToken
import time
import datetime
from dateutil.relativedelta import relativedelta


class LogoutView(APIView):
    """
    API to logout from an user account.
    """

    serializer_class = serializers.LogoutRequestSerializer

    def post(self, request):
        """Logout an user account.
        Args:
            request (Request): request contains the refresh token.

        Returns:
            Response: status of the logout API.
        """
        serializer = serializers.LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh: str = serializer.validated_data.get('refresh')
        if utils.blacklist_token(refresh=refresh):
            return Response(data={'detail': 'Logout success.'},status=status.HTTP_200_OK)
        else:
            return Response(data={'detail': 'Token is invalid or expired'},status=status.HTTP_401_UNAUTHORIZED)

class ProfileInfoView(APIView):
    """
    API to update user profile. If if_staff in response is true, then its a superuser
    """
    permission_classes = [IsAuthenticated, ]

    @extend_schema(
        request   = None,
        responses = {200: serializers.UserInfoModelSerializer(many=True)}
    )    
    def get(self, request):
        result = utils.get_user_info(request.user.id)
        if not result:
            return Response(data={"detail": "User account does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"detail": result}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    """
    API to send the password reset link to the user's email.
    """
    permission_classes = [AllowAny, ]
    @extend_schema(
        request  = serializers.EmailSerializer,
        responses = dict
    )
    def post(self, request) -> Response:
        """
        Sends password reset email to the user.

        ------
        Params
        ------
        \temail : Email of the user whose password to be resetted.\n
        """
        serializer   = serializers.EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email : str  = serializer.validated_data.get('email', None)
        result: bool = utils.password_reset_email(email=email)
        if not result:
            return Response(data={"detail": "Password reset failed."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"detail": "Password reset email sent."}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    """
    API to create a new password from the password reset link.
    """
    permission_classes = [AllowAny, ]
    
    @extend_schema(
        request   = serializers.KeyPasswordSerializer,
        responses = dict
    )
    def post(self, request) -> Response:
        """
        Resets a new password through the forgot-password link.
        ------
        Params
        ------
        \tkey      : key is the auth key retrieved from the reset-password email.\n
        \tpassword : password is the new password to be set to the user account.
        """
        serializer = serializers.KeyPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key     : str = serializer.validated_data.get('key', None)
        password: str = serializer.validated_data.get('password', None)

        result: bool = utils.password_reset_done(key=key, password=password)
        if not result:
            return Response(data={"detail": "Invalid password reset link. Password reset failed."}, status=status.HTTP_403_FORBIDDEN)
        return Response(data={"detail": "Password reset success."}, status=status.HTTP_200_OK)

class OrganisationCRUDView(mixins.PermissionsPerMethodMixin,viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete organization
    """

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.OrganizationResponseSerializer
    queryset            = models.Organization.objects.none()
    
    def get_queryset(self):
        org_role = models.Role.objects.filter(user=self.request.user).first()
        if org_role.organization is None:
            return models.Organization.objects.all().order_by('-created_at')
        else:
            return models.Organization.objects.filter(id=org_role.organization.id).order_by('-created_at')

    @extend_schema(
        tags=['Common for Roadmap and Quiver'],
        request   = serializers.OrganisationCreateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        })
    @_permission_classes((permissions.IsSuperUser,))
    def create(self, request, *args, **kwargs):
        """
        Creates an account for Organization Admin

        Params:
        -------
        \tfirst_name         : first_name of the user.
        \tlast_name          : last_name of the user.
        \temail              : email of the user.
        \tname               : name of the organization.
        \tphone              : phone number of the user.
        Params for quiver:
        ------------------
        \tfirst_name         : first_name of the user.
        \tlast_name          : last_name of the user.
        \temail              : email of the user.
        \taccess_list        : app access List.
        \tproject_list       : UUID of projects.
        """
        serializer = serializers.OrganisationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        first_name  : str = serializer.validated_data.get('first_name', None)
        last_name   : str = serializer.validated_data.get('last_name', None)
        email       : str = serializer.validated_data.get('email', None)
        name        : str = serializer.validated_data.get('name', None)
        phone       : str = serializer.validated_data.get('phone', None)
       
        # project_list  : str = serializer.validated_data.get('project_list', None)
        access_list   : str = serializer.validated_data.get('access_list', [])
        project_creationlist : str = serializer.validated_data.get('project_creation_list', None)
        try:
            utils.create_organization_admin(creator=request.user, first_name=first_name,last_name=last_name, email=email, name=name, phone=phone,access_list=access_list,project_creationlist=project_creationlist)
        except exceptions.ExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={'detail': 'Organization admin created successfully'}, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Quiver'],
        request   = None,
        responses = {201: serializers.OrganizationResponseSerializer})
    @_permission_classes((permissions.IsAuthenticated,))
    def list(self, request):
        """
        Lists all organizations
        
        @TODO: Add pagination
        """
        querset     = self.get_queryset()
        serializer  = serializers.ListOrganizations(querset, many=bool)
        return Response(serializer.data)

    @extend_schema(
        tags=['Quiver'],
        request   = serializers.OrganizationUpdateSerializer,
        responses = {201: serializers.OrganizationResponseSerializer})
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def update(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except models.Organization.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if (not request.user.is_staff) and (not models.Role.objects.filter(user__id=request.user.id,organization__id=pk).exists()):
            return Response(data={"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.OrganizationUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        tags=['Quiver'],
        responses = {
            202: dict,
            404: dict})
    @_permission_classes((permissions.IsSuperUser,))
    def destroy(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except models.Organization.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)

        # finding the users in Hospital Group
        organization = models.Role.objects.filter(organization__id=pk)
        user_list = [i.user for i in organization]

        models.User.objects.filter(username__in=user_list).delete()
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        tags=['Quiver'],
        responses = {
            200: serializers.OrganizationResponseSerializer,
            404: dict, 403: dict})
    @_permission_classes((permissions.IsAuthenticated,))
    def retrieve(self, request, pk=None):
        org_role = models.Role.objects.get(organization__id=pk,user__id=request.user.id)
        if str(org_role.organization.id) != pk:
            return Response(data={"detail": "You are not part of this organization"}, status=status.HTTP_403_FORBIDDEN)

        querset = get_object_or_404(self.get_queryset(), pk=pk)
        serializer  = self.serializer_class(querset)
        return Response(serializer.data)

class ChangePasswordView(APIView):
    """
    API to change password.
    """
    @extend_schema(
        request   = serializers.ChangePasswordSerializer,
        responses = {
            200: dict,
            400: dict
        }
    )
    def post(self, request):
        """
        Replaces the current password with new password

        Params:
        -------
        old_password: str
            old_password is the current password of the user account.
        new_password: str
            new_password is the new password to be set to the user account.
        """

        serializer = serializers.ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password: str = serializer.validated_data.get('old_password', None)
        new_password: str = serializer.validated_data.get('new_password', None)

        try:
            result = utils.change_password(
                user_id=request.user.id, email=request.user.username, old_password=old_password, new_password=new_password)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        if not result:
            return Response(data={"detail": "Current Password does not match."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'detail': "Password is updated."}, status=status.HTTP_200_OK)

class UserView(mixins.PermissionsPerMethodMixin,viewsets.ViewSet):

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.UserInfoModelSerializer
    queryset            = models.User.objects.none()

    def get_queryset(self,pk):
        if models.Role.objects.get(user = self.request.user).role == models.Role.RoleName.superadmin:
           user_list = models.Role.objects.filter(role__in=[models.Role.RoleName.admin,models.Role.RoleName.user]).values_list('user',flat=True)
           access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')   
           return models.User.objects.filter(id__in=access_list).exclude(id=self.request.user.id).order_by('-date_joined')
        organization = models.Role.objects.filter(user=self.request.user).first()
        user_list = models.Role.objects.filter(organization=organization.organization,role__in=[models.Role.RoleName.admin,models.Role.RoleName.user]).values_list('user',flat=True)
        access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')
        return models.User.objects.filter(id__in=access_list).exclude(id=self.request.user.id).order_by('-date_joined')

    @extend_schema(
        tags=['Quiver'],
        request   = None,
        parameters=[

      OpenApiParameter(name='search', required=False, type=str,location=OpenApiParameter.QUERY),
      OpenApiParameter(name='field', required=False, type=str,location=OpenApiParameter.QUERY),

           ],
        responses = {201: serializers.UserInfoModelSerializer})
    @_permission_classes((permissions.IsAuthenticated,))
    def retrieve(self, request, pk=None):
        """
        Lists all Users
        @TODO: Add pagination
        """
        querset     = self.get_queryset(pk)
        if "search" in request.query_params:
                 search = request.query_params.get('search')
                 querset=querset.filter(first_name__icontains=search)
                 if "field" in request.query_params:
                    field = request.query_params.get('field')
                    querset= querset.order_by(field)
        elif "field" in request.query_params:
                field = request.query_params.get('field')
                querset= querset.order_by(field)
        serializer  = self.serializer_class(querset, many=bool)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Quiver'],
        request   = None,
        responses = {200: dict})
    @action(detail=False)
    def options(self, request):
        """Necessary data for user creation"""

        if models.Role.objects.get(user = self.request.user).organization == None:
            organizations = models.Organization.objects.all()
        else:
            organizations = models.Organization.objects.filter(id=utils.get_current_orgainzation(request.user.id).id)
        result= {
            "roles": [ {"code":choice, "name":value} for choice, value in models.Role.RoleName.choices ],
            "organizations": serializers.OrganizationNameListSerializer(organizations, many=True).data,
        }
        return Response(data=result, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Common for Roadmap and Quiver'],
        request   = serializers.CreateUsersSerializer,
        responses = {200: dict, 400: dict, 403: dict, 409: dict})
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def create(self,request):
        """Creating users for organizations
         - API allowed by super admins or organizational admins only
         - If an organizational admin try to create a user in another organization,
            - Returns 403\n
        Payload for creating superadmin 
        ---------------------------------
        \tfirst_name     : first_name of user.\n
        \tlast_name      : last_name of users.\n
        \temail          : email of users.\n
        \taccess_list        : app access List.
        """
        # if request.user.is_staff:
        serializer = serializers.CreateUsersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        first_name  : str = serializer.validated_data.get('first_name', None)
        last_name   : str = serializer.validated_data.get('last_name', None)
        email       : str = serializer.validated_data.get('email', None)
        phone       : str = serializer.validated_data.get('phone', None)
        role        : str = serializer.validated_data.get('role', None)
        org_id      : str = serializer.validated_data.get('organization', None)
        access_list   : str = serializer.validated_data.get('access_list', [])
        # roadmap_access: str = serializer.validated_data.get('roadmap_access', False)
        # pattern_access: str = serializer.validated_data.get('pattern_access', False)
        # context_access   : str = serializer.validated_data.get('context_access', False)
        # blueprint_access : str = serializer.validated_data.get('blueprint_access', False)
        try:
            current_role = models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if not ((current_role.role == models.Role.RoleName.superadmin) or (current_role.role == models.Role.RoleName.admin)):
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (org_id == None) and (current_role.role == models.Role.RoleName.admin):
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if current_role.role == models.Role.RoleName.superadmin:
            organization = models.Organization.objects.filter(id=org_id).first()
        elif current_role.role == models.Role.RoleName.admin:
            organization = current_role.organization
            if organization.id != org_id:
                return Response(data={"detail": "You are not part of this organization"}, status=status.HTTP_403_FORBIDDEN)
            if organization is None:
                return Response(data={"detail": "You are not part of any organization"}, status=status.HTTP_403_FORBIDDEN)
        else:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)
        if org_id == None and role != models.Role.RoleName.superadmin:
              return Response(data={"detail": "Please enter a valid organization."}, status=status.HTTP_403_FORBIDDEN)
        try:
            utils.create_user(first_name, last_name, organization, email.lower(), phone, role,access_list)
            # local_dt = timezone.localtime(datetime.datetime.now(), pytz.timezone(settings.CENTRAL_TIME_ZONE))
            # utils.user_activity_log(user=request.user,name='user created',arguments={'name':email, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={'detail': f'{role} created successfully'}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request   = serializers.UpdateOrganizationUserSerializer,
        responses = {200: dict, 400: dict, 403: dict, 409: dict})
    def update(self, request, pk):
        """Updating a user_id
         - if SuperAdmin:
            - Update role, org, fname, lname, phone
         - else if OrganizationAdmin:
            - Check if org_id and current_org_id match
            - Check if user_id is in current organization
            - Cannot modify other organizations
            - Update role, fname, lname, phone
         - else:
            - Check if org_id and current_org_id match
            - Check modify other users
            - Cannot change organization, role
            - Update fname, lname, phone
        
        """
        serializer = serializers.UpdateOrganizationUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id         : str = serializer.validated_data.get('organization', None)
        role           : str = serializer.validated_data.get('role', None)
        first_name     : str = serializer.validated_data.get('first_name', None)
        last_name      : str = serializer.validated_data.get('last_name', None)
        phone          : str = serializer.validated_data.get('phone', None)
        email          : str = serializer.validated_data.get('email', None)
        access_list   : str = serializer.validated_data.get('access_list', [])
        # roadmap_access   : str = serializer.validated_data.get('roadmap_access', False)
        # pattern_access   : str = serializer.validated_data.get('pattern_access', False)
        # context_access   : str = serializer.validated_data.get('context_access', False)
        # blueprint_access : str = serializer.validated_data.get('blueprint_access', False)
        current = utils.get_current_org_role(request.user.id)
        requested = utils.get_current_org_role(pk)
        try:
            user = models.User.objects.get(id=pk)
        except:
            return Response(data={"detail": "Requested user does not exists"}, status=status.HTTP_404_NOT_FOUND)
        if org_id == None: organization = None
        else: organization = models.Organization.objects.get(id=org_id)
        if (role != 'admin') and (requested.role=='admin') and len(requested.organization.role_set.filter(role='admin'))<=1:
            return Response(data={"detail": "organization must contain atleast one admin"}, status=status.HTTP_400_BAD_REQUEST)
        if current.role == models.Role.RoleName.superadmin:
            
            result=utils.update_user(user, first_name, last_name, phone, email)
            if result:
                utils.update_user_org_role(user,organization,role,access_list)       
                return Response(data={"detail": "User details has been updated."}, status=status.HTTP_200_OK)
            return Response(data={"detail": "Email already exists."}, status=status.HTTP_404_NOT_FOUND)
        
        elif current.role == models.Role.RoleName.admin:
            if organization is None:
                # if organization is None, it means thats a enterprise user. Specify organization_id in request
                return Response(data={"detail": "You do not have the permission to modify enterprise users"}, status=status.HTTP_403_FORBIDDEN)
            if current.organization.id != org_id:
                return Response(data={"detail": "You do not have permission to modify this organization"}, status=status.HTTP_403_FORBIDDEN)
            if str(utils.get_current_org_role(pk).organization.id) != str(current.organization.id):
                return Response(data={"detail": "User does not belong to your organization"}, status=status.HTTP_400_BAD_REQUEST)
            if (role != 'admin') and (requested.role=='admin') and len(requested.organization.role_set.filter(role='admin'))<=1:
                return Response(data={"detail": "organization must contain atleast one admin"}, status=status.HTTP_400_BAD_REQUEST)
            result=utils.update_user(user, first_name, last_name, phone, email)
            if result:
                utils.update_user_org_role(user,organization,role,access_list)
                # utils.user_activity_log(user=request.user,name='user updated',arguments={'name':user.username, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})       
                return Response(data={"detail": "User details has been updated."}, status=status.HTTP_200_OK)
            return Response(data={"detail": "Email already exists."}, status=status.HTTP_404_NOT_FOUND)
            # local_dt = timezone.localtime(datetime.datetime.now(), pytz.timezone(settings.CENTRAL_TIME_ZONE))
            

        else:
            if pk != request.user.id:
                return Response(data={"detail": "You do not have permission to modify another users"}, status=status.HTTP_403_FORBIDDEN)            
            if str(current.organization.id) != org_id:
                return Response(data={"detail": "You do not have permission to change your organization"}, status=status.HTTP_403_FORBIDDEN)
            if current.role != role:
                return Response(data={"detail": "You do not have permission to change your role"}, status=status.HTTP_403_FORBIDDEN)

            utils.update_user(user, first_name, last_name, phone)
            # local_dt = timezone.localtime(datetime.datetime.now(), pytz.timezone(settings.CENTRAL_TIME_ZONE))
            # utils.user_activity_log(user=request.user,name='user updated',arguments={'name':user.username, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})
            return Response(data={"detail": "User details has been updated."}, status=status.HTTP_200_OK)
    
    @extend_schema(responses = {202: dict,400: dict, 403: dict, 404: dict})
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def destroy(self, request, pk):
        if pk==request.user.id: return Response(data={"detail": "You cannot delete yourself"}, status=status.HTTP_403_FORBIDDEN)
        requested = utils.get_current_org_role(pk)
        current   = utils.get_current_org_role(request.user.id)
        user_obj=models.User.objects.filter(id=pk).first()
        if user_obj is None:
            return Response(data={"detail": "User details not found"}, status=status.HTTP_404_NOT_FOUND)
        if (requested.role=='admin') and len(requested.organization.role_set.filter(role='admin'))<=1:
            org_id = models.Role.objects.get(user__id=pk)
            utils.delete_user(pk)
            org = models.Organization.objects.get(id=org_id.organization.id)
            org.delete()
            return Response(data={"detail": "Admin and organization got deleted"}, status=status.HTTP_202_ACCEPTED)
        if (current.role == models.Role.RoleName.admin) and (requested.organization != current.organization):
            return Response(data={"detail": "User does not belong to your organization"}, status=status.HTTP_400_BAD_REQUEST)
        # try:
        #     self.get_queryset().get(pk=pk)
        # except models.User.DoesNotExist:
        #     return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        user = functions.get_user_by_id(id=pk)
        # local_dt = timezone.localtime(datetime.datetime.now().replace(tzinfo=pytz.UTC), pytz.timezone(settings.CENTRAL_TIME_ZONE))
        # utils.user_activity_log(user=request.user,name='user deleted',arguments={'name':user.username, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})
        utils.delete_user(pk)
        return Response(data={"status": "User deleted successfully"}, status=status.HTTP_202_ACCEPTED)


class UserFeedbackView(APIView):
    """
    API for list create update and delte roadmap.
    """

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.FeedbackSerializer

    def get(self,request):
        current   = utils.get_current_org_role(request.user.id)
        if current.role == models.Role.RoleName.superadmin:
            feedbacks = models.UserFeedback.objects.all().order_by('-created_at')
        else:
            feedbacks = models.UserFeedback.objects.filter(is_visible=True).order_by('-created_at')
        return Response(data=serializers.FeedbackSerializer(feedbacks, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = serializers.FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject  : str = serializer.validated_data.get('subject', None)
        description : str = serializer.validated_data.get('description', None)
        is_visible : str  = serializer.validated_data.get('is_visible', None)
        # project_id  : str = serializer.validated_data.get('project_id', None)
        user_role = utils.get_current_org_role(request.user.id).role
        try:
            feedback = functions.create_feedback(creator=request.user, subject=subject, description=description, is_visible=is_visible)
            utils.user_feedback(user=request.user, subject=subject, body=description, role=user_role)
            org= models.Role.objects.get(user=request.user.id).organization
            utils.user_activity_log(user=request.user,name='feedback send',arguments={'name':subject, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S'),"type":"feedback"},org_id=org,project_id=None)
        except exceptions.ExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={'detail': 'Feedback created successfully'}, status=status.HTTP_201_CREATED)

class UserFeedbackActionView(APIView):

    def get(self,request,pk):

        try:
            feedbacks = models.UserFeedback.objects.filter(id=pk)
        except (models.UserFeedback.DoesNotExist,django.core.exceptions.ValidationError) as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data=serializers.FeedbackSerializer(feedbacks, many=True, context={'id': pk}).data, status=status.HTTP_200_OK)

    # def post(self, request,pk):

    #     try:
    #         feedbacks = models.UserFeedback.objects.filter(id=pk).first()
    #     except (models.UserFeedback.DoesNotExist,django.core.exceptions.ValidationError) as error:
    #         return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

    #     try:
    #         feedback = functions.create_feedback(creator=request.user, subject=subject, description=description, is_visible=is_visible)
    #     except exceptions.ExistsError as error:
    #         return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
    #     except exceptions.NotExistsError as error:
    #         return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

    #     return Response(data={'detail': 'Feedback created successfully'}, status=status.HTTP_201_CREATED)


    def delete(self,request,pk):

        try:
            feedback = models.UserFeedback.objects.get(id=pk)
        except models.RoadMaps.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        feedback.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)

class NotificationView(APIView):
    def get(self,request):
        arguments= utils.activity_notifications_to_collaborator()
        current   = utils.get_current_org_role(request.user.id)
        org_id = self.request.query_params.get('organization',None)
        # local_dt = timezone.localtime(roadmap_feature.created_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
        if current.role == 'superadmin': 
            org_id=None
        if org_id:
            organization = models.Organization.objects.filter(id=org_id).first()
        else:
            organization=None
        final_data=[]
        datas=[]    
        for arg in arguments:  
            if current.role == 'superadmin':         
                for feature in arg['argument']['features']:
                    if (request.user) !=(feature.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'feature added',
                                      'time'        :utils.time_conversion(feature.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :feature.name,
                                      'user'        :feature.created_by.first_name
                            })
                for feature in arg['argument']['updated_features']:
                    if (request.user) !=(feature.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'feature updated',
                                      'time'        :utils.time_conversion(feature.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :feature.name,
                                      'user'        :feature.created_by.first_name
                            })
                for roadmap in arg['argument']['roadmaps']:
                    if (request.user) !=(roadmap.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'roadmap added',
                                      'time'        :utils.time_conversion(roadmap.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :roadmap.name,
                                      'user'        :roadmap.created_by.first_name
                            })
                for roadmap in arg['argument']['updated_roadmaps']:
                    if (request.user) !=(roadmap.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'roadmap updated',
                                      'time'        :utils.time_conversion(roadmap.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :roadmap.name,
                                      'user'        :roadmap.created_by.first_name,
                            })
                for product in arg['argument']['products']:
                    if (request.user) !=(product.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'product added',
                                      'time'        :utils.time_conversion(product.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :product.project.name,
                                      'user'        :product.created_by.first_name
                            })
                for product in arg['argument']['features']:
                    if (request.user) !=(product.created_by):
                        datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'product updated',
                                      'time'        :utils.time_conversion(product.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :product.name,
                                      'user'        :product.created_by.first_name
                            })



                # data={
                #     'new_features': [{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name,'roadmap':k.roadmap.name, 'project':k.roadmap.project.name} for k in arg['argument']['features']],
                #     'updated_features':[{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name, 'roadmap':k.roadmap.name, 'project':k.roadmap.project.name} for k in arg['argument']['updated_features']],
                #     'new_roadmaps':[{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name, 'project':k.project.name} for k in arg['argument']['roadmaps']],
                #     'updated_roadmaps':[{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name, 'project':k.project.name} for k in arg['argument']['updated_roadmaps']],
                #     'new_products':[{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name} for k in arg['argument']['products']],
                #     'updated_products':[{'user':k.created_by.first_name, 'time':k.updated_at.strftime('%d-%m-%Y %H:%M:%S'),'name':k.name} for k in arg['argument']['updated_products']],
                # }
                # final_data.append({'organization':arg['argument']['organization'].name, 'data':data})
            else:
                if arg['argument']['organization']==organization:
                    for feature in arg['argument']['features']:
                        if (request.user) !=(feature.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                      'action'      :'feature added',
                                      'time'        :utils.time_conversion(feature.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                      'name'        :feature.name,
                                      'user'        :feature.created_by.first_name
                            })
                    for feature in arg['argument']['updated_features']:
                        if (request.user) !=(feature.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                          'action'      :'feature updated',
                                          'time'        :utils.time_conversion(feature.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                          'name'        :feature.name,
                                          'user'        :feature.created_by.first_name
                                })
                    for roadmap in arg['argument']['roadmaps']:
                        if (request.user) !=(roadmap.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                          'action'      :'roadmap added',
                                          'time'        :utils.time_conversion(roadmap.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                          'name'        :roadmap.name,
                                          'user'        :roadmap.created_by.first_name
                                })
                    for roadmap in arg['argument']['updated_roadmaps']:
                        if (request.user) !=(roadmap.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                          'action'      :'roadmap updated',
                                          'time'        :utils.time_conversion(roadmap.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                          'name'        :roadmap.name,
                                          'user'        :roadmap.created_by.first_name,
                                })
                    for product in arg['argument']['products']:
                        if (request.user) !=(product.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                          'action'      :'product added',
                                          'time'        :utils.time_conversion(product.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                          'name'        :product.project.name,
                                          'user'        :product.created_by.first_name
                                })
                    for product in arg['argument']['updated_products']:
                        if (request.user) !=(product.created_by):
                            datas.append({'organization':arg['argument']['organization'].name,
                                          'action'      :'product updated',
                                          'time'        :utils.time_conversion(product.updated_at).strftime('%d-%m-%Y %H:%M:%S'),
                                          'name'        :product.project.name,
                                          'user'        :product.created_by.first_name
                                })

        return Response(data=sorted(datas,key=lambda x : datetime.datetime.strptime(x['time'],"%d-%m-%Y %H:%M:%S")), status=status.HTTP_200_OK)

class ActivityView(viewsets.ViewSet):

    @extend_schema(
        
        request   = serializers.UserActivitySerializer,
          parameters=[

            OpenApiParameter(name='product', required=False, type=UUID,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='start_date', required=False, type=datetime.date,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='org_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

            ],
        responses = {
            201: dict,
            404: dict,
            409: dict
        })
    def list(self,request):
        
        current_org   = utils.get_current_orgainzation(request.user.id)
        orgg_id = self.request.query_params.get('org_id',None)
        product_id = self.request.query_params.get('product',None)
        start_date = self.request.query_params.get('start_date',None)
        
        if product_id:
            
            activities = models.Activity.objects.filter(projects=product_id, arguments__date=start_date).exclude(user=request.user).order_by('-created_at')[:10]
        else:
            if current_org is None:
                activ = models.Activity.objects.filter(arguments__date=start_date).exclude(user=request.user)
                if orgg_id:
                    print(orgg_id)
                    activities=activ.filter(organization_id=orgg_id).order_by('-created_at')[:10]
                    
                else:
                    activities=activ.order_by('-created_at')[:10]

                # activities = models.Activity.objects.filter(organization_id=orgg_id,arguments__date=start_date)
            else:
                activities = models.Activity.objects.filter(organization_id=current_org,arguments__date=start_date).exclude(user=request.user).order_by('-created_at')[:10]

        final_data=[]
        serializer = serializers.UserActivitySerializer(activities,many=True)
        # for activity in activities:
        #     final_data.append({'user':activity.user.username,'actions':activity.name,'activity_details':activity.arguments})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
class AdminListUpdate(APIView):
    permission_classes  = [permissions.IsSuperUser, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.UpdateAdminsSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        })
    def post(self,request,pk):
        """
        API to update admin details\n
        Params for superadmin
        ----------------------
        \tfirst_name     : first_name of user.\n
        \tlast_name      : last_name of users.\n
        \temail          : email of users.\n
  
        
        Params for org admin\n
        \tfirst_name     : first_name of user.\n
        \tlast_name      : last_name of users.\n
        \tname           : organization name.\n
        \temail          : email of users.\n
        \tphone          : phone number of user (optional).\n
        \torg_id         : UUID or organization.\n
        \taccess_list        : app access List.
        \tproject_list   : UUID of projects.\n
        """
        serializer = serializers.UpdateAdminsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org_id         : str = serializer.validated_data.get('organization', None)
        name           : str = serializer.validated_data.get('name', None)
        first_name     : str = serializer.validated_data.get('first_name', None)
        last_name      : str = serializer.validated_data.get('last_name', None)
        phone          : str = serializer.validated_data.get('phone', None)
        email          : str = serializer.validated_data.get('email', False)
        # roadmap_access : str = serializer.validated_data.get('roadmap_access', False)
        # pattern_access : str = serializer.validated_data.get('pattern_access', False)
        # context_access : str = serializer.validated_data.get('context_access', False)
        # blueprint_access : str = serializer.validated_data.get('blueprint_access', False)
        access_list   : str = serializer.validated_data.get('access_list', [])
        project_list   : str = serializer.validated_data.get('project_list', [])
        project_creationlist : str = serializer.validated_data.get('project_creation_list', [])
        try:
            utils.admin_user_update(org_id,name,first_name,last_name,phone,email,access_list,project_list,pk,request.user,project_creationlist)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={'detail': 'Admin details updated successfully'}, status=status.HTTP_202_ACCEPTED)

class UsersAppAccessList(APIView):
    permission_classes  = [permissions.IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = None,
    responses = {
            200: dict,
            404: dict,
        })
    
    def get(self, request):
        
        result = models.Role.objects.filter(user=request.user).first()
        total_count = 0
        if result.organization is None:

      
            active_app=models.UserAppMappping.objects.filter(user=request.user)
            app_list=active_app.filter(status=1).values_list('app_id',flat=True)
            active_app=app_list.filter().values('app_id',app_name=F('app_id__app_name'),app_type=F('app_id__app_type'),description=F('app_id__description'))
            user_app_object=models.UserAppMappping.objects.all().exclude(user=request.user)
            inactive_app =  models.QuiverApps.objects.exclude(id__in=app_list)
            inactive_app=serializers.InactiveAppSerializer(inactive_app, many=True,context={'user':request.user}).data
            
            for i in  active_app:
                user_list=user_app_object.filter(app_id=i['app_id']).values(first_name=F('user_id__first_name'),last_name=F('user_id__last_name')).order_by('-created_at')[:3]

                if i["app_name"] in configurations.NOTIFICATION_DICT:
                    
                    model = apps.get_model(configurations.APP_DICT[i["app_name"]],configurations.NOTIFICATION_DICT[i["app_name"]])
                    if model:
                        comt_hist = model.objects.filter(action_type__in=["comment","reply"],org_user=request.user,higlight_status="unseen")
        
                        total_count = len(comt_hist)
                      

                i.update({"user_list":user_list,"notification":total_count})
                # inactive_app=inactive_app.exclude(id=i['app_id'])

            
        else:
            active_app=models.UserAppMappping.objects.filter(user=request.user,status=1).values('app_id','app_id',app_name=F('app_id__app_name'),app_type=F('app_id__app_type'),description=F('app_id__description'))
            org_users=models.Role.objects.filter(organization=result.organization).values('user_id')
            user_app_object=models.UserAppMappping.objects.filter(user_id__in=org_users).exclude(user=request.user)
            app_list=models.UserAppMappping.objects.filter(user=request.user,status=1).values_list('app_id',flat=True)
            inactive_app =  models.QuiverApps.objects.exclude(id__in=app_list)
            inactive_app=serializers.InactiveAppSerializer(inactive_app, many=True,context={'user':request.user}).data
            for i in  active_app:
                user_list=user_app_object.filter(app_id=i['app_id']).values(first_name=F('user_id__first_name'),last_name=F('user_id__last_name')).order_by('-created_at')[:3]
                if i["app_name"] in configurations.NOTIFICATION_DICT:
                    
                    model = apps.get_model(configurations.APP_DICT[i["app_name"]],configurations.NOTIFICATION_DICT[i["app_name"]])
                    if model:
                        comt_hist = model.objects.filter(action_type__in=["comment","reply"],org_user=request.user,higlight_status="unseen")
        
                        total_count = len(comt_hist)

                i.update({"user_list":user_list,"notification":total_count})
                # inactive_app=inactive_app.exclude(id=i['app_id'])
        return Response(data={"active_app": active_app ,"inactive_app":inactive_app}, status=status.HTTP_200_OK)
        

      
        
class ListAdminView(APIView):
    @extend_schema(
        tags=['Quiver'],
    request   = None,
    parameters=[

      OpenApiParameter(name='search', required=False, type=str,location=OpenApiParameter.QUERY),
      OpenApiParameter(name='field', required=False, type=str,location=OpenApiParameter.QUERY),

           ],
    responses = {
            200: dict,
            404: dict,
        })
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def get(self,request):
        
        current   = utils.get_current_org_role(request.user.id)
        if current.role == 'superadmin':
            admin_user= models.Role.objects.filter(role='superadmin')|models.Role.objects.filter(role = 'admin').order_by('-created_at')
            
            if "search" in request.query_params:
                 search = request.query_params.get('search')
                 admin_user=admin_user.filter(user__first_name__icontains=search)
                 if "field" in request.query_params:
                    field = request.query_params.get('field')
                    admin_user= admin_user.order_by(field)
            elif "field" in request.query_params:
                field = request.query_params.get('field')
                admin_user= admin_user.order_by(field)
               
            serializer  = serializers.AdminListModelSerializer(admin_user.exclude(user=request.user), many=bool)
            return Response(serializer.data)
        else:
            admin_user= models.Role.objects.filter(role='user',organization=current.organization)|models.Role.objects.filter(role = 'admin',organization=current.organization).order_by('-created_at')
            if "search" in request.query_params:
                 search = request.query_params.get('search')
                 admin_user=admin_user.filter(user__first_name__icontains=search)
                 if "field" in request.query_params:
                    field = request.query_params.get('field')
                    admin_user= admin_user.order_by(field)
            elif "field" in request.query_params:
                    field = request.query_params.get('field')
                    admin_user= admin_user.order_by(field)
            serializer  = serializers.AdminListModelSerializer(admin_user.order_by('-created_at').exclude(user=request.user), many=bool)
            return Response(serializer.data)


class UpdateUserProfile(APIView):

    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.UserprofileUpadate,
    responses = {

            200: dict,
            404: dict,
        })

    def put(self,request,pk):
        serializer_class    = serializers.UserprofileUpadate(data=request.data)
        serializer_class.is_valid(raise_exception=True)
        first_name     : str = serializer_class.validated_data.get('first_name', None)
        last_name      : str = serializer_class.validated_data.get('last_name', None)
        email          : str = serializer_class.validated_data.get('email', None)
        image          : str = serializer_class.validated_data.get('image', None)
        try:
            user = models.User.objects.filter(id=pk).first()
            result =utils.update_user_detail(user, first_name, last_name, email,image)
            return Response(data={"detail": "Requested user updated successfully"}, status=status.HTTP_202_ACCEPTED)
        except:
            return Response(data={"detail": "Requested user does not exists"}, status=status.HTTP_404_NOT_FOUND)
        
class AppList(APIView):
    permission_classes  = [AllowAny, ]
    @extend_schema(
        tags=['Quiver'],
    request   = None,
    responses = {
            200: dict,
            404: dict,
        })
    
    def get(self,request):
        apps =models.QuiverApps.objects.filter(status=1).values()
        return Response(data={"app":apps})         

class organizations(APIView):
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.CreateorganizationsSerializer,
    responses = {

            200: dict,
            404: dict,
        })
    def post(self,request):
        serializer = serializers.CreateorganizationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_name        : str = serializer.validated_data.get('org_name', None)
        image          : str = serializer.validated_data.get('image', None)
        if  models.Organization.objects.filter(name__iexact=org_name):
            return Response(data={"detail": "Organization exists"}, status=status.HTTP_409_CONFLICT)
        try:
            create = models.Organization.objects.create(name=org_name,image=image,created_by_id=request.user.id)
        except:
            return Response(data={"detail": "Organization exists"}, status=status.HTTP_404_NOT_FOUND)
        
        
        return Response(data={"detail": "Organization created"}, status=status.HTTP_202_ACCEPTED)

class AppRequest(APIView):
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    responses = {

            200: dict,
            404: dict,
        })
    def post(self,request,pk):
        try:
            app=models.QuiverApps.objects.filter(id=pk).first()
            app_name   =app.app_name
            first_name =request.user.first_name
            last_name  =request.user.last_name
            email      =request.user.username
            models.UserAppMappping.objects.create(user_id=request.user.id,app_id=app.id,status=2)
            utils.send_app_access_email(app_name,first_name,last_name,email)

        except:
            return Response(data={"detail": "app id invalid"}, status=status.HTTP_404_NOT_FOUND)    

        return Response(data={"detail":"Request has been sent successfully"}, status=status.HTTP_202_ACCEPTED)

class ReplacePassword(APIView):
    """
    API to change password.
    """
    authentication_classes = [] #disables authentication    
    permission_classes = []
    @extend_schema(
        tags=['Quiver'],
        request   = serializers.ReplacePasswordSerializer,
        responses = {
            200: dict,
            400: dict
        }
    )
    def post(self, request):

        serializer = serializers.ReplacePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email: str = serializer.validated_data.get('email', None)
        temp_password: str = serializer.validated_data.get('temp_password', None)
        new_password: str = serializer.validated_data.get('new_password', None)
      
        try:
            user = models.User.objects.filter(username=email).first()
            result  = utils.change_password(
                user_id=user.id, email=email, old_password=temp_password, new_password=new_password)
            st=models.Role.objects.filter(user_id=user.id)
            st.update(status=True)    
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        if not result:
            return Response(data={"detail": "Temporary Password is Incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'detail': "Password is updated."}, status=status.HTTP_200_OK)


    
class AppWiseUserView(viewsets.ViewSet):

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.AppWiseUserSerializer
    queryset            = models.User.objects.none()

    def get_queryset(self,pk,org_id):
        if models.Role.objects.get(user = self.request.user).role == models.Role.RoleName.superadmin:
            
            if org_id is None:
                 user_list = models.Role.objects.filter(role__in=[models.Role.RoleName.admin,models.Role.RoleName.user]).values_list('user',flat=True)
                 access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')   
                 return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')
            user_list = models.Role.objects.filter(organization=org_id ,role__in=[models.Role.RoleName.admin,models.Role.RoleName.user]).values_list('user',flat=True)
            access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')
            return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')
        organization = models.Role.objects.filter(user=self.request.user).first()
        user_list = models.Role.objects.filter(organization=organization.organization,role__in=[models.Role.RoleName.admin,models.Role.RoleName.user]).values_list('user',flat=True)
        access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')
        return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')

    @extend_schema(
        tags=['Quiver'],
        request   = None,
        parameters=[

            OpenApiParameter(name='app_id', required=True, type=int,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='org_id', required=False, type=UUID,location=OpenApiParameter.QUERY),
            

            ],
        responses = {201: serializers.AppWiseUserSerializer})
    @_permission_classes((permissions.IsAuthenticated,))
    def list(self, request):
        """
        Lists all Users
        @TODO: Add pagination
        """
        if "org_id" in request.query_params:
           
           querset     = self.get_queryset(request.query_params["app_id"],request.query_params["org_id"])
           serializer  = self.serializer_class(querset, many=bool)
           return Response(serializer.data)
        else:
            querset     = self.get_queryset(request.query_params["app_id"],None)
            serializer  = self.serializer_class(querset, many=bool)
            return Response(serializer.data)



class OrganizationLogoView(APIView):
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.CreateorganizationsSerializer,
    responses = {

            200: dict,
            404: dict,
        })
    def get(self,request,pk):
        
        try:
            
            org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=pk).first()
            if org_id:
                org_obj = org_id.organization
            if org_obj:
                org_serializer = serializers.OrganizationLogoSerializer(org_obj)
                return Response(data=org_serializer.data, status=status.HTTP_202_ACCEPTED)

            else:
                return Response(data={"detail": "Organization not exists"}, status=status.HTTP_404_NOT_FOUND)

        except:
            return Response(data={"detail": "Organization not exists"}, status=status.HTTP_404_NOT_FOUND)
        
class OrganizationUser(APIView):      
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.OrganizationUserSerializer,
    responses = {

            200: dict,
            404: dict,
        })  
    def post(self, request):
        serializer_class    = serializers.OrganizationUserSerializer(data=request.data)
        serializer_class.is_valid(raise_exception=True)
        access_list   : str =  serializer_class.validated_data.get('access_list', [])
        new_member_user =  serializer_class.validated_data.get('new_member_user', None)
        current_role = models.Role.objects.get(user=request.user)
        role = models.Role.RoleName.user
       
        if current_role.role == models.Role.RoleName.admin:
            organization = current_role.organization
            if organization is None:
                return Response(data={"detail": "You are not part of any organization"}, status=status.HTTP_403_FORBIDDEN)
            try:
                user_id=utils.create_organization_user(new_member_user,organization,role,access_list)
                
            except exceptions.ExistsError as e:
                return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)  
        elif current_role.role == models.Role.RoleName.superadmin:
                    
            organization : str = serializer_class.validated_data.get('organization', None)
            org_name=models.Organization.objects.filter(id=organization).first()
            if organization is None:
                return Response(data={"detail": "select any organization"}, status=status.HTTP_403_FORBIDDEN)
            try:
                user_id=utils.create_organization_user(new_member_user,org_name,role,access_list)
            except exceptions.ExistsError as e:
                return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)          
        else:
            return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)
        user=models.User.objects.filter(id=user_id)
        user_details=serializers.UserlistView(user,many=True)
        return Response(data={'detail': f'{role} created successfully','data':user_details.data}, status=status.HTTP_201_CREATED)   


class OrganizationProjectView(APIView):
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.OrganizationListSerializer,
    responses = {

            200: dict,
            404: dict,
        })
    def get(self,request):
        
        try:
            role = models.Role.objects.get(user = self.request.user).role
            
            if role=='admin' or role=='user':
                
                organization = models.Role.objects.get(user = self.request.user).organization
                org_serializer = serializers.OrganizationListSerializer(organization)
                
                return Response(data=[org_serializer.data], status=status.HTTP_202_ACCEPTED)
            elif role=='superadmin':
                organization = models.Organization.objects.all().order_by('name')
            
                org_serializer = serializers.OrganizationListSerializer(organization,many=True)
                return Response(data=org_serializer.data, status=status.HTTP_202_ACCEPTED)

            else:
                return Response(data={"detail": "Organization not exists"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
           
            return Response(data={"detail": "Organization not exists"}, status=status.HTTP_404_NOT_FOUND)
    
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.ProjectListSerializerData,
    responses = {

            200: dict,
            404: dict,
        })
    def post(self,request):
        
        status = self.request.query_params.get('status','active')
        role = models.Role.objects.get(user = self.request.user).role
        if role=='admin' or role == 'user':
            
            organization = models.Role.objects.get(user = self.request.user).organization
            # user_org_roles = user_models.Role.objects.filter(organization=organization).values_list('user', flat=True)
            project_org=prg_model.ProjectsOrganizationMapping.objects.filter(organization=organization,project__status=status)
            
        elif role=='superadmin':
            org_id = request.data["org_id"]
            if org_id:
                project_org = prg_model.ProjectsOrganizationMapping.objects.filter(organization=org_id)
            else:
                project_org = prg_model.ProjectsOrganizationMapping.objects.all()
        
        serializer = serializers.ProjectListSerializer(project_org,many=True)
    

        return Response(serializer.data)


        
class Invitation_Sent(APIView):      
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.EmailSerializer,
    responses = {

            200: dict,
            404: dict,
        })   
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def post(self, request) -> Response:
        """
        Sends invitation_sent_email to the user.

        ------
        Params
        ------
        \temail : Email of the user whose password to be resetted.\n
        """
        serializer   = serializers.EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email : str  = serializer.validated_data.get('email', None)
        result: bool = utils.invitation_sent_email(email=email)
        if not result:
            return Response(data={"detail": "invitation sent email failed."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"detail": "invitation  email sent."}, status=status.HTTP_200_OK)

class Activate(APIView): 
    authentication_classes = [] #disables authentication    
    permission_classes = []
    @extend_schema(
        tags=['Quiver'],
        request   = serializers.ActivateSerializer,
        responses = {
            200: dict,
            400: dict
        }
    )
    def post(self, request):

        serializer = serializers.ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email: str = serializer.validated_data.get('email', None)
        try:
            user = models.User.objects.filter(username=email).update(is_active=True) 
            
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)    
        return Response(data={"detail": "status updated."}, status=status.HTTP_200_OK)

class Login(APIView):
    
    authentication_classes = [] #disables authentication    
    permission_classes = []
    @extend_schema(
        tags=['Quiver'],
        request   = serializers.LoginSerializer,
        responses = {
            200: dict,
            400: dict
        }
    )
    def post(self,request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        remember_me = serializer.validated_data.get('remember_me')
        response = Response()
        if (username is None) or (password is None):
            return Response(data={"detail":"username and password required"}, status=status.HTTP_404_NOT_FOUND)
        user = models.User.objects.filter(username=username).first()
        if(user is None):
            return Response(data={"detail":"No active account found with the given credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if (not user.check_password(password)):
            return Response(data={"detail":"No active account found with the given credentials"}, status=status.HTTP_401_UNAUTHORIZED)
       
        if not user.is_active:
            return Response(data={"detail":'You have not activated your account yet'}, status=status.HTTP_404_NOT_FOUND)
        
        def get_token(user):
            return RefreshToken.for_user(user) 
        data={}
        refresh = get_token(user)
        
        data['refresh'] = str(refresh)
        a =data['access'] = str(refresh.access_token)
        # print(remember_me)
        if remember_me == True:
            # print(type(refresh))  
            # print(jwt.decode(a, key=settings.SECRET_KEY, algorithms=['HS256', ]))
            token_decode = jwt.decode(a, key=settings.SECRET_KEY, algorithms=['HS256', ])
            # print(token_decode["exp"])
            
            ad = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_decode["exp"]))
            # print("Epoc to dt",ad,type(ad))
            datetime_object = datetime.datetime.strptime(ad, '%Y-%m-%d %H:%M:%S')
            exte_date = datetime_object + relativedelta(months=+3)
            # print(exte_date.timestamp())
            # print("old",token_decode,type(token_decode))
            token_decode.update({"exp": int(exte_date.timestamp())})
            
            # print("New",token_decode,type(token_decode))
            final_enc = jwt.encode(token_decode, key=settings.SECRET_KEY, algorithm='HS256')
            # print("enc",(final_enc))

            # b = final_enc.access_token
            # # access_decode = jwt.decode(b, key=settings.SECRET_KEY, algorithms=['HS256', ])
            # print(b)
            data.update({"access": final_enc})

        
        return Response(data=data)

class AppWiseOrgUserView(viewsets.ViewSet):

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.AppWiseUserSerializer
    queryset            = models.User.objects.none()

    def get_queryset(self,pk,org_id):
        if models.Role.objects.get(user = self.request.user).role == models.Role.RoleName.superadmin:
            
            if org_id is None:
                 user_list = models.Role.objects.filter(role__in=[models.Role.RoleName.user]).values_list('user',flat=True)
                 access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')   
                 return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')
            user_list = models.Role.objects.filter(organization=org_id ,role__in=[models.Role.RoleName.user]).values_list('user',flat=True)
            access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')
            return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')
        organization = models.Role.objects.filter(user=self.request.user).first()
        user_list = models.Role.objects.filter(organization=organization.organization,role__in=[models.Role.RoleName.user]).values_list('user',flat=True)
        access_list = models.UserAppMappping.objects.filter(user_id__in=user_list,app_id=pk).values('user_id')
        return models.User.objects.filter(id__in=access_list,is_active=True).exclude(id=self.request.user.id).order_by('-date_joined')

    @extend_schema(
        tags=['Quiver'],
        request   = None,
        parameters=[

            OpenApiParameter(name='app_id', required=True, type=int,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='org_id', required=False, type=UUID,location=OpenApiParameter.QUERY),
            

            ],
        responses = {201: serializers.AppWiseUserSerializer})
    @_permission_classes((permissions.IsAuthenticated,))
    def list(self, request):
        """
        Lists all Users
        @TODO: Add pagination
        """
        if "org_id" in request.query_params:
           
           querset     = self.get_queryset(request.query_params["app_id"],request.query_params["org_id"])
           serializer  = self.serializer_class(querset, many=bool)
           return Response(serializer.data)
        else:
            querset     = self.get_queryset(request.query_params["app_id"],None)
            serializer  = self.serializer_class(querset, many=bool)
            return Response(serializer.data)
