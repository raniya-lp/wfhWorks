from concurrent.futures import process
from rest_framework import serializers
from . import models
from users.models import Organization, User
from projects import models as prg_model


class UpdatedUserSerilizer(serializers.ModelSerializer):

    
    class Meta:
        model  = User

        fields = ['id','username','first_name','last_name']

class SectionsCreateSerilizer(serializers.Serializer):
    
    
    name = serializers.CharField(min_length=3, max_length=100, required=True)
    subline_text = serializers.CharField(min_length=3, max_length=100, required=True)
    process_item_id = serializers.IntegerField()
    data = serializers.ListField()
    



class BlueprintCreateSerilizer(serializers.Serializer):
    
    
    project_id = serializers.UUIDField(format='hex', required=True)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=3, max_length=100, required=True)
    processdata = SectionsCreateSerilizer(many=True)
    
class BluePrintProject(serializers.Serializer):
   project_id = serializers.UUIDField(format='hex',required=False)  
   org_id = serializers.UUIDField(format='hex',required=False)
   start_date = serializers.DateField(format="%d-%m-%Y",required=False)
   end_date = serializers.DateField(format="%d-%m-%Y",required=False)
   date_type = serializers.CharField(required=False)



class BlueprintListSerilizer(serializers.ModelSerializer):
    
    def get_notification(self,obj):
        cmt_list = []
        request_ = self.context["request"]
        
        comt_hist = models.BluePrintNotification.objects.filter(blueprint=obj,action_type__in=["comment","reply"],org_user=request_.user,higlight_status="unseen")
        total_count = len(comt_hist)
        return total_count
    
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
    
    first_name = serializers.CharField(source='created_by.first_name')
    last_name = serializers.CharField(source='created_by.last_name')
    updated_by = serializers.CharField(source='updated_by.first_name')
    created_by =serializers.CharField(source='created_by.get_full_name')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%p')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%p')
    notification_count = serializers.SerializerMethodField(method_name='get_notification')
    collaborators = serializers.SerializerMethodField(method_name='get_collaborators')
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
    created_by_email = serializers.CharField(source='created_by.username')


    

    class Meta:
        model  = models.BluePrint

        fields = ['id','first_name','last_name','project','project_name','title','description','created_by','created_by_email','updated_by','created_at','updated_at','notification_count','collaborators','organization_data']




class UpdateUserSerializer(serializers.ModelSerializer):
   username = serializers.SerializerMethodField('is_updated_user')
   def is_updated_user(self,obj):
       results = User.objects.filter(id=obj.updated_by).first()
       username = results.username
       return username
       


   class Meta:
       model = models.BluePrint
       fields = ['id','project','title','description','created_by','updated_by','username']




class BlueprintCreateSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(format='hex', required=False)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=1,required=False)
    blueprint_details = serializers.JSONField(required=False)


# class BlueprintUpdateSerializer(serializers.Serializer):
#     project_id = serializers.UUIDField(format='hex', required=False)
#     title = serializers.CharField(min_length=3, max_length=100, required=True)
#     description = serializers.CharField(min_length=1,required=False)
#     processdata = serializers.JSONField()


class SectionCreateSerializer(serializers.Serializer):
    blueprint_id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(min_length=3, max_length=100, required=True)
    subline_text = serializers.CharField(min_length=1,required=False)
    process_item_id = serializers.IntegerField(required=False,default=1)
    data = serializers.JSONField(required=False)



class SectionListSerializer(serializers.ModelSerializer):
    

    created_by =serializers.CharField(source='created_by.get_full_name')


    class Meta:
        model = models.Sections
       # fields = '__all__'
        fields = ['id','blue_print','name','subline_text','process_item_id','data','created_by']
        
   

class BlueprintGetSerilizer(serializers.ModelSerializer):

    def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"
    
    
    first_name = serializers.CharField(source='created_by.first_name')
    last_name = serializers.CharField(source='created_by.last_name')
    updated_by = serializers.CharField(source='updated_by.first_name')
    created_by =serializers.CharField(source='created_by.get_full_name')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    # processdata = SectionListSerializer(many=True)
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%p')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%p')
    organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
    # processdata = serializers.SerializerMethodField()
    


    class Meta:
        model  = models.BluePrint

        fields = ['id','first_name','last_name','project','project_name','title','description','created_by','updated_by','created_at','updated_at','blueprint_details','organization_data']

    # def get_processdata(self,obj):
    #     section= models.Sections.objects.filter(blue_print=obj).order_by('process_item_id')
    #     serializer_data = SectionListSerializer(section,many=True)

    #     return serializer_data.data


    

# class SectionsCreateSerilizer(serializers.Serializer):
#     name = serializers.CharField(min_length=3, max_length=100, required=True)
#     subline_text = serializers.CharField(min_length=3, max_length=100, required=True)
#     process_item_id = serializers.CharField(min_length=3, max_length=100, required=True)
#     data = serializers.ListField()

