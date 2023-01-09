from email.policy import default
from django.db import models
from generics import mixins
from projects .models import Projects
from users.models import User
from simple_history.models import HistoricalRecords


class CanvasType(models.Model):
    id=models.AutoField(primary_key=True)
    name = models.CharField(null=False, max_length=50, unique=False)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "CanvasType"

class Priority(models.Model):
    id=models.AutoField(primary_key=True)
    canvas_type = models.ForeignKey(CanvasType, on_delete=models.CASCADE,related_name="canvas_type")
    name = models.CharField(null=False, max_length=50, unique=False)
   
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Priority"

class Canvas(mixins.GenericModelMixin):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    title = models.CharField(null=False, max_length=100, unique=False)
    description = models.TextField(blank=True, null=True)
    user_type = models.CharField(null=False, max_length=50, unique=False)
    user_list = models.JSONField(null=True,default=dict)
    canvas_type = models.ForeignKey(CanvasType, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.BooleanField(null=False, default=False)
   
    def __str__(self):     
        return self.title
    
    class Meta:
        verbose_name_plural = "Canvas"

class CanvasTask(mixins.GenericModelMixin):
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE,related_name="canvas_task")
    question = models.TextField(null=False, unique=False)
    description = models.TextField(blank=True, null=True)
    attachments = models.JSONField(null=True,default=dict)
    
    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name_plural = "CanvasTask"
       

class CanvasMembers(mixins.GenericModelMixin):
    history = HistoricalRecords(inherit=True)
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    count   = models.IntegerField(null=False, unique=False)
   
    def __str__(self):
        return f"{self.user_id}"

    class Meta:
        verbose_name_plural = "CanvasMembers"

class CanvasNotes(mixins.GenericModelMixin):
    canvas_task = models.ForeignKey(CanvasTask, on_delete=models.CASCADE,related_name="canvas_not")
    answer = models.TextField(blank=True, null=True)
    # canvas_member = models.ForeignKey(CanvasMembers, on_delete=models.CASCADE)
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE,related_name="priority")
    colour = models.CharField(null=False, max_length=50, unique=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
        
    def __str__(self):
        return self.answer

    class Meta:
        verbose_name_plural = "CanvasNotes"
            
# Canvas notification

class CanvasComments(mixins.GenericModelMixin):
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    # history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.canvas}"

    class Meta:
        verbose_name_plural = "CanvasComments"

class CanvasCommentsReply(mixins.GenericModelMixin):
    canvas_comment = models.ForeignKey(CanvasComments, on_delete=models.CASCADE,related_name="reply")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    # history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.canvas_comment}"

    class Meta:
        verbose_name_plural = "CanvasCommentsReply"


class CanvasShare(mixins.GenericModelMixin):
    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='canvas_receiver')
    message = models.CharField(null=True, max_length=1000)
    status = models.CharField(null=False, max_length=100,default="sent")
    
    def __str__(self):
        return f"{self.canvas}"

    class Meta:
        verbose_name_plural = "CanvasShare"


class CanvasNotification(mixins.GenericModelMixin):
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

    canvas = models.ForeignKey(Canvas, on_delete=models.CASCADE,null=True)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="canvas_action_user")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE)
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    comment = models.ForeignKey(CanvasComments, on_delete=models.CASCADE,null=True)
    reply = models.ForeignKey(CanvasCommentsReply, on_delete=models.CASCADE,null=True)
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)