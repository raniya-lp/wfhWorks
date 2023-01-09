import email
from email.policy import default
from rest_framework import serializers
from . import models
from projects.models import ProjectsOrganizationMapping 
from projects import models as prg_model
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

def validate_role(role_value):
    for choice, value in models.Role.RoleName.choices:
        if choice == role_value:
            return choice
    raise serializers.ValidationError("role must be a valid OrganizationalRole")

def validate_organization(value):
    try:
        organization = models.Organization.objects.get(pk=value)
    except models.Organization.DoesNotExist:
        raise serializers.ValidationError("organization must be a valid OrganizationalRole id")
    return organization

def validate_user(value):
    try:
        user = models.User.objects.get(pk=value)
    except models.User.DoesNotExist:
        raise serializers.ValidationError("user must be a valid id")
    return user

class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(min_length=100,max_length=300,required=True)
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=8, max_length=100, required=True)

class UserCreateSerializer(EmailSerializer):
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)
    phone = serializers.IntegerField(
        min_value=1000000000, max_value=9999999999, required=False, allow_null=True, error_messages={'min_value': _('Enter a valid Phone number.'), 'max_value': _('Enter a valid Phone number.')})


class UserInfoModelSerializer(serializers.ModelSerializer):
    def get_image(self, query_set) -> str:
        profile = models.Profile.objects.filter(user=query_set).first()
        if profile is None:
            return profile
        if len(profile.image) == 0:
            return None     
        return profile.image
    def get_org_id(self, queryset) -> dict:
        organization_role = models.Role.objects.filter(user=queryset).first()
        if organization_role is None:
            return organization_role
        if organization_role.organization is None:
            return None 
        return organization_role.organization.id

    def get_organization(self, queryset) -> dict:
        organization_role = models.Role.objects.filter(user=queryset).first()
        if organization_role is None:
            return organization_role
        if organization_role.organization is None:
            return {"role": organization_role.role, "name": None, "id":None},  
        return [{"role": organization_role.role, "name": organization_role.organization.name, "id":organization_role.organization.id}]
    def get_app_access(self,queryset) -> dict:
        app_access=models.UserAppMappping.objects.filter(user=queryset,status=1).values('app_id')
        ls=[]
        for i in app_access:
            ls.append(i['app_id'])
        return ls
    def get_status(self, queryset) -> dict:
        organization_role = models.Role.objects.filter(user=queryset).first()
        if organization_role is None:
            return organization_role
        if organization_role.organization is None:
            return organization_role.status 
        return organization_role.status
    def get_role(self,queryset)-> dict:
        organization_role = models.Role.objects.filter(user=queryset).first()
        if organization_role is None:
            return organization_role  
        return organization_role.role
    email = serializers.CharField(source='username')
    image = serializers.SerializerMethodField(method_name='get_image')
    organization = serializers.SerializerMethodField(method_name='get_organization')
    is_active = serializers.SerializerMethodField(method_name='get_status')
    access_list=serializers.SerializerMethodField(method_name='get_app_access')
    full_name = serializers.CharField(source='get_full_name')
    role = serializers.SerializerMethodField(method_name='get_role')
    org_id = serializers.SerializerMethodField(method_name='get_org_id')
    class Meta:
        model  = models.User
        fields = ['id','first_name', 'last_name','full_name','email','is_active','organization','role','image','access_list','org_id']

class SuperUserListModelSerializer(UserInfoModelSerializer):
    class Meta:
        model  = models.User
        fields = ['id', 'first_name', 'last_name', 'email']

class KeyPasswordSerializer(serializers.Serializer):
    key = serializers.CharField(min_length=100, max_length=300, required=True)
    password = serializers.CharField(min_length=8, max_length=30, required=True)


class UserIDSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(
        min_value=1, max_value=None, required=True)

class UserUpdateSerializer(UserIDSerializer):
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)
    phone = serializers.IntegerField(min_value=1000000000, max_value=9999999999, required=False, allow_null=True, error_messages={'min_value': _('Enter a valid Phone number.'), 'max_value': _('Enter a valid Phone number.')})


class UserIdSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1, max_value=None, required=True)

class OrganizationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.Organization
        fields = '__all__'

class OrganisationCreateSerializer(UserCreateSerializer):
    name  = serializers.CharField(min_length=3, max_length=50, required=True)
    access_list    = serializers.ListField(required=True)
    # project_list         = serializers.ListField(child=serializers.UUIDField(format='hex', required=True))
    project_creation_list         = serializers.ListField(required=False)
class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.Organization
        fields = ['id', 'name']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        min_length=8, max_length=30, required=True)
    new_password = serializers.CharField(
        min_length=8, max_length=30, required=True)

class UserListModelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.User
        fields = ['id', 'first_name', 'last_name', 'username']

class AppWiseUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')
    class Meta:
        model  = models.User
        fields = ['id', 'first_name', 'last_name', 'username','full_name']


class OrganizationNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.Organization
        fields = ['id', 'name']

class CreateUsersSerializer(UserCreateSerializer):     
    role         = serializers.CharField(required=True,validators=[validate_role])
    organization = serializers.UUIDField(required=False,validators=[validate_organization])
    access_list    = serializers.ListField(required=False)

    
class UpdateOrganizationUserSerializer(serializers.Serializer):
    role         = serializers.CharField(required=True,validators=[validate_role])
    organization = serializers.UUIDField(required=False,validators=[validate_organization])
    email = serializers.EmailField(min_length=8, max_length=100, required=True)
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)
    phone = serializers.IntegerField(min_value=1000000000, max_value=9999999999, required=False, allow_null=True, error_messages={'min_value': _('Enter a valid Phone number.'), 'max_value': _('Enter a valid Phone number.')})
    access_list    = serializers.ListField(required=False)  