# class BlueprintCreateSerilizer(serializers.Serializer):
#     project_id = serializers.UUIDField(format='hex', required=True)
#     title = serializers.CharField(min_length=3, max_length=100, required=True)
#     description = serializers.CharField(min_length=3, max_length=100, required=True)
#     processdata = SectionsCreateSerilizer(many=True)



class BlueprintUpdateSerializer(serializers.Serializer):
    # project_id = serializers.UUIDField(format='hex', required=False)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=1,required=False)
    blueprint_details = serializers.JSONField(required=False,default=list)


class SectionsUpdateReqstSerilizer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=100, required=True)
    subline_text = serializers.CharField(min_length=3, max_length=100, required=True)
    process_item_id = serializers.CharField(min_length=3, max_length=100, required=True)
    data = serializers.ListField()

class BlueprintUpdateReqstSerilizer(serializers.Serializer):
    # project_id = serializers.UUIDField(format='hex', required=True)
    title = serializers.CharField(min_length=3, max_length=100, required=True)
    description = serializers.CharField(min_length=3, max_length=100, required=True)
    processdata = SectionsUpdateReqstSerilizer(many=True)

class OrganizationHistorySerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source='organization.name')
    class Meta:
        model =   prg_model.ProjectsOrganizationMapping
        fields = ["id","org_name"]

class BlueprintHistorySerializer(serializers.ModelSerializer):
     
     history_type = serializers.SerializerMethodField()
     project_name = serializers.CharField(source='project.name')
     blueprint_name = serializers.CharField(source='title')
     org = OrganizationHistorySerializer(source='project.project_data',many=True)
     updated_by = serializers.CharField(source='history_user.get_full_name')
     created_by = serializers.CharField(source='created_by.get_full_name')
     updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    
     class Meta:
       model =   models.HistoricalBluePrint
       fields = ["id","project_name","blueprint_name","history_type","created_by","created_at","history_user","history_id","updated_by","updated_at","org"]

     def get_history_type(self,obj):
        hist_type = obj.history_type
        if hist_type == "+":
            history_type = "Created"
        elif hist_type == "~":
            history_type = "Updated"
        elif hist_type == "-":
            history_type = "Deleted"
        return history_type




########### For blueprint Notification ###################
class BluePrinttNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )

class BluePrintNotifcationSerializer(serializers.ModelSerializer):

    def get_project_name(self, obj):
        
        if obj.action_type == "product_create" or obj.action_type == "product_update":
            
            return obj.product.name
        else:
            
            return obj.blueprint.project.name
     
     
    # project_name = serializers.CharField(source='blueprint.project.name',allow_null=True)
    project_name = serializers.SerializerMethodField(method_name='get_project_name')
    blueprint_id = serializers.CharField(source='blueprint.id',allow_null=True)
    blueprint_name = serializers.CharField(source='blueprint.title',allow_null=True)
    created_by = serializers.CharField(source='action_user.get_full_name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")

    class Meta:
       model =   models.BluePrintNotification
       fields = ["id","project_name","blueprint_id","blueprint_name","action_type","created_by","created_at","updated_at","action_status","higlight_status","comment","reply"]



#blueprint Comments serializer
class CommentSectionSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, max_length=1000)
    body = serializers.CharField(required=True, max_length=3000)
    tags = serializers.ListField(
        child=serializers.CharField(required=False)
    )

class BluePrintCommentSerializer(serializers.ModelSerializer):
    blueprint_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.BluePrintComments
        fields = ["blueprint_id","comments","attachments"]


class BluePrintReplyListSerializer(serializers.ModelSerializer):
    blueprint_comment_id = serializers.UUIDField()
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
        model =   models.BluePrintCommentsReply
        fields = ["id","blueprint_comment_id","user_id","first_name","last_name","comments","created_at","updated_at","attachments"]


class BluePrintCommentListSerializer(serializers.ModelSerializer):
    blueprint_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    # user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    reply = BluePrintReplyListSerializer(many=True)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.BluePrintComments
        fields = ["id","blueprint_id","user_id","first_name","last_name","comments","created_at","updated_at","attachments","reply"]


class BluePrintReplySerializer(serializers.ModelSerializer):
    blueprint_comment_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.BluePrintCommentsReply
        fields = ["blueprint_comment_id","comments","attachments"]


class BluePrintCommentUpdateSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.BluePrintComments
        fields = ["comments","attachments"]

class BluePrintReplyUpdationSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.BluePrintCommentsReply
        fields = ["comments","attachments"]



#For BluePrint Document Share

class BluePrintDocumentShareSerializer(serializers.ModelSerializer):
    
    
    receiver_id = serializers.IntegerField(required=True)
    blueprint_id= serializers.UUIDField(format='hex', required=True)
    message = serializers.CharField(required=False,allow_blank=True)
    
    class Meta:
        model =   models.BluePrintShare
        fields = ["blueprint_id","receiver_id","message"]


class BluePrintNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )

