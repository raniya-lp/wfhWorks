from rest_framework import serializers
from . import models
from users import models as user_models
from users.serializers import validate_organization



def validate_project(value):
    try:
        project = models.Projects.objects.get(pk=value)
    except models.Projects.DoesNotExist:
        raise serializers.ValidationError("project must be a valid Projects id")
    return project

def validate_roadmap(value):
    try:
        roadmap = models.RoadMaps.objects.get(pk=value)
    except models.RoadMaps.DoesNotExist:
        raise serializers.ValidationError("project must be a valid Projects id")
    return roadmap

class ProjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=50, required=True)
    status = serializers.CharField(min_length=3, max_length=10, required=False)
    organization = serializers.UUIDField(required=False,validators=[validate_organization])

class ProjectSerializer(serializers.ModelSerializer):
    # def get_organization(self, obj) -> dict:
    #     return{'name':obj.organization.name, 'id':obj.organization.id}
    
    # organization = serializers.SerializerMethodField(method_name='get_organization')
    
    class Meta:
        model  = models.Projects
        fields = ['id', 'name','status']
class ProjectListSerializer(serializers.ModelSerializer):
    def get_organization(self, obj) -> dict:
        return{'name':obj.organization.name, 'id':obj.organization.id}
    def get_created_at(self, obj):
        return obj.created_at.strftime("%m/%d/%Y")
    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%m/%d/%Y")
    name = serializers.CharField(source='project.name')
    id = serializers.CharField(source='project.id')
    project_org_id=serializers.CharField(source='id')
    status = serializers.CharField(source='project.status')
    organization = serializers.SerializerMethodField(method_name='get_organization')
    created_by =serializers.CharField(source='created_by.get_full_name')
    first_name =serializers.CharField(source='created_by.first_name')
    last_name =serializers.CharField(source='created_by.last_name')
    created_at = serializers.SerializerMethodField(method_name='get_created_at')
    updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
    class Meta:
        model  = models.ProjectsOrganizationMapping
        fields = ['id', 'name','status','organization','created_at','updated_at','created_by','first_name','last_name','project_org_id']

class ProjectsOrganizationSerializer(serializers.Serializer):
    project_name = serializers.CharField(min_length=3, max_length=50, required=True,error_messages={"detail": 'Ensure this field has no more than 50 characters.'})


class RoadMapCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=50, required=True)
    collaborators = serializers.ListField(child=serializers.JSONField(required=False),required=False)
    description = serializers.CharField(required=False)
    # project = serializers.UUIDField(required=False,validators=[validate_project])
    
class CollaboratorSerializer(serializers.ModelSerializer):
    
    def get_user(self, queryset) -> dict:
        user = user_models.User.objects.filter(id=queryset.user.id).first()
        if user is None:
            return user
        return {"id": user.id, "first_name": user.first_name,"last_name": user.last_name}
    
    user = serializers.SerializerMethodField(method_name='get_user')
    
    class Meta:
        model  = models.Collaborator
        fields = ['id', 'user','write']

class RoadMapSerializer(serializers.ModelSerializer):
    
    class Meta:
        model  = models.RoadMaps
        fields = ['id', 'name', 'description']
class QuiverProjectListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model  = models.Projects
        fields = ['id', 'name','status']

