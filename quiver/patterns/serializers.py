from email.policy import default
from rest_framework import serializers
from . import models
from projects import models as prg_model

class PatternSectionSubCreateSerializer(serializers.Serializer):
    sub_section = serializers.CharField(min_length=3, max_length=100, required=True)
    level = serializers.IntegerField(required=False,default=1)
    data=serializers.ListField(required=True)

class PatternSectionCreateSerializer(serializers.Serializer):
    section = serializers.CharField(min_length=3, max_length=100, required=True)
    level = serializers.IntegerField(required=False,default=1)
    has_sub_section = serializers.BooleanField(required=False)
    section_icon = serializers.JSONField(required=False)
    # font_types = serializers.CharField(min_length=1, max_length=100, required=True)
    section_type = serializers.CharField(min_length=3, max_length=100, required=True)
    data=serializers.ListField(required=False)
    sub_section_list=PatternSectionSubCreateSerializer(many=True,required=False)
    
class PatternCreateSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(format='hex', required=False)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=1,required=False)
    # pattern_section = PatternSectionCreateSerializer(many=True)

class PatternSubSerializer(serializers.ModelSerializer):
    def sub_section(self,queryset):
        pattern_section_data=models.PatternSectionCollection.objects.filter(pattern_sub_section=queryset.id).values('id','data_list','data_text','data_image').order_by('created_at')
        return pattern_section_data
    sub_section_list = serializers.SerializerMethodField(method_name='sub_section')
    class Meta:
        model = models.PatternSubSection
        fields=['id','name','level','sub_section_list']
    
class PatternSectionSerializer(serializers.ModelSerializer):
    def get_pattern__sub_section(self,queryset):
        if queryset.has_sub_section:
            pattern_section_obj=models.PatternSubSection.objects.filter(pattern_section=queryset.id).order_by('level')
            pattern_sub_section = PatternSubSerializer(pattern_section_obj,many=True, read_only=True).data
            return pattern_sub_section
        else:
            pattern_section_data=models.PatternSectionCollection.objects.filter(pattern_section=queryset.id).values('id','data_list','data_text','data_image').order_by('created_at')
            return pattern_section_data
            
    pattern_sub_section = serializers.SerializerMethodField(method_name='get_pattern__sub_section')
    class Meta:
        model = models.PatternSection
        fields=['id','name','level','pattern','has_sub_section','section_type','section_icon','pattern_sub_section']
class PatternListSerializer(serializers.ModelSerializer):
    # def get_pattern_section(self, queryset):
    #     pattern_section_obj=models.PatternSection.objects.filter(pattern=queryset.id).order_by('level')
    #     pattern_section = PatternSectionSerializer(pattern_section_obj,many=True, read_only=True).data
    #     return pattern_section

    def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"
        
    created_by_name = serializers.CharField(source='created_by.get_full_name')
    pattern_section = serializers.JSONField(source='section')
    project_name = serializers.CharField(source='project.name')
    updated_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M %p")
    created_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M %p")
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
    # created_at = serializers.SerializerMethodField(method_name='get_created_at')
    # updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
    # def get_created_at(self, obj):
    #     return obj.created_at.strftime("%d/%m/%Y %H:%M %p")
    # def get_updated_at(self, obj):
    #     return obj.updated_at.strftime("%d/%m/%Y %H:%M %p")
    class Meta:
        model  = models.Pattern
        fields = ['id', 'title','created_by_name','description','project','project_name','pattern_section','created_at','updated_at','organization_data']

class PatternProject(serializers.Serializer):
   project_id = serializers.UUIDField(format='hex',required=False)  
   org_id = serializers.UUIDField(format='hex',required=False)
   start_date = serializers.DateField(format="%d-%m-%Y",required=False)
   end_date = serializers.DateField(format="%d-%m-%Y",required=False)
   date_type = serializers.CharField(required=False)


