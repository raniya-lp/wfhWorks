from django.db import models

# Create your models here.
from django.db import models
from email.policy import default
from django.db import models
from generics import mixins
from projects .models import Projects
from users.models import User
from simple_history.models import HistoricalRecords


class BluePrint(mixins.GenericModelMixin):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    title = models.CharField(null=False, max_length=100, unique=False)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="updated_user")
    blueprint_details = models.JSONField(null=True,default=list)
    history = HistoricalRecords(inherit=True)
    
    def __str__(self):
        return self.title
    class Meta:
        verbose_name_plural = "BluePrint"

class Sections(mixins.GenericModelMixin):
    blue_print = models.ForeignKey(BluePrint, on_delete=models.CASCADE,related_name="processdata")
    name = models.CharField(null=False, max_length=100, unique=False)
    subline_text = models.CharField(null=True, max_length=100, unique=False)
    process_item_id = models.IntegerField(null=False)
    data = models.JSONField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Sections"


# blueprint notification

class BluePrintComments(mixins.GenericModelMixin):
    blueprint = models.ForeignKey(BluePrint, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    # history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.blueprint}"

    class Meta:
        verbose_name_plural = "blueprintComments"

class BluePrintCommentsReply(mixins.GenericModelMixin):
    blueprint_comment = models.ForeignKey(BluePrintComments, on_delete=models.CASCADE,related_name="reply")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    # history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.blueprint_comment}"

    class Meta:
        verbose_name_plural = "BlueprintCommentsReply"


class BluePrintShare(mixins.GenericModelMixin):
    blueprint = models.ForeignKey(BluePrint, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='blueprint_receiver')
    status = models.CharField(null=False, max_length=100,default="sent")
    message = models.CharField(null=True, max_length=1000)
    
    def __str__(self):
        return f"{self.blueprint}"

    class Meta:
        verbose_name_plural = "BluePrintShare"


class BluePrintNotification(mixins.GenericModelMixin):
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

    blueprint = models.ForeignKey(BluePrint, on_delete=models.CASCADE,null=True)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="blueprint_action_user")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE)
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    comment = models.ForeignKey(BluePrintComments, on_delete=models.CASCADE,null=True)
    reply = models.ForeignKey(BluePrintCommentsReply, on_delete=models.CASCADE,null=True)
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)