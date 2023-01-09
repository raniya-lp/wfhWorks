from . import models
from projects.models import Projects
from generics import exceptions
from . import functions 
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from django.conf import settings
from users import models as user_model
from projects import models as prg_model
from . import serializers


def patten_creation(project_id,title,description,user):
    project=Projects.objects.filter(id=project_id).first()
    if project is None:
        raise exceptions.ExistsError("Project details doesn't exists")
    pattern_obj=models.Pattern.objects.filter(title__contains=title,project=project_id).first()
    if pattern_obj is  not None:
        raise exceptions.ExistsError("Pattern details already exists")
    pattern=models.Pattern.objects.create(project=project,title=title,description=description,created_by=user)

    # functions.pattern_subsection_creation(pattern_section,pattern)
    return pattern
    
def pattern_update(instance,title,description):
    if instance is None:
        raise exceptions.ExistsError("Pattern details does not exists")
    instance.title=title
    instance.description=description
    instance.save()

def pattern_section_update(instance,pattern_section_id,pattern_section):
    if instance is None:
        raise exceptions.ExistsError("Pattern details does not exists")
    pattern_section_obj=models.PatternSection.objects.filter(name__contains=pattern_section[0]["section"],pattern=instance.id).exclude(id=pattern_section_id).first()
    if pattern_section_obj is  not None:
        raise exceptions.ExistsError("Pattern section already exists")
    obj= models.PatternSection.objects.get(id=pattern_section_id)
    functions.pattern_subsection_creation(pattern_section,instance)
    instance.updated_at=datetime.now()
    instance.save()
    obj.delete()
     
def patten_add(pattern_id ,pattern_section):
    pattern_obj=models.Pattern.objects.get(id=pattern_id )
    if pattern_obj is  None:
        raise exceptions.ExistsError("Pattern dosen't exists")
    section_list=list(map(lambda x: x .get('section'), pattern_section))
    pattern_section_obj=models.PatternSection.objects.filter(name__in=section_list,pattern=pattern_id).first()
    if pattern_section_obj is  not None:
        raise exceptions.ExistsError("Pattern section already exists")
    functions.pattern_subsection_creation(pattern_section,pattern_obj)
    
def patten_font_upload(name ,file,generic,font_type,url):
    font_obj=models.PatternFont.objects.filter(name__contains=name).first()
    if font_obj is  not None:
        raise exceptions.ExistsError("Data already exists")
    if font_type =="file":
        fs = FileSystemStorage()
        now = datetime.now()
        dt_string = now.strftime("%d%m%Y%H%M%S")
        _file_name = file.name.split('.')
        filename = fs.save(f'{dt_string}.{_file_name[1]}', file)
        uploaded_file_url = fs.url(filename)
        file_path=f'{settings.SITE_ORIGIN}{uploaded_file_url}'
        models.PatternFont.objects.create(name=name,data_file_path=file_path,upload_flag=True,generic=generic,font_type=font_type)
    else:
        file_path=url
        models.PatternFont.objects.create(name=name,url=file_path,upload_flag=True,generic=generic,font_type=font_type)



def activity_notifications(request):
    user = request.user
    org_id = user_model.Role.objects.filter(user=request.user).first()
    if org_id.role == "admin":
        
        if org_id:
            org = org_id.organization.id
            org_users = user_model.Role.objects.filter(organization=org).values_list("user",flat=True)
            temp= []
            # print(list(org_users))
            # a=list(filter(lambda x: list(org_users).remove(x) if x == user.id else x, list(org_users)))
            # finl_list=list(filter(lambda x: x != user.id, list(org_users)))
            

            pattern = models.Pattern.objects.filter(project_id__in=prg_model.ProjectsOrganizationMapping.objects.filter(organization_id=org).values("project"))
            
            history = models.HistoricalPattern.objects.filter(history_user_id__in=org_users,project_id__in=pattern.values("project_id")).exclude(history_user_id=user.id)[:10]
            if history:
                    
                    serializer = serializers.PatternHistorySerializer(history,many=True)
            else:
                return "No Data"
    elif org_id.role == "superadmin":
            history = models.HistoricalPattern.objects.all()[:10]
            if history:
                    
                    serializer = serializers.PatternHistorySerializer(history,many=True)
            else:
                return "No Data"
        # for blueprint_obj in blueprint:
            
        #     history = blueprint_obj.history.filter(history_user_id__in=finl_list)
        #     if history:
        #         print(history)
        #         serializer = serializers.BlueprintHistorySerializer(history,many=True)
                
    
    
    return serializer.data



#For Pattern Creation

def creat_pattern(project_id,title,description,pattern_section,user,request):
    project=Projects.objects.filter(id=project_id).first()
    if project is None:
        raise exceptions.ExistsError("Project details doesn't exists")
    pattern_obj=models.Pattern.objects.filter(title__contains=title,project=project_id).first()
    if pattern_obj is  not None:
        raise exceptions.ExistsError("Pattern details already exists")
    pattern=models.Pattern.objects.create(project=project,title=title,description=description,section=pattern_section,created_by=user)

    # functions.pattern_subsection_creation(pattern_section,pattern)
    
    
    #For pattern notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=pattern.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)
        pattern_notif = list(map(lambda user: models.PatternNotification(pattern=pattern,action_user=request.user,action_type="create",org_user_id=user),final_user ))
        models.PatternNotification.objects.bulk_create(pattern_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
       
        pattern_notif = list(map(lambda user: models.PatternNotification(pattern=pattern,action_user=request.user,action_type="create",org_user_id=user), final_user))
        models.PatternNotification.objects.bulk_create(pattern_notif)
    # if models.PatternNotification.objects.filter(pattern=pattern,action_type="create",)
    return pattern
  

def update_pattern(instance,title,description,pattern_section,request):
    if instance is None:
        raise exceptions.ExistsError("Pattern details does not exists")
    instance.title=title
    instance.description=description
    instance.section = pattern_section
    instance.save()

    #Delete previous notification data

    delete_data  = models.PatternNotification.objects.filter(pattern=instance,action_type="update")
    delete_data.delete()


    #For pattern notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)

        pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance,action_user=request.user,action_type="update",org_user_id=user), final_user))
        models.PatternNotification.objects.bulk_create(pattern_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
       
        pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance,action_user=request.user,action_type="update",org_user_id=user), final_user))
        models.PatternNotification.objects.bulk_create(pattern_notif)



def patter_notifications(request):
    user = request.user
    org_id = user_model.Role.objects.filter(user=request.user).first()
    
    if org_id.role != "superadmin":

        pattern_notification = models.PatternNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        if pattern_notification:        
            serializer = serializers.PatternNotifcationSerializer(pattern_notification,many=True)
        else:
                return []
            
    elif org_id.role == "superadmin":
        
        history = models.PatternNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=request.user.id).order_by("-created_at")[:10]
        if history:
                
                serializer = serializers.PatternNotifcationSerializer(history,many=True)
        else:
            return []
    
    
    return serializer.data

