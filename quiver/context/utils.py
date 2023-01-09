import email
from os import access
from . import models
from projects.models import Projects
from .models import Canvas, CanvasMembers
from generics import exceptions
from django.core.files.storage import FileSystemStorage
from datetime import datetime , timedelta
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from users import models as user_models
from users import configurations
from users import functions
import threading
from projects import models as prg_models
from context import serializers
import base64

def create_user(new_member_user,organization,canvas_id,existing_list,request):
    user_list=[]
    member_list=[]
    user_role=[]
    user_access=[]
    profile_list=[]
    for i in new_member_user:
        user = models.User.objects.filter(username=i["email"]).first()
        if user is not None:
            existing_list.append({"email":i["email"],"id":user.id})
            #  raise exceptions.ExistsError("Email already exists.")
        else:
            password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)       
            user = user_models.User(first_name=i["first_name"], last_name=i["last_name"], username=i["email"], is_staff=False, is_superuser=False,is_active=False, password=password_hash)     
            members =models.CanvasMembers(canvas_id=canvas_id,user_id=user,count=0) 
            role=user_models.Role(user=user, organization=organization, role=user_models.Role.RoleName.user)
            access=user_models.UserAppMappping(user=user,app_id=4)
            profile = user_models.Profile(user=user)
            user_list.append(user) 
            user_role.append(role) 
            profile_list.append(profile)
            member_list.append(members)
            user_access.append(access)
            email_id=i["email"]
            email_bytes= email_id.encode("ascii")  
            base64_bytes= base64.b64encode(email_bytes)
            base64_email= base64_bytes.decode("ascii")
            email_args = {
                'full_name': f"{i['first_name']} {i['last_name']}".strip(),
                'email': i["email"],
                'password': password_str,
                'origin'  : f"{settings.USER_URL}{canvas_id}{'&key='}{base64_email}"
            }
           
            # Send Email as non blocking thread. Reduces request waiting time.      
            t = threading.Thread(target=functions.EmailService(email_args,[i['email'], ]).send_context_welcome_email)
            t.start()

    
    user_models.User.objects.bulk_create(user_list)
    user_models.Role.objects.bulk_create(user_role)
    user_models.Profile.objects.bulk_create(profile_list)
    user_models.UserAppMappping.objects.bulk_create(user_access)
    canvas_member = models.CanvasMembers.objects.bulk_create(member_list)
    #For canvas notificationorganization
    canvas_obj = models.Canvas.objects.filter(id=canvas_id).first()
    usr_lst = []        
    list(map(lambda user: usr_lst.append(user.user_id.id), canvas_member))

    if request.user.is_superuser:
        org_id = prg_models.ProjectsOrganizationMapping.objects.filter(project=canvas_obj.project).values_list('organization',flat = True).get()
        org_user_list = user_models.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)  
    else:
                
        organization = user_models.Role.objects.filter(user=request.user).first()
        org_user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)     
    
    super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)
    final_user = list(usr_lst) + list(super_admin_list) + list(org_user_list)

    final_user = [*set(final_user)]
    
    canvas_notif = list(map(lambda user: models.CanvasNotification(canvas_id=canvas_id,action_user=request.user,action_type="create",org_user_id=user), final_user))
    
    models.CanvasNotification.objects.bulk_create(canvas_notif)
    
    return Response(data={"created"},status=status.HTTP_201_CREATED)


def existing_user(canvas_id,existing_list,request):
    canvasmembers=[]
    for i in existing_list:

        check=models.CanvasMembers.objects.filter(canvas_id=canvas_id,user_id=i["id"]).first()
        if check is None:
            name=user_models.User.objects.filter(id=i["id"]).first()
            access=user_models.UserAppMappping.objects.filter(user_id=i["id"],app_id=4)
            if access is None:
                user_models.UserAppMappping.objects.create(user_id=i["id"],app_id=4)
            members =models.CanvasMembers(canvas_id=canvas_id,user_id_id=i["id"],count=0) 
            canvasmembers.append(members)   
            email_args = {
                   'full_name': f"{name.first_name} {name.last_name}".strip(),
                   'email'     : i['email'],
                   'url'       : f"{settings.USER_URL}{canvas_id}"

                 } 
               
            # Send Email as non blocking thread. Reduces request waiting time.
            
            t = threading.Thread(target=functions.EmailService(email_args, [i['email'], ]).send_invitation_email)
            t.start()
    result=models.CanvasMembers.objects.bulk_create(canvasmembers)
    canvas_obj = models.Canvas.objects.filter(id=canvas_id).first()
    #For canvas notificationorganization
    usr_lst = []   
      
    list(map(lambda user: usr_lst.append(user.user_id.id), result))

    if request.user.is_superuser:
        org_id = prg_models.ProjectsOrganizationMapping.objects.filter(project=canvas_obj.project).values_list('organization',flat = True).get()
        org_user_list = user_models.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)  
    else:
                
        organization = user_models.Role.objects.filter(user=request.user).first()
        org_user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)  
           
    
    super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)
    final_user = list(usr_lst) + list(super_admin_list) + list(org_user_list)

    final_user = [*set(final_user)]
    
    canvas_notif = list(map(lambda user: models.CanvasNotification(canvas_id=canvas_id,action_user=request.user,action_type="create",org_user_id=user), final_user))
    
    models.CanvasNotification.objects.bulk_create(canvas_notif)
    return Response(data={"created"},status=status.HTTP_201_CREATED)

