from rest_framework import serializers
from . import models
from users import models as user_models
from projects import models as prg_model
from django.db.models import F


class CanvasProject(serializers.Serializer):
   project_id = serializers.UUIDField(format='hex',required=False)  
   org_id = serializers.UUIDField(format='hex',required=False)
   start_date = serializers.DateField(format="%d-%m-%Y",required=False)
   end_date = serializers.DateField(format="%d-%m-%Y",required=False)
   date_type = serializers.CharField(required=False)
class MembersListSerializer(serializers.Serializer): 
    email = serializers.EmailField(min_length=1, max_length=50, required=True)
    id = serializers.IntegerField(required=False)

class CreateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(min_length=2, max_length=50, required=True)
    last_name = serializers.CharField(min_length=1, max_length=50, required=True)  
    email = serializers.EmailField(min_length=8, max_length=100, required=True) 
# class UserListSerializer(serializers.Serializer):
#    existing_list =   MembersListSerializer(required=False)
#    new_member_user =  CreateUserSerializer(required=False)

class CanvasSerializers(serializers.Serializer):
   project = serializers.UUIDField(format='hex',required=True)
   title = serializers.CharField(min_length=3,max_length=100,required=True)
   description = serializers.CharField(min_length=1,required=False)
   user_type = serializers.CharField(required=True)
   canvas_type = serializers.IntegerField(required=True)
   user_list = serializers.JSONField(required=False)

class canvastaskListSerializer(serializers.ModelSerializer):
   class Meta:
      model=models.CanvasTask
      fields='__all__'

# class CanvasviewSerializers(serializers.ModelSerializer):
#    #   task=canvastaskListSerializer(many=True,required=False)
#      created_by =serializers.CharField(source='created_by.get_full_name')
#      memberlist=serializers.SerializerMethodField()
#      def get_memberlist(self,obj):
#         member=models.CanvasMembers.objects.filter(canvas_id=obj.id)
#         temp = []
#         for i in member:
#            id=i.id
#            temp.append({"id":id})
#         return temp
#      class Meta:
#         model = models.Canvas
#         fields = ['id','project','title','description','user_type','created_by','canvas_type','memberlist','task']    

class CanvasTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.CanvasType
        fields = ['id', 'name']

class CanvasListSerializers(serializers.ModelSerializer):
   def get_notification(self,obj):
        cmt_list = []
        user = self.context["user_id"]
        
        comt_hist = models.CanvasNotification.objects.filter(canvas=obj,action_type__in=["comment","reply"],org_user_id=user,higlight_status="unseen")
        total_count = len(comt_hist)
        return total_count

   def get_created_at(self, obj):
      return obj.created_at.strftime("%d/%m/%Y %H:%M %p")
   # def get_updated_at(self, obj):
   #      return obj.updated_at.strftime("%d/%m/%Y %H:%M %p")
   def get_updated_at(self,obj):
      notes=models.CanvasNotes.objects.filter(canvas_task__canvas_id=obj.id).order_by("-updated_at").first()
      if notes is None:
         return obj.updated_at.strftime("%d/%m/%Y %H:%M %p") 
      return notes.updated_at.strftime("%d/%m/%Y %H:%M %p")
   def get_status(self,obj):
         user = self.context["user_id"]
         role = user_models.Role.objects.get(user =user).role
         if role =='user':
            member=models.CanvasMembers.objects.filter(canvas_id=obj.id,user_id=user).first()
            if member:
               return member.count 
            else:
               return 1
         elif role == 'admin':
            member=models.CanvasMembers.objects.filter(canvas_id=obj.id,user_id=user).first()
            if member:
               return member.count
            else:
               return 1
         else:
            member=models.CanvasMembers.objects.filter(canvas_id=obj.id,count=0).first()
            if member is None:
               return 1
            return 0
   def get_collaborators(self,obj):
      user=models.CanvasMembers.objects.filter(canvas_id=obj.id).values(first_name=F('user_id__first_name'),last_name=F('user_id__last_name')).order_by('-created_at')[:3]
      return user 
   def get_cont(self,obj):
      user = self.context["user_id"]
      member=models.CanvasMembers.objects.filter(canvas_id=obj.id,user_id=user).first()

      if member is None:
         return 0
      notes=models.CanvasNotes.objects.filter(canvas_task_id__canvas_id=obj.id,created_by=user).first()    
      if  notes is None: 
         return 0

      if notes is not None and  member.count == 0:
         return 1  
      return 0
   def get_view_status(self,obj):
      user = self.context["user_id"]
      if models.CanvasShare.objects.filter(receiver=user):
         return True
      else:
         return False
         

   created_by =serializers.CharField(source='created_by.get_full_name')
   created_by_email =serializers.CharField(source='created_by.username')
   project=serializers.CharField(source='project.id')
   project_name=serializers.CharField(source='project.name')
   created_at = serializers.SerializerMethodField(method_name='get_created_at')
   updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
   flag_status = serializers.SerializerMethodField(method_name='get_status')
   notification_count = serializers.SerializerMethodField(method_name='get_notification')
   collaborators = serializers.SerializerMethodField(method_name='get_collaborators')
   continue_edite= serializers.SerializerMethodField(method_name='get_cont')
   shared_status = serializers.SerializerMethodField(method_name='get_view_status')

   
   class Meta:
        model = models.Canvas
        fields = ['id','project','title','description','user_type','status','collaborators','created_by_email','created_by','canvas_type','created_at','updated_at','flag_status','project_id','notification_count','continue_edite','shared_status','project_name']

class CanvasTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = models.CanvasType
        fields = ['id', 'name']

class CanvasUpdateSerializer(serializers.ModelSerializer):
     class Meta:
      model=models.Canvas
      # fields=['title','description','user_type','canvas_type']
      fields=['title','description']

class TasklistSerializer(serializers.Serializer):
   question = serializers.CharField(required=True)
   descriptionlist = serializers.CharField(allow_blank=True,required=False)
   attachments = serializers.JSONField(required=False)

class CanvasTaskSerializer(serializers.Serializer):
    canvas_id = serializers.UUIDField(format='hex', required=False)
    tasklist= TasklistSerializer(many=True,required=False)      

class CanvasTaskUpdateSerializer(serializers.ModelSerializer):
      class Meta:
         model=models.CanvasTask
         fields=['id','question','description','attachments']

class CanvasPrioritySerializer(serializers.ModelSerializer):
   class Meta:
      model=models.Priority
      fields=['name','id']

class CanvasAnswer(serializers.Serializer):
   notes = serializers.CharField(min_length=1,required=False,error_messages={"detail": 'Ensure this field has at least 1 characters.'})
   priority = serializers.IntegerField(required=True)
   colour = serializers.CharField(min_length=1,required=False,error_messages={"detail": 'Ensure this field has at least 1 characters.'})
   # created_by =serializers.CharField(source='created_by.get_full_name')

class CanvasNotesSerializers(serializers.Serializer):
   notes = serializers.CharField(min_length=1,required=False)
   priority = serializers.IntegerField(required=True)
   colour = serializers.CharField(min_length=1,required=False)
   
class CanvasQuestion(serializers.Serializer):
   canvas_task = serializers.UUIDField(format='hex', required=False)
   answer = CanvasAnswer(many=True,required=False)

class CanvasNotes(serializers.Serializer):
   canvas = serializers.UUIDField(format='hex', required=False)
   question_list=CanvasQuestion(many=True,required=True)
   


class CanvasMemberSerializer(serializers.Serializer):
   canvas_id = serializers.UUIDField(format='hex', required=False)
   existing_list= MembersListSerializer(many=True,required=False)
   new_member_user= CreateUserSerializer(many=True,required=False)

class TaskviewSerializers(serializers.ModelSerializer):
   class Meta:
      model = models.CanvasTask
      fields=['id','question','description','attachments']

class CanvasDeleteSerializer(serializers.Serializer):
    canvas_id = serializers.CharField(required=True)
 

class NotesSerializer(serializers.ModelSerializer):
   id = serializers.CharField(required=True)
   question =serializers.CharField(source='canvas_task')
   description=serializers.CharField(source='canvas_task.description')
   # attachments=serializers.JSONField(source='canvas_task.attachments')
   created_by =serializers.CharField(source='created_by.get_full_name')
   class Meta:
      model=models.CanvasNotes
      fields=['canvas_task','question','description','id','answer','colour','created_by']
      