class PatternAllListSerializer(serializers.ModelSerializer):
    def get_collaborators(self, obj):
        
        if obj:
            return [{"id" : obj.created_by.id,"first_name" : obj.created_by.first_name,"last_name" : obj.created_by.last_name}]
        else:
            return "NA"
    def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"
    def get_notification(self,obj):
        cmt_list = []
        request_ = self.context["request"]
        
        comt_hist = models.PatternNotification.objects.filter(pattern=obj,action_type__in=["comment","reply"],org_user=request_.user,higlight_status="unseen")
        # l2 = list(map(lambda v: cmt_list.append(v.id), comt_hist))
        # reply_hist = models.HistoricalPatterCommentsReply.objects.filter(pattern_comment__in=cmt_list)
        # total_count = len(comt_hist)+len(reply_hist)
        total_count = len(comt_hist)
        return total_count

    created_by_name = serializers.CharField(source='created_by.get_full_name')
    project_name = serializers.CharField(source='project.name')
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
    # updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
    updated_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M %p")
    created_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M %p")
    created_date_time = serializers.CharField(source='created_at')
    updated_date_time = serializers.CharField(source='updated_at')
    notification_count = serializers.SerializerMethodField(method_name='get_notification')
    collaborators = serializers.SerializerMethodField(method_name='get_collaborators')
    class Meta:
        model  = models.Pattern
        fields = ['id', 'title','created_by_name','description','project','project_name','created_at','updated_at','created_date_time','updated_date_time','notification_count','collaborators','organization_data']

class PatternFontfetchSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.PatternFont
        fields =['name','upload_flag','data_file_path','generic','font_type','url']


class PatternUpdateSerializer(serializers.Serializer):
    edit_pattern_section = serializers.BooleanField(required=True)
    title = serializers.CharField(min_length=3, max_length=100, required=False)
    description = serializers.CharField(min_length=1,required=False)
    pattern_section_id = serializers.UUIDField(format='hex', required=False)
    pattern_section = PatternSectionCreateSerializer(many=True, required=False)

class PatternAddSerializer(serializers.Serializer):
    pattern_id = serializers.UUIDField(format='hex', required=True)
    pattern_section = PatternSectionCreateSerializer(many=True)
    
class PatternFontSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1,required=False)
    generic = serializers.CharField(min_length=1,required=False)
    font_type = serializers.CharField(min_length=1,required=False)
    file = serializers.FileField(required=False)
    url = serializers.CharField(min_length=1,required=False)


class OrganizationHistorySerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source='organization.name')
    class Meta:
        model =   prg_model.ProjectsOrganizationMapping
        fields = ["id","org_name"]


class PatternHistorySerializer(serializers.ModelSerializer):
     
     history_type = serializers.SerializerMethodField()
     project_name = serializers.CharField(source='project.name')
     pattern_name = serializers.CharField(source='title')
     org = OrganizationHistorySerializer(source='project.project_data',many=True)
     updated_by = serializers.CharField(source='history_user.get_full_name')
     created_by = serializers.CharField(source='created_by.get_full_name')
     updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    
     class Meta:
       model =   models.HistoricalPattern
       fields = ["id","project_name","pattern_name","history_type","created_by","created_at","history_user","history_id","updated_by","updated_at","org"]

     def get_history_type(self,obj):
        hist_type = obj.history_type
        if hist_type == "+":
            history_type = "Created"
        elif hist_type == "~":
            history_type = "Updated"
        elif hist_type == "-":
            history_type = "Deleted"
        return history_type



#Pattern Comments serializer
class CommentSectionSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, max_length=1000,error_messages={'blank': 'No subject added'})
    body = serializers.CharField(required=True, max_length=3000,error_messages={'blank': 'No content added'})
    tags = serializers.ListField(
        child=serializers.CharField(required=False)
    )

class PatternCommentSerializer(serializers.ModelSerializer):
    pattern_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.PatterComments
        fields = ["pattern_id","comments","attachments"]


class PatternReplyListSerializer(serializers.ModelSerializer):
    pattern_comment_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    # user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")


    class Meta:
        model =   models.PatterCommentsReply
        fields = ["id","pattern_comment_id","user_id","first_name","last_name","comments","created_at","updated_at","attachments"]


