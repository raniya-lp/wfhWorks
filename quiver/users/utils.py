from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.utils import timezone
import threading
import datetime
import pytz
from generics import exceptions
from . import functions
from . import configurations
from . import models
from . import serializers
import projects.models as project_models
import jwt
import base64  

def time_conversion(time):
    return timezone.localtime(time, pytz.timezone(settings.CENTRAL_TIME_ZONE))

def blacklist_token(refresh: str) -> None:
    try:
        token = RefreshToken(refresh)
        token.blacklist()
        return True
    except:
        return False

def get_user_info(user_id: int) -> dict:
    user = functions.get_user_by_id(id=user_id)
    if user is None:
        return False
    return functions.user_info(user)

def create_enterprise_user(first_name: str, last_name: str, email: str, phone:int, role: str,access_list) -> bool:
    password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
    user = models.User.objects.filter(username=email)
    if user.exists():
        raise exceptions.ExistsError("Email already exists")
    ce = functions.create_enterprise_user(first_name, last_name, email, phone, password_hash, role,access_list)
    if not ce:
        return False
    email_bytes= email.encode("ascii")  
    base64_bytes= base64.b64encode(email_bytes)
    base64_email= base64_bytes.decode("ascii")
    email_args = {
        'full_name' : f"{first_name} {last_name}".strip(),
        'email'     : email,
        'password'  : password_str,
        'origin'    : f"{settings.SITE_ORIGIN}{base64_email}"
    }
    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, [email, ]).send_welcome_email)
    t.start()
    return True

def list_super_user():
    users = models.User.objects.filter(is_staff=True)
    return serializers.SuperUserListModelSerializer(users, many=True).data

def password_reset_done(key: str, password: str) -> bool:
    password = password.strip()
    decrypted_message = functions.CryptoGraphy().crypto_decrypt_msg(key)
    if decrypted_message is None:
        return False

    data_list = decrypted_message.split('||')
    if len(data_list) < 3:
        return False

    email, date_string, user_id = data_list
    url_generated_time  = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")
    current_time        = datetime.datetime.now()
    is_greater_15_mins: bool = functions.is_time_greater_15_mins(current_time=current_time, url_generated_time=url_generated_time)

    if is_greater_15_mins:
        return False

    return functions.update_password(user_id=user_id, email=email, password=password)

def password_reset_email(email: str) -> bool:
    password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
    email = email.strip()
    # user  = functions.get_user_by_email(email=email)
    user = models.User.objects.filter(username=email).first()
    if user is None:
        return False
    user.password = password_hash
    user.save()
    message = f"{email}||{datetime.datetime.now()}||{user.id}"
    encrypted_message = functions.CryptoGraphy().crypto_encrypt_msg(data_string=message)

    # email_args = {
    #     'full_name': user.get_full_name(),
    #     'url': f"{settings.SITE_ORIGIN}/{configurations.CHANGE_PASSWORD_BROWSER_URL}?key={encrypted_message}",
    # }
    email_args = {
        'full_name' : user.get_full_name(),
        'email'     : email,
        'password'  : password_str,
        'origin'    : settings.SITE_ORIGIN,
    }

    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, [email, ]).send_password_reset_email)
    t.start()
    return True


def update_user(user, first_name: str, last_name: str, phone: int, email: str) -> None:
    username = models.User.objects.filter(username=email).exclude(id=user.id)
    if username.exists():
        # raise exceptions.ExistsError("Email already exists.")
        return False
    profile = models.Profile.objects.filter(user=user).update(phone=phone)
    if profile == 0: models.Profile.objects.create(user=user,phone=phone)
    models.User.objects.filter(id=user.id).update(first_name=first_name,last_name=last_name,username=email)
    return True