class TaskSerializer(serializers.ModelSerializer):
      def get_task(self,obj):
         task_object=models.CanvasNotes.objects.filter(priority=obj.id,canvas_task__canvas=self.context["canvas"])
         note_list= NotesSerializer(task_object,many=True, read_only=True,context={'canvas':obj}).data
         return note_list
      task_list = serializers.SerializerMethodField(method_name='get_task')
      class Meta:
         model=models.Priority
         fields=['id','name','task_list']

class CanvasSingleGetSerializer(serializers.ModelSerializer):

   def get_priority_list(self,obj):
      p_object=models.Priority.objects.filter(canvas_type=obj.canvas_type)
      s_object= TaskSerializer(p_object,many=True, read_only=True,context={'canvas':obj}).data
      return s_object
   def get_status(self,obj):
      if obj.user_type=='s':
         return {}
      percentage=0
      completed=models.CanvasMembers.objects.filter(canvas_id=obj.id,count=1).count()
      pending=models.CanvasMembers.objects.filter(canvas_id=obj.id,count=0).count()
      if pending==0:
         status="Completed"
      else:
         status="In Progress"
      total=completed + pending
      if total==0:
         percentage=0
      else:
         percentage=completed/total*100
      return {"completed":completed,"pending":pending,"status":status,"percentage":percentage}
   def get_member_list(self,obj):
      member=models.CanvasMembers.objects.filter(canvas_id=obj.id)
      temp = []
      for i in member:
         first=i.user_id.first_name
         last=i.user_id.last_name
         image = user_models.Profile.objects.get(user_id=i.user_id_id).image
         temp.append({"first_name":first,"last_name":last,"image":image})
      return temp
   def get_assigned_to(self,obj):

      user = obj.created_by
      usr = models.User.objects.filter(id=user.id).first()
      image = user_models.Profile.objects.get(user_id=user.id).image
      role =user_models.Role.objects.get(user_id=user.id).role
      if usr:
         return({"first_name":usr.first_name ,"last_name":usr.last_name,"role":role,"image":image}) 
      else:
         return "NA"
   def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"     
   def get_task_count(self,obj):
      canva= models.CanvasTask.objects.filter(canvas_id=obj.id).count()
      return canva
   title = serializers.CharField(min_length=3,max_length=100,required=True)
   description = serializers.CharField(min_length=1,required=False)
   created_by =serializers.CharField(source='created_by.get_full_name')
   # created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
   # updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
   user_type = serializers.CharField(required=True)
   canvas_type_id=serializers.IntegerField(required=True)
   canvas_type = serializers.CharField(required=True)
   priority_list = serializers.SerializerMethodField(method_name='get_priority_list')
   members_list = serializers.SerializerMethodField(method_name='get_member_list')
   status_details = serializers.SerializerMethodField(method_name='get_status')
   assigned_by=serializers.SerializerMethodField(method_name='get_assigned_to')
   canvas_id = serializers.UUIDField(source='id')
   project_name=serializers.CharField(source='project.name')
   organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
   task_count = serializers.SerializerMethodField(method_name='get_task_count')
   
   class Meta:
       model=models.Canvas
       fields=['canvas_id','title','description','project','project_name','created_by','created_at','updated_at','user_type','canvas_type_id','canvas_type','assigned_by','priority_list','members_list','status_details','organization_data','task_count']

class UserSpecificAnswerNotes(serializers.ModelSerializer):
   def get_answer(self,obj):
         task_object=models.CanvasNotes.objects.filter(priority_id=obj.priority_id,canvas_task_id=obj.canvas_task_id,created_by=self.context["user"])
         answer_lists= Notes(task_object,many=True, read_only=True,context={'canvas':obj}).data
         return answer_lists

   canvas_task_id = serializers.UUIDField(format='hex',required=True)
   question =serializers.CharField(source='canvas_task')
   description=serializers.CharField(source='canvas_task.description')
   attachments=serializers.JSONField(source='canvas_task.attachments')
   created_by =serializers.CharField(source='created_by.get_full_name')
   # answer_list = serializers.SerializerMethodField(method_name='get_answer')

   class Meta:
      model=models.CanvasNotes
      fields=['canvas_task_id','question','description','attachments','id','answer','colour','created_by']
      