class UpdateAdminsSerializer(serializers.Serializer):
    organization = serializers.UUIDField(required=False,validators=[validate_organization])
    name = serializers.CharField(min_length=2, max_length=50, required=False)
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)
    email = serializers.EmailField(min_length=1, max_length=50, required=True)
    phone = serializers.IntegerField(min_value=1000000000, max_value=9999999999, required=False, allow_null=True, error_messages={'min_value': _('Enter a valid Phone number.'), 'max_value': _('Enter a valid Phone number.')})
    access_list    = serializers.ListField(required=False)
    project_list         = serializers.ListField(required=False,child=serializers.UUIDField(format='hex', required=False))
    project_creation_list         = serializers.ListField(required=False)

class ListOrganizations(serializers.ModelSerializer):
    def get_contact(self,queryset):
        roles = models.Role.objects.filter(organization=queryset, role='admin')
        user_list = [i.user for i in roles]
        user = models.User.objects.filter(username__in=user_list).order_by('date_joined').first()
        if user:
            return UserListModelSerializer(user).data
        return {}

    contact = serializers.SerializerMethodField(method_name='get_contact')
    class Meta:
        model  = models.Organization
        fields = ['id', 'name', 'contact',]

class FeedbackCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True)
    description = serializers.CharField( required=True)
    is_visible = serializers.BooleanField(required=True)
    
class FeedbackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model  = models.UserFeedback
        fields = ['id', 'subject', 'description','is_visible']

class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='project.id')
    name = serializers.CharField(source='project.name')
    class Meta:
        model  = ProjectsOrganizationMapping
        fields = ['id', 'name',]

class AdminListModelSerializer(serializers.ModelSerializer):
    def get_project_details(self, queryset) -> dict:
        project_details = ProjectsOrganizationMapping.objects.filter(organization=queryset.organization)
        project_list = ProjectSerializer(project_details,many=True, read_only=True).data
        return project_list
    def get_app_access(self,queryset) -> dict:

        app_access=models.UserAppMappping.objects.filter(user=queryset.user_id,status=1).values('app_id')
        ls=[]
        for i in app_access:
            ls.append(i['app_id'])
        return ls     
    project_list = serializers.SerializerMethodField(method_name='get_project_details')
    email = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    organization_name = serializers.CharField(source='organization')
    is_active = serializers.BooleanField(source ='status')
    access_list=serializers.SerializerMethodField(method_name='get_app_access')
    id = serializers.CharField(source='user.id')
    class Meta:
        model  = models.Role        
        fields =['id','role','first_name','last_name','email','organization','organization_name','is_active','project_list','access_list']

class UserprofileUpadate(serializers.Serializer):
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)
    email = serializers.EmailField(min_length=1, max_length=50, required=True)
    image = serializers.JSONField(required=False)


class CreateorganizationsSerializer(serializers.Serializer):
    org_name = serializers.CharField(min_length=2, max_length=50, required=True,error_messages={"detail": 'Ensure this field has at least 2 characters.'})
    image = serializers.JSONField(required=False)

class OrganizationLogoSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="name")
    class Meta:
        model  = models.Organization        
        fields =['id','org_name','image']

class ReplacePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=8, max_length=100, required=True)
    temp_password = serializers.CharField(
        min_length=8, max_length=30, required=True)
    new_password = serializers.CharField(
        min_length=8, max_length=30, required=True)

class CreateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)  
    email = serializers.EmailField(min_length=8, max_length=100, required=True) 
class OrganizationUserSerializer(serializers.Serializer):
    organization = serializers.UUIDField(required=False,validators=[validate_organization])
    access_list    = serializers.ListField(required=False)
    new_member_user= CreateUserSerializer(many=True,required=False)

class UserActivitySerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    organization = serializers.CharField(source='organization.name',allow_null=True)
    class Meta:
        model  = models.Activity        
        fields =['id','user','name','first_name','last_name','arguments','organization']


class OrganizationListSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="name")
    class Meta:
        model  = models.Organization        
        fields =['id','org_name']
class ProjectListSerializerData(serializers.Serializer):
    org_id = serializers.UUIDField(required=False)

class ProjectListSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(source='project.id',allow_null=True)
    project_name = serializers.CharField(source='project.name',allow_null=True)
    
    class Meta:
        model  = prg_model.ProjectsOrganizationMapping
        fields = ['project_id','project_name']  

class ActivateSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=8, max_length=100, required=True)
class LoginSerializer(serializers.Serializer): 

    username =serializers.CharField(min_length=2, max_length=50, required=True)
    password = serializers.CharField(min_length=1, max_length=50, required=True)
    remember_me = serializers.BooleanField(default=False, required=False)
 
class InactiveAppSerializer(serializers.ModelSerializer):
    def get_status(self,obj):
        user = self.context["user"]
        if obj :
             s=models.UserAppMappping.objects.filter(user_id=user,app_id=obj.id,status=2).first()
             if s:
               return 1
        return 0    
    status = serializers.SerializerMethodField(method_name='get_status')
    class Meta:
        model = models.QuiverApps
        fields =  ['id','app_name','description','app_type','status']

class UserlistView(serializers.ModelSerializer):
    email = serializers.CharField(source='username')
    class Meta:
        model  = models.User
        fields = ['id','first_name', 'last_name','email']      