def admin_user_update(org_id,org_name,first_name,last_name,phone,email,access_list,project_list,pk,creator,project_creationlist):
    user = models.User.objects.filter(id=pk)
    if user.first() is None:
        raise exceptions.ExistsError("User details doesn't exists")
    queryset =project_models.Projects.objects.filter(name__in=project_creationlist)
    if queryset.exists():
        raise exceptions.ExistsError("project already exists.")
    user_obj=models.User.objects.filter(username=email).exclude(id=pk)
    if user_obj.count()!=0:
        raise exceptions.ExistsError("Email details already exist")
    profile = models.Profile.objects.filter(user=pk)
    models.Profile.objects.create(user=user,phone=phone)if profile == 0  else profile.update(phone=phone)
    user.update(first_name=first_name,last_name=last_name,username=email)
    models.UserAppMappping.objects.filter(user=user).delete()
    bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
    ]
    models.UserAppMappping.objects.bulk_create(bulk_app_access)
    role_obj=models.Role.objects.filter(user=pk)
    # role_obj.update(roadmap_access=roadmap_access,pattern_access=pattern_access,context_access=context_access,blueprint_access=blueprint_access)
    if org_id is None:
        return True
    else:
        org_obj = models.Organization.objects.filter(id=org_id)
        org_obj.update(name=org_name)

    project_models.ProjectsOrganizationMapping.objects.filter(organization=org_id).delete()

    bulk_project = [
       project_models.Projects(name=i,created_by=creator) for i in project_creationlist
    ]
    project_creation=project_models.Projects.objects.bulk_create(bulk_project)
    bulk_project_creation = [
        project_models.ProjectsOrganizationMapping(organization=role_obj.first().organization, project=i,created_by=creator) for i in project_creation
    ]
    bulk_project_mapping = [
        project_models.ProjectsOrganizationMapping(organization=role_obj.first().organization, project=project_models.Projects.objects.filter(id=i).first(),created_by=creator) for i in project_list
    ]
    project_models.ProjectsOrganizationMapping.objects.bulk_create(bulk_project_mapping)
    project_models.ProjectsOrganizationMapping.objects.bulk_create(bulk_project_creation)
def delete_user(user_id):
    user = functions.get_user_by_id(id=user_id)
    models.Profile.objects.filter(user=user).delete()
    models.UserAppMappping.objects.filter(user=user).delete()
    user.delete()


def create_organization_admin(creator, first_name: str, last_name: str, name: str, email: str, phone: int,access_list :list,project_creationlist: list):
    password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
    user = models.User.objects.filter(username=email)
    queryset =project_models.Projects.objects.filter(name__in=project_creationlist)
    if queryset.exists():
        raise exceptions.ExistsError("project already exists.")
    if user.exists():
        raise exceptions.ExistsError("Email already exists.")
    functions.create_organization(creator, first_name, last_name , name, email, phone, password_hash,access_list ,project_creationlist)

    email_args = {
        'full_name': f"{first_name} {last_name}".strip(),
        'email': email,
        'password': password_str,
        'origin': settings.SITE_ORIGIN,
    }

    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, [email, ]).send_welcome_email)
    t.start()


def get_user_by_id(id: int, active: bool = True):
    return models.User.objects.filter(id=id).first()


def get_user_by_id_email(id: int, email: str, active: bool = True):
    return models.User.objects.filter(id=id, username=email, is_active=active)


def update_password(user_id: int, email: str, password: str) -> bool:
    users = get_user_by_id_email(id=user_id, email=email)

    if users.first() is None:
        raise exceptions.NotExistsError(message="User account does not exist.")
   
    password_hash = make_password(password)
    users.update(password=password_hash)
    return True


def change_password(user_id: int, email: str, old_password: str, new_password: str) -> bool:
    user = get_user_by_id(id=user_id)
    if user is None:
        raise exceptions.NotExistsError(message="User account does not exist.")
    if not check_password(password=old_password, encoded=user.password):
        return False
    return update_password(user_id=user_id, email=email, password=new_password)

def get_current_orgainzation(user_id: int):
    organization_role = models.Role.objects.filter(user__id=user_id).first()
    if organization_role is None:
        return organization_role
    return organization_role.organization

def get_current_org_role(user_id: int):
    organization_role = models.Role.objects.filter(user__id=user_id).first()
    if organization_role is None:
        return organization_role
    return organization_role