class TasksSerializer(serializers.ModelSerializer):
      def get_task(self,obj):
         user = self.context["user"]
         task_object=models.CanvasNotes.objects.filter(priority=obj.id,canvas_task__canvas=self.context["canvas"],created_by=user)
         note_list= UserSpecificAnswerNotes(task_object,many=True, read_only=True,context={'canvas':obj,'user':user}).data
         return note_list
      task_list = serializers.SerializerMethodField(method_name='get_task')
      class Meta:
         model=models.Priority
         fields=['id','name','task_list']
   

class CanvasViewSerializer(serializers.ModelSerializer):
    
   def get_count(self,obj):

      user = self.context["user"]
      question = models.CanvasTask.objects.filter(canvas_id=obj.id).count()
      answer = models.CanvasNotes.objects.filter(canvas_task__canvas_id=obj.id,created_by=user.id).values('canvas_task').distinct().count()
      percentage=(answer/question)*100
      return ({"total":question,"answered":answer,"percentage":percentage})

   def get_priority_list(self,obj):

      user = self.context["user"]
      p_object=models.Priority.objects.filter(canvas_type=obj.canvas_type)
      s_object= TasksSerializer(p_object,many=True, read_only=True,context={'canvas':obj,'user':user}).data
      
      return s_object
   def get_assigned_to(self,obj):

      user = obj.created_by
      usr = models.User.objects.filter(id=user.id).first()
      image = user_models.Profile.objects.get(user_id=user.id).image
      if usr:
         return({"first_name":usr.first_name ,"last_name":usr.last_name,"image":image}) 
      else:
         return "NA"
   def get_member_list(self,obj):
      member=models.CanvasMembers.objects.filter(canvas_id=obj.id)
      temp = []
      for i in member:
         first=i.user_id.first_name
         last=i.user_id.last_name
         image = user_models.Profile.objects.get(user_id=i.user_id_id).image
         temp.append({"first_name":first,"last_name":last,"image":image})
      return temp     
   def get_organization_data(self, obj):
        org = prg_model.ProjectsOrganizationMapping.objects.filter(project=obj.project).first()
        if org:
            return {"org_id":org.organization.id,"org_name":org.organization.name}
        else:
            return "NA"    
   title = serializers.CharField(min_length=3,max_length=100,required=True)
   description = serializers.CharField(min_length=1,required=False)
   created_by =serializers.CharField(source='created_by.get_full_name')
   user_type = serializers.CharField(required=True)
   canvas_type_id=serializers.IntegerField(required=True)
   canvas_type = serializers.CharField(required=True)
   priority_list = serializers.SerializerMethodField(method_name='get_priority_list')
   assigned_by=serializers.SerializerMethodField(method_name='get_assigned_to')
   members_list = serializers.SerializerMethodField(method_name='get_member_list')
   task_count = serializers.SerializerMethodField(method_name='get_count')
   project_name=serializers.CharField(source='project.name')
   organization_data = serializers.SerializerMethodField(method_name='get_organization_data')
   class Meta:
      model=models.Canvas
      fields=['title','description','created_by','user_type','task_count','canvas_type_id','canvas_type','priority_list','members_list','assigned_by','project','project_name','organization_data']

class CanvasViewsSerializer(serializers.Serializer):
    canvas_id = serializers.CharField(required=False)
    user_id=serializers.IntegerField(required=False)
class ProfileSeria(serializers.ModelSerializer):
   user_name = serializers.CharField(source='user.get_full_name')
   class Meta:
      model=user_models.Profile
      fields=['user_name' ,'image']
class Notes(serializers.ModelSerializer):
   # question =serializers.CharField(source='canvas_task')
   # description=serializers.CharField(source='canvas_task.description')
   # attachments=serializers.JSONField(source='canvas_task.attachments')
   priority=serializers.IntegerField(source='priority.id')
   priority_name =serializers.CharField(source='priority.name')
   notes = serializers.CharField(source='answer')
   # created_by = serializers.CharField(source='created_by.get_full_name')
   created_by = ProfileSeria(source='created_by.user_prf',many=True)
   class Meta:
      model=models.CanvasNotes
      fields=['id','notes','colour','created_by','priority','priority_name']

      