class PatternCommentListSerializer(serializers.ModelSerializer):
    def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.pattern.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"

    pattern_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    # user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    reply = PatternReplyListSerializer(many=True)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.PatterComments
        fields = ["id","pattern_id","organization_data","user_id","first_name","last_name","comments","created_at","updated_at","attachments","reply"]


class PatternReplySerializer(serializers.ModelSerializer):
    pattern_comment_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.PatterCommentsReply
        fields = ["pattern_comment_id","comments","attachments"]


class PatternCommentUpdateSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.PatterComments
        fields = ["comments","attachments"]

class PatternReplyUpdationSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.PatterCommentsReply
        fields = ["comments","attachments"]



#For patter CRUD 

class PatternCreationSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(format='hex', required=False)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=1,required=False)
    section = serializers.JSONField(required=False)

    class Meta:
        model =   models.Pattern
        fields = ["project_id","title","description","section"]


class PatternUpdationSerializer(serializers.ModelSerializer):
    
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=1,required=False)
    section = serializers.JSONField(required=False)

    class Meta:
        model =   models.Pattern
        fields = ["title","description","section"]


#For Pattern Filter

class PatternFilterSerializer(serializers.Serializer):
    
    
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")
    date_type = serializers.CharField(required=True)

class PatternFilterListSerializer(serializers.ModelSerializer):

    def get_collaborators(self, obj):
        
        if obj:
            return [{"id" : obj.created_by.id,"first_name" : obj.created_by.first_name,"last_name" : obj.created_by.last_name}]
        else:
            return "NA"
    def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"

    def get_notification(self,obj):
        cmt_list = []
        request_ = self.context["request"]
        
        comt_hist = models.PatternNotification.objects.filter(pattern=obj,action_type__in=["comment","reply"],org_user=request_.user,higlight_status="unseen")
        # l2 = list(map(lambda v: cmt_list.append(v.id), comt_hist))
        # reply_hist = models.HistoricalPatterCommentsReply.objects.filter(pattern_comment__in=cmt_list)
        # total_count = len(comt_hist)+len(reply_hist)
        total_count = len(comt_hist)
        return total_count
    
    created_by_name = serializers.CharField(source='created_by.get_full_name')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y")
    created_at = serializers.DateTimeField(format="%d-%m-%Y")
    notification_count = serializers.SerializerMethodField(method_name='get_notification')
    collaborators = serializers.SerializerMethodField(method_name='get_collaborators')
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')

    class Meta:
        model =   models.Pattern
        fields = ["id","title","description","created_by_name","project","project_name","created_at","updated_at","notification_count","collaborators","organization_data"]


#For Pattern Notification


class PatternNotifcationSerializer(serializers.ModelSerializer):
     
    def get_project_name(self, obj):
        
        if obj.action_type == "product_create" or obj.action_type == "product_update":
            
            return obj.product.name
        else:
            
            return obj.pattern.project.name
    #  project_name = serializers.CharField(source='pattern.project.name',allow_null=True)
    project_name = serializers.SerializerMethodField(method_name='get_project_name')
    pattern_id = serializers.CharField(source='pattern.id',allow_null=True)
    pattern_name = serializers.CharField(source='pattern.title',allow_null=True)
    created_by = serializers.CharField(source='action_user.get_full_name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")

    class Meta:
       model =   models.PatternNotification
       fields = ["id","project_name","pattern_id","pattern_name","action_type","created_by","created_at","updated_at","action_status","higlight_status","comment","reply"]


class PatternNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )



#For Pattern Document Share

class PatternDocumentShareSerializer(serializers.ModelSerializer):
    
    
    receiver_id = serializers.IntegerField(required=True)
    pattern_id= serializers.UUIDField(format='hex', required=True)
    message = serializers.CharField(required=False,allow_blank=True)
    class Meta:
        model =   models.PatterShare
        fields = ["pattern_id","receiver_id","message"]