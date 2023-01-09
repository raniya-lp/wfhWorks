from email.policy import default
from http import client
from pyexpat import model
from urllib import request
from rest_framework import fields,serializers
from . import models
from django.conf import settings

#serializer to fetch credentials for wokzone api
class projectnameSerializer(serializers.Serializer):
    name=serializers.CharField(max_length=100)
class ReportGenerateSerializer(serializers.Serializer):
    client_id=serializers.CharField(max_length=50)
    client_secret=serializers.CharField(max_length=50)
    grant_type=serializers.CharField(max_length=25)
    project_id=serializers.CharField(max_length=100)

class projectIdSerializer(serializers.Serializer):
    project_id=serializers.CharField(max_length=100)

class ReportListSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    keyword = serializers.CharField(max_length=100,allow_blank=True,required=False)
    start_date = serializers.DateField(required=False,allow_null=True)
    end_date = serializers.DateField(required=False,allow_null=True)

class TaskListSerializer(serializers.Serializer):
    report_id = serializers.CharField(max_length=100)
    keyword = serializers.CharField(max_length=100,allow_blank=True,required=False)

class ReportIdSerializer(serializers.Serializer):
    report_id=serializers.CharField(max_length=100)

class CommentSectionSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, max_length=1000)
    body = serializers.CharField(required=True, max_length=3000)
    tags = serializers.ListField(
        child=serializers.CharField(required=False)
    )
class TaskCommentSerializer(serializers.ModelSerializer):
    task_id = serializers.UUIDField()
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)

    class Meta:
        model =   models.TaskComments
        fields = ["task_id","comments","attachments"]

class TaskReplyListSerializer(serializers.ModelSerializer):
    task_comment_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField(source="user.get_full_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.TaskCommentsReply
        fields = ["id","task_comment_id","user_id","user_name","comments","created_at","updated_at","attachments","first_name","last_name"]


class TaskCommentListSerializer(serializers.ModelSerializer):
    task_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField(source="user.get_full_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    reply = TaskReplyListSerializer(many=True)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.TaskComments
        fields = ["id","task_id","user_id","user_name","comments","created_at","updated_at","attachments","reply","first_name","last_name"]


class TaskReplySerializer(serializers.ModelSerializer):
    task_comment_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.TaskCommentsReply
        fields = ["task_comment_id","comments","attachments"]


class TaskCommentUpdateSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.TaskComments
        fields = ["comments","attachments"]

class TaskReplyUpdationSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.TaskCommentsReply
        fields = ["comments","attachments"]

class LogoImageSerializer(serializers.Serializer):
    project_id = serializers.CharField(max_length=250)
    image = serializers.ImageField()

class MomentumReportShareSerializer(serializers.ModelSerializer):
    
    
    receiver_id = serializers.IntegerField(required=True)
    report_id= serializers.UUIDField(format='hex', required=True)
    message = serializers.CharField(required=False,allow_blank=True)
    
    class Meta:
        model =   models.ReportShare
        fields = ["report_id","receiver_id","message"]


class TaskNotifcationSerializer(serializers.ModelSerializer):
     def get_project_name(self,queryset):
        if queryset.task:
            data = models.ProjectFromWorkzone.objects.filter(id=queryset.task.reports.product_id.id).values('name').first()
            return data['name']
        elif queryset.report:
            data = models.ProjectFromWorkzone.objects.filter(id=queryset.report.product_id.id).values('name').first()
            return data['name']
        elif queryset.product:
            return queryset.product.name
        else:
            return None
     def get_task_id(self,queryset):
        if queryset.task:       
            return queryset.task.reports.id
        elif queryset.report:
            return queryset.report.id
        else:
            return None
     def get_task_title(self,queryset):
        if queryset.task:      
            return queryset.task.task_title
        else:
            return None
     
     project_name = serializers.SerializerMethodField(method_name='get_project_name')
     task_id = serializers.SerializerMethodField(method_name='get_task_id')
     task_name = serializers.SerializerMethodField(method_name='get_task_title')
     created_by = serializers.CharField(source='action_user.get_full_name')
     updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    
     class Meta:
       model =   models.TaskNotification
       fields = ["id","project_name","task_id","task_name","action_type","created_by","created_at","updated_at","action_status","higlight_status","comment","reply"]


class TaskNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )


class TaskReplySerializer(serializers.ModelSerializer):
    task_comment_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.TaskCommentsReply
        fields = ["task_comment_id","comments","attachments"]

class ReportListViewSerializer(serializers.ModelSerializer):
    project_id=serializers.CharField(source="product_id.id")
    project_name=serializers.CharField(source="product_id.name")
    org=serializers.CharField(source="product_id.organization_data")
    
    class Meta:
        model=models.Report
        fields=["id","project_name","report_name","created_at","project_id","org"]

class ProjectByIdSerializer(serializers.ModelSerializer):
    lg_img=serializers.SerializerMethodField()
    class Meta:
        model=models.ProjectFromWorkzone
        fields=["id","name","created_at","updated_at","lg_img"]

    def get_lg_img(self,obj):
        try:
            img=models.ProjectLogo.objects.get(project_id=obj)
            image_url=settings.MEDIA_LOGOIMG+str(img.logo_image)
            return image_url
        except:
            img=models.default_logo.objects.all()[:1].get()
            image_url=settings.MEDIA_LOGOIMG+str(img.logo_image)
            return image_url