class AnswerNotes(serializers.ModelSerializer):
   def get_answer(self,obj):
         task_object=models.CanvasNotes.objects.filter(priority_id=obj.priority_id,canvas_task_id=obj.canvas_task_id)
         answer_lists= Notes(task_object,many=True, read_only=True,context={'canvas':obj}).data
         return answer_lists

   canvas_task_id = serializers.UUIDField(format='hex',required=True)
   question =serializers.CharField(source='canvas_task')
   description=serializers.CharField(source='canvas_task.description')
   attachments=serializers.JSONField(source='canvas_task.attachments')
   created_by = serializers.CharField(source='created_by.get_full_name')
   # answer_list = serializers.SerializerMethodField(method_name='get_answer')

   class Meta:
      model=models.CanvasNotes
      fields=['canvas_task_id','question','description','attachments','id','answer','colour','created_by']


class TaskListSerializer(serializers.ModelSerializer):
      def get_task(self,obj):
         task_object=models.CanvasNotes.objects.filter(priority=obj.id,canvas_task__canvas=self.context["canvas"])
         note_list= AnswerNotes(task_object,many=True, read_only=True,context={'canvas':obj}).data
         return note_list
      task_list = serializers.SerializerMethodField(method_name='get_task')
      class Meta:
         model=models.Priority
         fields=['id','name','task_list']

class CanvasInfoSerializer(serializers.ModelSerializer):

   def get_priority_list(self,obj):
      p_object=models.Priority.objects.filter(canvas_type=obj.canvas_type)
      s_object= TaskListSerializer(p_object,many=True, read_only=True,context={'canvas':obj}).data
      return s_object
   def get_status(self,obj):
      if obj.user_type=='s':
         return {}
      percentage=0
      completed=models.CanvasMembers.objects.filter(canvas_id=obj.id,count=1).count()
      pending=models.CanvasMembers.objects.filter(canvas_id=obj.id,count=0).count()
      if pending==0:
         status="Completed"
      else:
         status="In Progress"
      total=completed + pending 
      if total==0:
         percentage=0
      else:
         percentage=completed/total*100
      return {"completed":completed,"pending":pending,"status":status,"percentage":percentage}
   def get_member_list(self,obj):
      member=models.CanvasMembers.objects.filter(canvas_id=obj.id)
      temp = []
      for i in member:
         user=i.user_id.id
         first=i.user_id.first_name
         last=i.user_id.last_name
         name=first+" "+last
         temp.append({"user_name":name,"user_id":user})
      return temp

   title = serializers.CharField(min_length=3,max_length=100,required=True)
   description = serializers.CharField(min_length=1,required=False)
   created_by =serializers.CharField(source='created_by.get_full_name')
   user_type = serializers.CharField(required=True)
   canvas_type_id=serializers.IntegerField(required=True)
   canvas_type = serializers.CharField(required=True)
   priority_list = serializers.SerializerMethodField(method_name='get_priority_list')
   members_list = serializers.SerializerMethodField(method_name='get_member_list')
   status_details = serializers.SerializerMethodField(method_name='get_status')
   
   class Meta:
       model=models.Canvas
       fields=['title','description','created_by','user_type','canvas_type_id','canvas_type','priority_list','members_list','status_details']


class CanvasTasksListSerializer(serializers.ModelSerializer):
      def get_answer(self,obj):
         user = self.context["user"]
         task_object=models.CanvasNotes.objects.filter(canvas_task_id=obj.id,created_by=user)
         answers= Notes(task_object,many=True, read_only=True,context={'canvas':obj}).data
         return answers
      task_list= serializers.SerializerMethodField(method_name='get_answer')
      class Meta:
         model=models.CanvasTask
         fields=['id','question','description','attachments','task_list']


class CanvasMembersHistorySerializer(serializers.ModelSerializer):
     
     history_type = serializers.SerializerMethodField()
     canvas=serializers.CharField(source='canvas.title',required=True)
     updated_by = serializers.CharField(source='history_user.get_full_name')
     updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    
     class Meta:
       model =   models.HistoricalCanvasMembers
       fields = ["id","canvas","history_type","created_at","history_user","history_id","updated_by","updated_at"]

     def get_history_type(self,obj):
      hist_type = obj.history_type
      if hist_type == "+":
         history_type = "Created"
      elif hist_type == "~":
         history_type = "Updated"
      elif hist_type == "-":
         history_type = "Deleted"
      return history_type