class RoadMapListSerializer(serializers.ModelSerializer):

    def get_notification(self,obj):
        cmt_list = []
        user = self.context["user_id"]
        
        comt_hist = models.RoadMapNotification.objects.filter(roadmap=obj,action_type__in=["comment","reply"],org_user_id=user,higlight_status="unseen")
        total_count = len(comt_hist)
        return total_count

    def get_projects(self, queryset) -> dict:
        projects = models.Projects.objects.filter(id=queryset.project.id).first()
        if projects is None:
            return projects
        return {"id": projects.id, "name": projects.name}

    def get_collaborator(self, queryset) -> dict:
     
        collaborator = models.Collaborator.objects.filter(roadmap=queryset).values_list("user",flat=True)
        user = user_models.User.objects.filter(id__in=list(collaborator)).values('first_name','last_name')[:3]
        return user
      
       
    
    def get_updated_at(self, queryset) -> dict:
        r_feature = models.RoadMapFeatures.objects.filter(roadmap=queryset)
        if r_feature.exists():
            if r_feature.latest('updated_at').updated_at > queryset.updated_at:
                updated_time = r_feature.latest('updated_at').updated_at.strftime("%d-%m-%Y %I:%M:%S %p")
            else:
                updated_time = queryset.updated_at.strftime("%d-%m-%Y %I:%M:%S %p")
        else:
            updated_time = queryset.updated_at.strftime("%d-%m-%Y %I:%M:%S %p")
        
        return updated_time
    def get_wirte(self,queryset):
        user=self.context['user_id']
        role = user_models.Role.objects.get(user = user).role
        if role =='user':
            collaborator = models.Collaborator.objects.filter(roadmap=queryset,user=user).first()
            if collaborator:
                    return collaborator.write
            else:
                return False
        else:
            return True 
    def get_view_status(self,obj):
      user = self.context["user_id"]
      
      if not models.Collaborator.objects.filter(roadmap=obj,user=user):
        
        if models.RoadMapShare.objects.filter(receiver=user):
            
            return True
        else:
            
            return False
      else:
        
        return False

    project=serializers.CharField(source='project.id')
    project_name=serializers.CharField(source='project.name')
    created_by =serializers.CharField(source='created_by.get_full_name')
    created_by_email =serializers.CharField(source='created_by.username')
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    wirte=serializers.SerializerMethodField(method_name='get_wirte')
    title=serializers.CharField(source='name')
    collaborators = serializers.SerializerMethodField(method_name='get_collaborator')
    projects = serializers.SerializerMethodField(method_name='get_projects')
    updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
    shared_status = serializers.SerializerMethodField(method_name='get_view_status')
    notification_count = serializers.SerializerMethodField(method_name='get_notification')
    
    class Meta:
        model  = models.RoadMaps
        fields = ['id', 'name','title', 'projects','description','wirte','created_at','updated_at','collaborators','created_by','created_by_email','shared_status','notification_count','project','project_name']

class RoadMapFeatureCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=500, required=True)
    reach = serializers.FloatField(min_value=0.0, max_value=None, required=True)
    impact = serializers.FloatField(min_value=0.0, max_value=None, required=True)
    confidence = serializers.FloatField(min_value=0.0, max_value=None, required=True)
    effort = serializers.FloatField(min_value=0.0, max_value=None, required=True)
    description = serializers.CharField(required=False)
    image = serializers.JSONField(required=False)

class RoadMapFeatureSerializer(serializers.ModelSerializer):
    
    class Meta:
        model  = models.RoadMapFeatures
        fields = ['id', 'name', 'reach','impact','confidence','effort','rice_score','status', 'order']

class RoadMapFeatureListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.RoadMapFeatures
        fields = ['id', 'name', 'reach','impact','confidence','effort','rice_score','status','order','updated_at','description','image']
class RoadmapProject(serializers.Serializer):
   project_id = serializers.UUIDField(format='hex',required=False)
   org_id = serializers.UUIDField(format='hex',required=False)
   start_date = serializers.DateField(format="%d-%m-%Y",required=False)
   end_date = serializers.DateField(format="%d-%m-%Y",required=False)
   date_type = serializers.CharField(required=False) 



#For notification

class RoadMapNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )



class RoadMapNotifcationSerializer(serializers.ModelSerializer):
    def get_feature_title(self,obj):
        
        if (obj.action_type == "feature_create") or (obj.action_type == "feature_update"):
            
            return obj.feature.name
        else:
            return None
    
    def get_project_name(self, obj):
        
        if obj.action_type == "product_create" or obj.action_type == "product_update":
            
            return obj.product.name
        else:
            
            return obj.roadmap.project.name

    project_name = serializers.SerializerMethodField(method_name='get_project_name')
    # project_name = serializers.CharField(source='roadmap.project.name',allow_null=True)
    roadmap_id = serializers.CharField(source='roadmap.id',allow_null=True)
    roadmap_name = serializers.CharField(source='roadmap.name',allow_null=True)
    created_by = serializers.CharField(source='action_user.get_full_name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    feature_title = serializers.SerializerMethodField(method_name='get_feature_title')
    
    class Meta:
       model =   models.RoadMapNotification
       fields = ["id","project_name","roadmap_id","roadmap_name","action_type","created_by","created_at","updated_at","action_status","higlight_status","comment","reply","feature","feature_title","product"]



#FOR COMMENTS

class CommentSectionSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, max_length=1000)
    body = serializers.CharField(required=True, max_length=3000)
    tags = serializers.ListField(
        child=serializers.CharField(required=False)
    )


class RoadMapCommentSerializer(serializers.ModelSerializer):
    roadmap_id = serializers.UUIDField()
    feature_id = serializers.UUIDField()
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.RoadMapComments
        fields = ["roadmap_id","comments","feature_id","attachments"]

class RoadMapReplyListSerializer(serializers.ModelSerializer):
    roadmap_comment_id = serializers.UUIDField()
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
        model =   models.RoadMapCommentsReply
        fields = ["id","roadmap_comment_id","user_id","first_name","last_name","comments","created_at","updated_at","attachments"]


class RoadMapCommentListSerializer(serializers.ModelSerializer):
    roadmap_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    # user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    reply = RoadMapReplyListSerializer(many=True)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.RoadMapComments
        fields = ["id","feature","roadmap_id","user_id","first_name","last_name","comments","created_at","updated_at","attachments","reply"]


class RoadMapCommentUpdateSerializer(serializers.ModelSerializer):
    
    
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.RoadMapComments
        fields = ["comments","attachments"]



class RoadMapReplySerializer(serializers.ModelSerializer):
    roadmap_comment_id = serializers.UUIDField()
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.RoadMapCommentsReply
        fields = ["roadmap_comment_id","comments","attachments"]


class RoadMapReplyUpdationSerializer(serializers.ModelSerializer):
    
   
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.RoadMapCommentsReply
        fields = ["comments","attachments"]

#For RoadMap Document Share

class RoadMapDocumentShareSerializer(serializers.ModelSerializer):
    
    
    receiver_id = serializers.IntegerField(required=True)
    roadmap_id= serializers.UUIDField(format='hex', required=True)
    message = serializers.CharField(required=False,allow_blank=True)
    class Meta:
        model =   models.RoadMapShare
        fields = ["roadmap_id","receiver_id","message"]

class RoadmapFilterSerializer(serializers.Serializer):
    
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")
    date_type = serializers.CharField(required=True)

class RoadmapFilterListSerializer(serializers.ModelSerializer):
    
    created_by_name = serializers.CharField(source='created_by.get_full_name')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y")
    created_at = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        model = models.RoadMaps
        fields = ['id','project','project_name','name','description','created_by','created_at','updated_at','created_by_name']

class RoadMapsingleSerializer(serializers.ModelSerializer):
    def get_organization(self, obj) -> dict:
        s= models.ProjectsOrganizationMapping.objects.filter(project_id=obj.project.id).first()
        return s.organization_id
    def get_collaborator(self, queryset) -> dict:
        collaborator = models.Collaborator.objects.filter(roadmap=queryset)
        return CollaboratorSerializer(collaborator,many=True).data
    created_by_name = serializers.CharField(source='created_by.get_full_name')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    organization = serializers.SerializerMethodField(method_name='get_organization')
    collaborator = serializers.SerializerMethodField(method_name='get_collaborator')
    
    class Meta:
        model  = models.RoadMaps
        fields = ['id', 'name', 'description','organization','project','project_name','created_by_name','collaborator']