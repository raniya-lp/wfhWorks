from django.db import models
from projects.models import Projects
from users.models import Organization, User
from generics import mixins
# Create your models here.

class ApiDetails(models.Model):
    organization=models.ForeignKey(Organization, on_delete=models.CASCADE,null=True,blank=True)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    api_name=models.CharField(max_length=250,unique=True)

    def __str__(self):
        return str(self.api_name)

class ApiCallDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apiname=models.ForeignKey(ApiDetails,on_delete=models.CASCADE)
    latency=models.FloatField()
    error_status=models.BooleanField()
    status_message=models.TextField()
    processed_at=models.DateTimeField(auto_now_add=True)
    ip_address=models.CharField(max_length=250,null=True,blank=True)
    system_name=models.CharField(max_length=250,null=True,blank=True)

    def __str__(self):
        return str(self.apiname)

class ApiNotification(mixins.GenericModelMixin):
    class Action(models.TextChoices):
        
        create       = "create", "Create"
        update       = "update", "Update"
        delete       = "delete", "Delete"
        comment      = "comment", "Comment"
        reply        = "reply" ,  "Reply"
        product_create  = "Product_create", "product_create"
        product_update  = "Product_update", "product_update"
    
    class Status(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"

    
    class HighLightStatus(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"
    apiname = models.ForeignKey(ApiDetails, on_delete=models.CASCADE)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="api_action_user")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="api_org_user")
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)

    def __str__(self):
        return str(self.apiname)

    