#For canvas Notification


class CanvasNotifcationSerializer(serializers.ModelSerializer):
     def get_project_name(self, obj):
        
        if obj.action_type == "product_create" or obj.action_type == "product_update":
            
            return obj.product.name
        else:
            
            return obj.canvas.project.name
     
   #   project_name = serializers.CharField(source='canvas.project.name',allow_null=True)
     project_name = serializers.SerializerMethodField(method_name='get_project_name')
     canvas_id = serializers.CharField(source='canvas.id',allow_null=True)
     canvas_name = serializers.CharField(source='canvas.title',allow_null=True)
     created_by = serializers.CharField(source='action_user.get_full_name')
     updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    
     class Meta:
       model =   models.CanvasNotification
       fields = ["id","project_name","canvas_id","canvas_name","action_type","created_by","created_at","updated_at","action_status","higlight_status","comment","reply"]

class ContextNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )

#For canvas Document Share

class CanvasDocumentShareSerializer(serializers.ModelSerializer):
    
    
    receiver_id = serializers.IntegerField(required=True)
    canvas_id= serializers.UUIDField(format='hex', required=True)
    message = serializers.CharField(required=False,allow_blank=True)
    class Meta:
        model =   models.CanvasShare
        fields = ["canvas_id","receiver_id","message"]



#canvas Comments serializer
class CommentSectionSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, max_length=1000)
    body = serializers.CharField(required=True, max_length=3000)
    tags = serializers.ListField(
        child=serializers.CharField(required=False)
    )

class CanvasCommentSerializer(serializers.ModelSerializer):
    canvas_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.CanvasComments
        fields = ["canvas_id","comments","attachments"]


class CanvasReplyListSerializer(serializers.ModelSerializer):
    canvas_comment_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
   #  user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")


    class Meta:
        model =   models.CanvasCommentsReply
        fields = ["id","canvas_comment_id","first_name","last_name","user_id","comments","created_at","updated_at","attachments"]


class CanvasCommentListSerializer(serializers.ModelSerializer):
    canvas_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
   #  user_name = serializers.CharField(source="user.get_full_name")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)
    reply = CanvasReplyListSerializer(many=True)
    updated_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")
    created_at = serializers.DateTimeField(format="%d-%m-%Y %I:%M %p")

    class Meta:
        model =   models.CanvasComments
        fields = ["id","canvas_id","first_name","last_name","user_id","comments","created_at","updated_at","attachments","reply"]


class CanvasReplySerializer(serializers.ModelSerializer):
    canvas_comment_id = serializers.UUIDField()
    # user_id = serializers.IntegerField()
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.CanvasCommentsReply
        fields = ["canvas_comment_id","comments","attachments"]


class CanvasCommentUpdateSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.CanvasComments
        fields = ["comments","attachments"]

class CanvasReplyUpdationSerializer(serializers.ModelSerializer):
    
    # comments = serializers.CharField(required=True, max_length=3000)
    comments = CommentSectionSerializer()
    attachments = serializers.JSONField(required=False)


    class Meta:
        model =   models.CanvasCommentsReply
        fields = ["comments","attachments"]

class CanvasFilterSerializer(serializers.Serializer):
    
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")
    date_type = serializers.CharField(required=True)

class CanvasFilterListSerializer(serializers.ModelSerializer):
    
    created_by_name = serializers.CharField(source='created_by.get_full_name')
    created_by_email =serializers.CharField(source='created_by.username')
    project = serializers.CharField(source='project.id')
    project_name = serializers.CharField(source='project.name')
    updated_at = serializers.DateTimeField(format="%d-%m-%Y")
    created_at = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        model = models.Canvas
        fields = ['id','project','project_name','title','description','status','user_type','created_by','created_by_name','created_by_email','canvas_type','created_at','updated_at']

class CanvasTaskNotesSerializer(serializers.ModelSerializer):
   priority_name =serializers.CharField(source='priority.name')
   created_by = ProfileSeria(source='created_by.user_prf',many=True)
   class Meta:
      model=models.CanvasNotes
      fields=['id','answer','colour','created_by','priority','priority_name']


class CanvasNotifcationStatusSerializer(serializers.Serializer):
     
     
    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )
