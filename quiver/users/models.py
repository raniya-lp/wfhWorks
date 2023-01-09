from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from generics import mixins 


class User(AbstractUser):
    # Changing default username field type `CharField` to `EmailField`
    username = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={'unique': "A user with that username already exists."})

    EMAIL_FIELD = 'username'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.username

    class Meta:
        verbose_name_plural = "Users"


class Profile(mixins.GenericModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user_prf')
    phone = models.BigIntegerField(null=True)
    image = models.JSONField(blank=True,default=dict)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Profiles"

class Organization(mixins.GenericModelMixin):
    name = models.CharField(null=False, max_length=50, unique=True)
    image = models.JSONField(blank=True,default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Organizations"


class Role(mixins.GenericModelMixin):
    class RoleName(models.TextChoices):
        """
        -----------
        Permissions
        -----------
        user      : see roadmaps
        admin     : everything in the organization
        """
        user        = "user", "User"
        admin       = "admin", "Organization Admin"
        superadmin  = "superadmin", "Super Admin"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(null=True,
                            max_length=50,
                            choices=RoleName.choices,
                            default=RoleName.admin)
    # organization: Field to check if organization user or not
    organization = models.ForeignKey(Organization,
                                     null=True,
                                     on_delete=models.CASCADE)
    status = models.BooleanField(null=False, default=False)
    roadmap_access = models.BooleanField(null=False, default=True)
    pattern_access = models.BooleanField(null=False, default=True)
    context_access = models.BooleanField(null=False, default=True)
    blueprint_access = models.BooleanField(null=False, default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Roles"


class Activity(mixins.GenericModelMixin):
    class Action(models.TextChoices):
        roadmap_created = "roadmap created", "Roadmap Created"
        roadmap_updated = "roadmap updated", "Roadmap Updated"
        roadmap_deleted = "roadmap deleted", "Roadmap Deleted"
        feature_created = "feature created", "Reature Created"
        feature_updated = "feature updated", "Feature Updated"
        feature_deleted = "feature deleted","Feature Seleted"
        feedback_send   = "feedback send","Feedback Send"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20,choices=Action.choices)
    description = models.TextField(blank=True, null=True)
    arguments = models.JSONField(null=False, default=dict)
    organization = models.ForeignKey(Organization,null=True,on_delete=models.CASCADE)
    projects=models.UUIDField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Activities"


class UserFeedback(mixins.GenericModelMixin):

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=20,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_visible = models.BooleanField(null=False, default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "UserFeedback"


class QuiverApps(models.Model):
    class ApptypeList(models.TextChoices):
        project_Initiation ="Project Initiation"
        requirement_Analysis= "Requirement Analysis"
        planning="Planning"
        designing="Designing"
        development= "Development"
        testing=  "Testing"
        deployment=  "Deployment"
        maintenance="Maintenance"
    id=models.AutoField(primary_key=True)  
    app_name = models.CharField(null=False, max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    app_type = models.CharField(max_length=50,
                            choices=ApptypeList.choices)
    icon =models.JSONField(blank=True,default=dict)
    status = models.CharField(default=1, max_length=50 )
    
    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "QuiverApps"

class  UserAppMappping(mixins.GenericModelMixin):

    app =  models.ForeignKey(QuiverApps, on_delete=models.CASCADE)   
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(default=1, max_length=50 )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "UserAppMappping"