from distutils.command.upload import upload
from email.policy import default
from django.db import models
from generics import mixins
from projects .models import Projects
from users.models import User
from projects.models import ProjectsOrganizationMapping
from simple_history.models import HistoricalRecords
from django_base64field.fields import Base64Field
from users import models as user_models
import os
from django.conf import settings
from urllib.parse import urlparse

class ProjectFromWorkzone(mixins.GenericModelMixin):
    organization_data=models.ForeignKey(user_models.Organization,null=True,on_delete=models.CASCADE)
    name = models.CharField(null=False, max_length=500, unique=False)
    status=models.CharField(null=False, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

class Report(mixins.GenericModelMixin):
    product_id = models.ForeignKey(ProjectFromWorkzone, on_delete=models.CASCADE)
    report_name = models.CharField(null=False, max_length=500, unique=False)
    created_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = "ReportList"


class Report_Pdf(mixins.GenericModelMixin):
    report_id=models.ForeignKey(Report, on_delete=models.CASCADE)
    report_pdf=models.TextField(null=False,default="")
    report_size=models.CharField(max_length=10,default='0 Kb')

def upload_to(instance, filename):
    try:
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.project_id.name, ext)
        filename=filename.replace(' ','_')
        imgurl=settings.MEDIA_LOGOIMG+'LogoFolder/'+filename
        print('\n\nimage found: ',imgurl)
        parse_object = urlparse(imgurl)
        path1=parse_object.path
        print('\n\n\nfile found',path1)

        loc=os.getcwd()+'/quiver'+path1
        loc=loc.replace('\\','/')
        print('\n\nloction: ',loc)
        rem=os.remove(loc)
            
    except:
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.project_id.name, ext)
    
    return 'LogoFolder/{filename}'.format(filename=filename)

class ProjectLogo(models.Model):
    project_id= models.ForeignKey(ProjectFromWorkzone, on_delete=models.CASCADE)
    logo_image=models.ImageField(upload_to=upload_to)

def upload_to_default(instance, filename):
    try:
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format('default', ext)
        filename=filename.replace(' ','_')
        imgurl=settings.MEDIA_LOGOIMG+'LogoFolder/'+filename
        print('\n\nimage found: ',imgurl)
        parse_object = urlparse(imgurl)
        path1=parse_object.path
        print('\n\n\nfile found',path1)
        
        loc=os.getcwd()+'/quiver'+path1
        loc=loc.replace('\\','/')
        print('\n\nloction: ',loc)
        rem=os.remove(loc)
        return 'LogoFolder/{filename}'.format(filename=filename)
    except:
        return 'LogoFolder/{filename}'.format(filename=filename)

class default_logo(models.Model):
    logo_image=models.ImageField(upload_to=upload_to_default)

class Task(mixins.GenericModelMixin):
    reports=models.ForeignKey(Report, on_delete=models.CASCADE)
    task_id=models.IntegerField(null=False, unique=False)
    task_title=models.TextField(null=False, max_length=500, unique=False)
    status=models.CharField(null=False, max_length=500, unique=False)
    workspacename=models.CharField(null=False, max_length=500, unique=False)
    startdate=models.DateField()
    enddate=models.DateField()
    
    def __str__(self):
        return self.task_title
    
    class Meta:
        verbose_name_plural = "Task"

class TaskComments(mixins.GenericModelMixin):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="task_comment_user")
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.task}"

    class Meta:
        verbose_name_plural = "TaskComments"

class TaskCommentsReply(mixins.GenericModelMixin):
    task_comment = models.ForeignKey(TaskComments, on_delete=models.CASCADE,related_name="reply")
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="task_reply_user")
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.task_comment}"

    class Meta:
        verbose_name_plural = "TaskCommentsReply"


class ReportShare(mixins.GenericModelMixin):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE,related_name="report_sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='report_receiver')
    status = models.CharField(null=False, max_length=100,default="sent")
    message = models.CharField(null=True, max_length=1000,default="Sample")
    
    def __str__(self):
        return f"{self.report}"

    class Meta:
        verbose_name_plural = "ReportShare"


class TaskNotification(mixins.GenericModelMixin):
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
    report = models.ForeignKey(Report, on_delete=models.CASCADE,null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE,null=True)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="task_action_user")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="task_org_user")
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    comment = models.ForeignKey(TaskComments, on_delete=models.CASCADE,null=True)
    reply = models.ForeignKey(TaskCommentsReply, on_delete=models.CASCADE,null=True)
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)