def canvas_creation(project,title,description,user_type,canvas_type,user,user_list):
    project=Projects.objects.filter(id=project).first()

    if project is None:
        raise exceptions.ExistsError("Project details doesn't exists")
    canvas_obj= Canvas.objects.filter(title=title,project=project).first()  

    if canvas_obj is  not None:
        raise exceptions.ExistsError("Project details already exists")
    canvas=models.Canvas.objects.create(project=project,title=title,description=description,user_type=user_type,canvas_type_id=canvas_type,created_by=user,user_list=user_list)
    #canvas_id =canvas.id

    # #For canvas notificationorganization
    # if request.user.is_superuser:
    #     org_id = prg_models.ProjectsOrganizationMapping.objects.filter(project=canvas.project).values_list('organization',flat = True).get()
    #     org_user_list = user_models.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

    #     super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

    #     final_user = list(org_user_list) + list(super_admin_list)
    #     canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=canvas,action_user=request.user,action_type="create",org_user_id=user),final_user ))
    #     models.CanvasNotification.objects.bulk_create(canvas_notif)
    # else:
        
    #     organization = user_models.Role.objects.filter(user=request.user).first()
    #     user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin,user_models.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

    #     super_admin_list = user_models.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
    #     final_user = list(user_list) + list(super_admin_list)
       
    #     canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=canvas,action_user=request.user,action_type="create",org_user_id=user), final_user))
    #     models.CanvasNotification.objects.bulk_create(canvas_notif)

    return canvas

def canvas_update(canvas,title,description,request):
    # if canvas is None:
    #     raise exceptions.ExistsError("Project details does not exists")
    canvas.title=title
    canvas.description=description
    # canvas.user_type=user_type
    # canvas.canvas_type=canvas_type
    canvas.save()

    #Delete previous notification data

    delete_data  = models.CanvasNotification.objects.filter(canvas=canvas,action_type="update")
    delete_data.delete()


     #For canvas notificationorganization
    if request.user.is_superuser:
        org_id = prg_models.ProjectsOrganizationMapping.objects.filter(project=canvas.project).values_list('organization',flat = True).get()
        org_user_list = user_models.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)
        canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=canvas,action_user=request.user,action_type="update",org_user_id=user),final_user ))
        models.CanvasNotification.objects.bulk_create(canvas_notif)
    else:
        
        organization = user_models.Role.objects.filter(user=request.user).first()
        user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin,user_models.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_models.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
       
        canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=canvas,action_user=request.user,action_type="update",org_user_id=user), final_user))
        models.CanvasNotification.objects.bulk_create(canvas_notif)

def canvas_task_update(task,question,description,attachments):
    
    task.question=question
    task.description=description
    task.attachments=attachments
    task.save()

def notes_update (notes,answer,priority,colour):
    notes.answer=answer
    notes.priority_id=priority
    notes.colour=colour
    notes.save()
def count_update(member,count):
    member.count=count
    member.save()

def update_canvas_status(task):
    task.status=True
    task.save()
def create_userlist(user_list,organization,canvas_id,request):
    
    # new_member_user= user_list['new_member_user'] 
    # existing_list = user_list['existing_list']
    # if user_list.has_key('new_member_user'):
    if 'new_member_user' in user_list:
        new_member_user= user_list['new_member_user'] 
        if 'existing_list' in user_list:
            existing_list = user_list['existing_list']
            create_user(new_member_user,organization,canvas_id,existing_list,request)
        else:
            existing_list = []
            create_user(new_member_user,organization,canvas_id,existing_list,request)
            user_list["existing_list"] = existing_list
    if 'existing_list' in user_list:
        existing_list = user_list['existing_list']
        existing_user(canvas_id,existing_list,request)


def activity_notifications(request):
    user = request.user
    org_id = user_models.Role.objects.filter(user=request.user).first()
    if org_id.role == "admin":
        if org_id:
            org = org_id.organization.id
            # org_users = user_models.Role.objects.filter(organization=org).values_list("user",flat=True)
            canvas = models.Canvas.objects.filter(project_id__in=prg_models.ProjectsOrganizationMapping.objects.filter(organization_id=org).values("project"),created_by_id=request.user)
            canvas_members=models.CanvasMembers.objects.filter(canvas__in=canvas,updated_at__gte=datetime.now()-timedelta(hours=24)).values_list("user_id_id",flat=True)
            history = models.HistoricalCanvasMembers.objects.filter(history_user_id__in=canvas_members,count=1).exclude(history_user_id=user.id)
            if history:
                    serializer = serializers.CanvasMembersHistorySerializer(history,many=True)
            else:
                return "No Data"
    return serializer.data 


def context_notifications(request):
    user = request.user
    org_id = user_models.Role.objects.filter(user=request.user).first()
    if org_id.role != "superadmin":


        canvas_notification = models.CanvasNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        if canvas_notification:        
            serializer = serializers.CanvasNotifcationSerializer(canvas_notification,many=True)
        else:
                return []
            
    elif org_id.role == "superadmin":
            history = models.CanvasNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=request.user.id).order_by("-created_at")[:10]
            if history:
                    
                    serializer = serializers.CanvasNotifcationSerializer(history,many=True)
            else:
                return []
    
    
    return serializer.data