def create_user(first_name: str, last_name: str, organization, email: str, phone: int, role: str,access_list:list):
    if organization is None:
        create_enterprise_user(first_name, last_name, email, phone, role,access_list)
    else:
        create_org_user(first_name, last_name, organization, email, phone, role,access_list)

def create_org_user(first_name: str, last_name: str, organization, email: str, phone: int, role: str,access_list:list):
    password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
    user = models.User.objects.filter(username=email)
    if user.exists():
        raise exceptions.ExistsError("Email already exists.")

    functions.create_organization_user(first_name, last_name , email, phone, password_hash, role, organization,access_list)
    email_bytes= email.encode("ascii")  
    base64_bytes= base64.b64encode(email_bytes)
    base64_email= base64_bytes.decode("ascii")
    email_args = {
        'full_name': f"{first_name} {last_name}".strip(),
        'email': email,
        'password': password_str,
        'origin': f"{settings.SITE_ORIGIN}{base64_email}"
    }
    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, [email, ]).send_welcome_email)
    t.start()

def update_user_org_role(user, organization, role, access_list ) -> None:
    if role == 'superadmin':
        models.User.objects.filter(id=user.id).update(is_staff = True,is_superuser = True)
        
        # user.is_staff = True
        # user.is_superuser = True
        # user.save()
        models.Role.objects.filter(user=user).update(organization=None, role=role)
        models.UserAppMappping.objects.filter(user=user).delete()
        bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
        ] 
        models.UserAppMappping.objects.bulk_create(bulk_app_access)
    else:
        models.User.objects.filter(id=user.id).update(is_staff = False,is_superuser = False)
        # user.is_staff = False
        # user.is_superuser = False
        # user.save()
        models.Role.objects.filter(user=user).update(organization=organization, role=role)
        models.UserAppMappping.objects.filter(user=user).delete()
        bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
        ] 
        models.UserAppMappping.objects.bulk_create(bulk_app_access)

def update_user_role(user, role) -> None:
    models.Role.objects.filter(user=user).update(role=role)

