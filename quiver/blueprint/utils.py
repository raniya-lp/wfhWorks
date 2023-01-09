from pyexpat import model

from blueprint import serializers
from . import models
from projects.models import Projects
from generics import exceptions
#from . import functions 
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from django.conf import settings
import datetime as dt

from projects import models as prg_model
from users import models as user_model

def blueprint_creation(project_id,title,description,user,created_by,updated_by,request,blueprint_details):
    project=Projects.objects.filter(id=project_id).first()
    if project is None:
        raise exceptions.ExistsError("Project details doesn't exists")
    blueprint_obj=models.BluePrint.objects.filter(title__contains=title,project=project_id,description=description,created_by=created_by,updated_by=updated_by).first()
    if blueprint_obj is  not None:
        raise exceptions.ExistsError("Blueprint details already exists")
    blueprint=models.BluePrint.objects.create(project=project,title=title,description=description,created_by=user,updated_by=user,blueprint_details=blueprint_details)
    blueprint_id=blueprint.id


    #For blueprint notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=blueprint.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)
        blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=blueprint,action_user=request.user,action_type="create",org_user_id=user),final_user ))
        models.BluePrintNotification.objects.bulk_create(blueprint_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
       
        blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=blueprint,action_user=request.user,action_type="create",org_user_id=user), final_user))
        models.BluePrintNotification.objects.bulk_create(blueprint_notif)
    return blueprint_id



def section_creation(blueprint_id ,name,subline_text,process_item_id,data,created_by,user):
    blueprint_obj=models.BluePrint.objects.get(id=blueprint_id )
    if blueprint_obj is  None:
        raise exceptions.ExistsError("Blueprint dosen't exists")
    blueprint_obj=models.Sections.objects.filter(blue_print=blueprint_id,name=name,subline_text=subline_text,process_item_id=process_item_id,data=data,created_by=created_by).first()
    if blueprint_obj is  not None:
        raise exceptions.ExistsError("Section details already exists")
    section_create=models.BluePrint.objects.create(blue_print=blueprint_id,name=name,subline_text=subline_text,process_item_id=process_item_id,data=data,created_by=user)
   



def blueprint_updation(project_id,title,description,user,request,blueprint_details):    
    if project_id is not None:
        update_time = datetime.now()
        project_id.title=title
        project_id.description=description
        project_id.updated_by=user
        project_id.updated_at=update_time
        project_id.blueprint_details=blueprint_details
        project_id.save()

        #Delete previous notification data

        delete_data  = models.BluePrintNotification.objects.filter(blueprint=project_id,action_type="update")
        delete_data.delete()

        #For blueprint notificationorganization
        if request.user.is_superuser:
            org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=project_id.project).values_list('organization',flat = True).get()
            org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

            super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

            final_user = list(org_user_list) + list(super_admin_list)
            blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=project_id,action_user=request.user,action_type="update",org_user_id=user),final_user ))
            models.BluePrintNotification.objects.bulk_create(blueprint_notif)
        else:
            
            organization = user_model.Role.objects.filter(user=request.user).first()
            user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

            super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
            
            final_user = list(user_list) + list(super_admin_list)
        
            blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=project_id,action_user=request.user,action_type="update",org_user_id=user), final_user))
            models.BluePrintNotification.objects.bulk_create(blueprint_notif)

def section_updation(project_id,processdata,user):    
    if project_id is not None:
        for prd in processdata:
            update_time = dt.datetime.now()
            name = prd['name']
            subline_text = prd['subline_text']
            process_item_id = prd['process_item_id']
            data = prd['data']
            blueprint_id =  project_id
            section = models.Sections.objects.filter(blue_print=blueprint_id,process_item_id=process_item_id).update(name=name,subline_text=subline_text,process_item_id=process_item_id,data=data)


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
            

            blueprint = models.BluePrint.objects.filter(project_id__in=prg_model.ProjectsOrganizationMapping.objects.filter(organization_id=org).values("project"))
            
            history = models.HistoricalBluePrint.objects.filter(history_user_id__in=org_users,project_id__in=blueprint.values("project_id")).exclude(history_user_id=user.id)[:10]
            if history:
                    
                    serializer = serializers.BlueprintHistorySerializer(history,many=True)
            else:
                return "No Data"
    elif org_id.role == "superadmin":
            history = models.HistoricalBluePrint.objects.all()[:10]
            if history:
                    
                    serializer = serializers.BlueprintHistorySerializer(history,many=True)
            else:
                return "No Data"
        # for blueprint_obj in blueprint:
            
        #     history = blueprint_obj.history.filter(history_user_id__in=finl_list)
        #     if history:
        #         print(history)
        #         serializer = serializers.BlueprintHistorySerializer(history,many=True)
                
    
    
    return serializer.data


def blueprint_notifications(request):
    user = request.user
    org_id = user_model.Role.objects.filter(user=request.user).first()
    if org_id.role != "superadmin":


        blueprint_notification = models.BluePrintNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        if blueprint_notification:        
            serializer = serializers.BluePrintNotifcationSerializer(blueprint_notification,many=True)
        else:
               return []
            
    elif org_id.role == "superadmin":
            history = models.BluePrintNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=request.user.id).order_by("-created_at")[:10]
            if history:
                    
                    serializer = serializers.BluePrintNotifcationSerializer(history,many=True)
            else:
               return []
    
    
    return serializer.data