def activity_notifications_to_collaborator():
    last_24_hours = (datetime.datetime.now() - datetime.timedelta(hours=24)).replace(tzinfo=pytz.UTC)
    organizations = models.Organization.objects.all()
    final_args=[]
    for organization in organizations:
        # products = project_models.Projects.objects.filter(organization=organization,created_at__gte=last_24_hours)
        products = project_models.ProjectsOrganizationMapping.objects.filter(organization=organization,created_at__gte=last_24_hours)
        if products.count()==0:
            continue
        project_list=[ i.project for i in products]
        roadmaps = project_models.RoadMaps.objects.filter(project__in=project_list,updated_at__gte=last_24_hours)
        features = project_models.RoadMapFeatures.objects.filter(roadmap__project__in=project_list, updated_at__gte=last_24_hours)
        # roadmap_ids = project_models.RoadMapFeatures.objects.filter(updated_at__gte=last_24_hours).values_list('roadmap__id',flat=True)
        # features_roadmap = project_models.RoadMaps.objects.filter(id__in=roadmap_ids)
        argument = {}
        notifiers = []
        new_features = []
        o_features = []
        n_features = []
        o_roadmap = []
        n_roadmap = []
        o_product = []
        n_product = []
        if features or roadmaps or products:
            for feature in features:
                if feature.updated_at.strftime('%d-%m-%Y %H:%M:%S')>feature.created_at.strftime('%d-%m-%Y %H:%M:%S'):
                    f_new = feature.history.filter(updated_at__gte=last_24_hours).first()
                    f_old = feature.history.filter(updated_at__lt=last_24_hours).first()
                    if f_old and ((f_new.name!=f_old.name) or (f_new.reach!=f_old.reach) or (f_new.impact!=f_old.impact) or (f_new.confidence!=f_old.confidence) or (f_new.effort!=f_old.effort)):
                        o_features.append(feature)
                else:
                    n_features.append(feature)
                # collaborators=project_models.Collaborator.objects.filter(roadmap=feature.roadmap).values_list('user__username',flat=True)
                project_org=project_models.ProjectsOrganizationMapping.objects.filter(project=feature.roadmap.project).values('organization')
                org_admins=models.Role.objects.filter(organization__in=project_org,role='admin').values_list('user__username', flat=True)
                # org_admins = project_org.role_set.filter(role="admin").values_list('user__username', flat=True)
                # notifiers.extend(list(collaborators))
                notifiers.extend(list(org_admins))
            for roadmap in roadmaps:
                if roadmap.updated_at.strftime('%d-%m-%Y %H:%M:%S')>roadmap.created_at.strftime('%d-%m-%Y %H:%M:%S'):
                    r_new = roadmap.history.filter(updated_at__gte=last_24_hours).first()
                    r_old = roadmap.history.filter(updated_at__lt=last_24_hours).first()
                    if r_old and ((r_new.name!=r_old.name) or (r_new.description!=r_old.description)):
                        o_roadmap.append(roadmap)
                    else:
                        n_roadmap.append(roadmap)
                else:
                    n_roadmap.append(roadmap)
                # collaborators=project_models.Collaborator.objects.filter(roadmap=roadmap).values_list('user__username',flat=True)
                project_org=project_models.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).values('organization')
                org_admins=models.Role.objects.filter(organization__in=project_org,role='admin').values_list('user__username', flat=True)
                # org_admins = project_org.role_set.filter(role="admin").values_list('user__username', flat=True)
                # notifiers.extend(list(collaborators))
                notifiers.extend(list(org_admins))
            for product in products:
                if product.updated_at.strftime('%d-%m-%Y %H:%M:%S')>product.created_at.strftime('%d-%m-%Y %H:%M:%S'):
                    p_new = product.history.filter(updated_at__gte=last_24_hours).first()
                    p_old = product.history.filter(updated_at__lt=last_24_hours).first()
                    if p_old and ((p_new.name!=p_old.name)):
                        o_product.append(product)
                else:
                    n_product.append(product)
                org_admins = product.organization.role_set.filter(role="admin").values_list('user__username', flat=True)
                notifiers.extend(list(org_admins))
            # superadmins = models.Role.objects.filter(role="superadmin").values_list('user__username', flat=True)
            # notifiers.extend(list(superadmins))
            argument = {
                'organization':organization,
                'features': n_features,
                'updated_features':o_features,
                'roadmaps':n_roadmap,
                'updated_roadmaps':o_roadmap,
                'products':n_product,
                'updated_products':o_product,
            }
            final_args.append({'argument':argument, 'notifiers':notifiers})

    return final_args

def send_notification_email():
    arguments = activity_notifications_to_collaborator()
    superadmins = models.Role.objects.filter(role="superadmin").values_list('user__username', flat=True)
    email_args = {
                'arguments':arguments,
                'origin': settings.SITE_ORIGIN,
            }
    recipients = list(set(superadmins))
    
    # Send Email as non blocking thread. Reduces request waiting time.
    if arguments:
        t = threading.Thread(target=functions.EmailService(email_args, recipients).send_notification_email_to_superadmin)
        t.start()
    
    for argument in arguments:
        email_args = {
                'arguments':argument['argument']
            }

        recipients = list(set(argument['notifiers']))
        # Send Email as non blocking thread. Reduces request waiting time.
        t = threading.Thread(target=functions.EmailService(email_args, recipients).send_notification_email)
        t.start()


local_time=datetime.datetime(year=settings.NOTIFY_YEAR, month=settings.NOTIFY_MONTH, day=settings.NOTIFY_DAY, hour=settings.NOTIFY_HOUR, minute=settings.NOTIFY_MINUTE, second=settings.NOTIFY_SECOND, microsecond=settings.NOTIFY_M_SECOND, tzinfo=pytz.timezone(settings.CENTRAL_TIME_ZONE))
central_time = (local_time + datetime.timedelta(minutes=300))

sched = BackgroundScheduler()
sched.add_job(send_notification_email, 'cron', hour=central_time.hour, minute=central_time.minute, second=(central_time.second+20))
# sched.add_job(send_notification_email, 'interval', seconds=10)
sched.start()

def user_feedback(user,subject,body, role):
    
    email_args = {
            'full_name':user.first_name,
            'user_email':user.username,
            'subject':subject,
            'body':body,
            'role':role
        }

    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, settings.FEEDBACK_EMAIL).send_feedback_email)
    t.start()

def user_activity_log(user,name,arguments,org_id,project_id):

    try:
        role = models.Role.objects.get(user=user)
    except models.Role.DoesNotExist:
        return Response(data={"detail": "user does not have any roles"}, status=status.HTTP_404_NOT_FOUND)
    arguments['date'] = arguments['date'][:10]
    models.Activity.objects.create(
                user=user,
                name=name,
                arguments=arguments,
                organization=org_id,
                projects=project_id
                )

def update_user_detail(user, first_name, last_name, email,image):
    
    if user is None:
        raise exceptions.ExistsError("User details doesn't exists")
    user_obj=models.User.objects.filter(username=email).exclude(id=user.id)
    if user_obj.count()!=0:
        raise exceptions.ExistsError("Email details already exist")
    pr=models.Profile.objects.filter(user_id=user.id).first()
    if image is not None:
        pr.image=image
        p=pr.save()
    user.first_name=first_name
    user.last_name=last_name
    user.username=email
    use=user.save()
    return use

def send_app_access_email(app_name,first_name,last_name,email):
    superadmins = models.Role.objects.filter(role="superadmin").values_list('user__username', flat=True)
    email_args = {
               'full_name': f"{first_name} {last_name}".strip(),
                'app_name':app_name,
                'user_email':email,
            }
    recipients = list(set(superadmins))
    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, recipients).send_app_access_email_to_superadmin)
    t.start()    

def create_organization_user (new_member_user,organization,role,access_list):
    user_list=[]
    user_role=[]
    user_access=[]
    profile_list=[]
    for i in new_member_user:
       
        user = models.User.objects.filter(username=i["email"]).first()
        if user is not None:
            raise exceptions.ExistsError("Email already exists.")
        else:
            password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
            user = models.User(first_name=i["first_name"], last_name=i["last_name"], username=i["email"], is_staff=False, is_superuser=False,is_active=False ,password=password_hash)
            role = models.Role(user=user, organization=organization, role= models.Role.RoleName.user)
            for j in access_list:
                access = models.UserAppMappping(user=user,app_id=j)
            profile = models.Profile(user=user)
            user_list.append(user) 
            user_role.append(role) 
            profile_list.append(profile)
            user_access.append(access)
            email_id=i["email"]
            email_bytes= email_id.encode("ascii")  
            base64_bytes= base64.b64encode(email_bytes)
            base64_email= base64_bytes.decode("ascii")
            email_args = {
                'full_name': f"{i['first_name']} {i['last_name']}".strip(),
                'email': i["email"],
                'password': password_str,
                'origin': f"{settings.SITE_ORIGIN}{base64_email}"
            }
            # Send Email as non blocking thread. Reduces request waiting time.
            t = threading.Thread(target=functions.EmailService(email_args, [email_id, ]).send_welcome_email)
            t.start()
            models.User.objects.bulk_create(user_list)
            models.Role.objects.bulk_create(user_role)
            models.Profile.objects.bulk_create(profile_list)
            models.UserAppMappping.objects.bulk_create(user_access)
    return user.id        

def invitation_sent_email(email: str) -> bool:
    password_str, password_hash = functions.get_hashed_password(allowed_chars=configurations.ALLOWED_RANDOM_CHARS)
    email = email.strip()
    # user  = functions.get_user_by_email(email=email)
    user = models.User.objects.filter(username=email).first()
    if user is None:
        return False
    user.password = password_hash
    user.save()
    email_bytes= email.encode("ascii")  
    base64_bytes= base64.b64encode(email_bytes)
    base64_email= base64_bytes.decode("ascii")
    email_args = {
                'full_name': user.get_full_name(),
                'email': email,
                'password': password_str,
                'origin': f"{settings.SITE_ORIGIN}{base64_email}"
            }
    # Send Email as non blocking thread. Reduces request waiting time.
    t = threading.Thread(target=functions.EmailService(email_args, [email, ]).send_welcome_email)
    t.start()
    return True            
