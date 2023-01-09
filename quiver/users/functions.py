from . import models
from . import serializers
from . import configurations
from generics import exceptions
from django.contrib.auth.hashers import make_password, check_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from projects.models import ProjectsOrganizationMapping,Projects
def get_user_by_id(id: int, active: bool = True):
    return models.User.objects.filter(id=id).first()

def user_info(user) -> dict:
    return serializers.UserInfoModelSerializer(user).data

def get_hashed_password(allowed_chars: str) -> tuple:
    password_str = get_random_string(length=8, allowed_chars=allowed_chars)
    return password_str, make_password(password_str)

def get_user_by_email(email: str, active: bool = True, active_check: bool = True):
    if not active_check:
        return models.User.objects.filter(username=email).first()
    return models.User.objects.filter(username=email, is_active=active).first()

def get_user_by_id_email(id: int, email: str, active: bool = True):
    return models.User.objects.filter(id=id, username=email, is_active=active)

def create_enterprise_user(first_name: str, last_name: str, email: str, phone: int, password: str, role: str,access_list) -> bool:
    # check if user exists in database
    user = get_user_by_email(email=email, active_check=False)
    if user is not None:
        return False
    if role == models.Role.RoleName.superadmin:
        user = models.User.objects.create(first_name=first_name, last_name=last_name, username=email, is_staff=True, is_superuser=True, password=password)
    else:
        user = models.User.objects.create(first_name=first_name, last_name=last_name, username=email, is_staff=False, is_superuser=False,is_active=False, password=password)
    role = models.Role.objects.create(user=user,role=role)
    bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
    ]
    models.UserAppMappping.objects.bulk_create(bulk_app_access)
    models.Profile.objects.create(user=user, phone=phone)
    return True

def is_organization_exists(organization_name: str):
    return models.Organization.objects.filter(name=organization_name).first()

def is_role_exists(role: str):
    return models.Role.objects.filter(role=role).first()

class EmailService:
    def __init__(self, email_args, email_to_list):
        self.email_args     = email_args
        self.email_to_list  = email_to_list

    def send_custom_email(self, subject, html_body):
        send_mail(
            subject = subject,
            message = '',
            from_email      = settings.EMAIL_HOST_USER,
            recipient_list  = self.email_to_list,
            html_message    = html_body
        )

    def send_custom_email_momentum(self, subject, html_body):
        
        send_mail(
            subject = subject,
            message = '',
            from_email      = settings.EMAIL_HOST_USER,
            recipient_list  = self.email_to_list,
            html_message    = html_body
        )
        

    def send_welcome_email(self):
        subject     = "Welcome to Alignment Chain"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        password    = self.email_args['password']
        origin      = self.email_args['origin']
        primary_layout  = render_to_string('welcome.html', {'fullname': full_name, 'email': email, 'password': password, 'origin': origin})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    def send_password_reset_email(self):
        subject     = "Alignment Chain: Reset Password"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        password    = self.email_args['password']
        origin      = self.email_args['origin']
        primary_layout  = render_to_string('resetpassword.html', {'fullname': full_name, 'email': email, 'password': password, 'origin': origin})
        html_body       = render_to_string('main3.html', {'content': primary_layout})

        self.send_custom_email(subject, html_body)

    def send_notification_email(self):
        subject     = f"Alignment Chain: Activity Notification of Organization {self.email_args['arguments']['organization'].name} "
        arguments   = self.email_args['arguments']
        primary_layout  = render_to_string('notification.html', {'arguments': arguments})
        html_body       = render_to_string('main3.html', {'content': primary_layout})

        self.send_custom_email(subject, html_body)

    def send_notification_email_to_superadmin(self):
        subject     = f"RoadmapLive: Activity Notification"
        arguments   = self.email_args['arguments']
        origin      = self.email_args['origin']
        primary_layout  = render_to_string('notification_admin.html', {'arguments': arguments, 'origin':origin})
        html_body       = render_to_string('main3.html', {'content': primary_layout})

        self.send_custom_email(subject, html_body)
    def send_app_access_email_to_superadmin(self):
        subject     = f"Alignment Chain: App Access Request "
        user_email  = self.email_args['user_email']
        full_name      = self.email_args['full_name']
        app_name    = self.email_args['app_name']
        primary_layout  = render_to_string('requestaccess.html', {'user_email': user_email, 'full_name':full_name,'app_name':app_name})
        html_body       = render_to_string('main3.html', {'content': primary_layout})

        self.send_custom_email(subject, html_body)
    def send_feedback_email(self):
        subject     = self.email_args['subject']
        full_name   = self.email_args['full_name']
        email       = self.email_args['user_email']
        body    = self.email_args['body']
        role    = self.email_args['role']
        primary_layout  = render_to_string('feedback.html', {'fullname': full_name, 'email': email, 'body': body, 'role':role})
        html_body       = render_to_string('main3.html', {'content': primary_layout})

        self.send_custom_email(subject, html_body)
    def send_context_welcome_email(self):
        subject     = "Welcome to Context"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        password    = self.email_args['password']
        origin      = self.email_args['origin']
        primary_layout  = render_to_string('emailtempl.html', {'fullname': full_name, 'email': email, 'password': password, 'origin': origin})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)
    def send_invitation_email(self):
        subject     = "Welcome to Context"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['url']
        primary_layout  = render_to_string('existinguser.html', {'fullname': full_name,'email': email,'url':url})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    #For document share
    #Pattern
    def send_pattern_document_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        app       = self.email_args['app']
        message = self.email_args['message']
        primary_layout  = render_to_string('sharereport.html', {'fullname': full_name,'email': email,'url':url,'app':app,'message':message})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    #RoadMap
    def send_roadmap_document_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        app       = self.email_args['app']
        message = self.email_args['message']
        primary_layout  = render_to_string('sharereport.html', {'fullname': full_name,'email': email,'url':url,'app':app,'message':message})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    #Context
    def send_canvas_document_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        app       = self.email_args['app']
        message = self.email_args['message']
        primary_layout  = render_to_string('sharereport.html', {'fullname': full_name,'email': email,'url':url,'app':app,'message':message})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)
    
    #BluePrint
    def send_blueprint_document_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        app       = self.email_args['app']
        message = self.email_args['message']
        primary_layout  = render_to_string('sharereport.html', {'fullname': full_name,'email': email,'url':url,'app':app,'message':message})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    def send_momentum_report_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        app       = self.email_args['app']
        message = self.email_args['message']
        primary_layout  = render_to_string('sharereport.html', {'fullname': full_name,'email': email,'url':url,'app':app,'message':message})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

    def send_momentum_auto_report_email(self):
        subject     = f"{'Welcome to '}{self.email_args['app']}"
        full_name   = self.email_args['full_name']
        email       = self.email_args['email']
        url       = self.email_args['origin']
        primary_layout  = render_to_string('autoreport.html', {'fullname': full_name,'email': email,'url':url})
        html_body       = render_to_string('main3.html', {'content': primary_layout})
        self.send_custom_email(subject, html_body)

class CryptoGraphy:
    def __init__(self):
        password_provided = settings.SECRET_KEY
        password = password_provided.encode()  # Convert to bytes type
        salt = b'`y\xcdB`\xc8.\xb8J\xd5\x99\xb6\xfb\x99X\x94'  # must be type bytes
        kdf = PBKDF2HMAC(
            algorithm   = hashes.SHA256(),
            length      = 32,
            salt        = salt,
            iterations  = 100000,
            backend     = default_backend()
        )
        self.key = base64.urlsafe_b64encode(
            kdf.derive(password))  # Can only use kdf once

    def crypto_encrypt_msg(self, data_string):
        encoded_message = data_string.encode()
        f = Fernet(self.key)
        encrypted = f.encrypt(encoded_message)
        encrypted = encrypted.decode()
        return encrypted

    def crypto_decrypt_msg(self, data_string):
        encoded_message = data_string.encode()
        f = Fernet(self.key)
        try:
            decrypted = f.decrypt(encoded_message)
        except InvalidToken:
            return None
        decrypted = decrypted.decode()
        return decrypted

    def non_safe_base64_encode(self, data_string):
        encoded_message = data_string.encode()
        encoded = base64.b64encode(encoded_message)
        encoded = encoded.decode()
        return encoded

    def non_safe_base64_decode(self, data_string):
        encoded_message = data_string.encode()
        decoded = base64.b64decode(encoded_message)
        decoded = decoded.decode()
        return decoded

def is_time_greater_15_mins(current_time, url_generated_time) -> bool:
    time_difference     = current_time - url_generated_time
    minutes_difference  = time_difference.seconds / 60
    if minutes_difference > 15:
        return True
    return False

def update_password(user_id: int, email: str, password: str) -> bool:
    users = get_user_by_id_email(id=user_id, email=email)
    if users.first() is None:
        return False
    password_hash = make_password(password)
    users.update(password=password_hash)
    return True

def create_organization(creator, first_name: str, last_name: str, name: str, email: str, phone: str, password: str,access_list:list,project_creationlist:list) -> bool:
    
    user = get_user_by_email(email=email, active_check=True)
    if user is not None:
        raise exceptions.ExistsError("The Email address is already being used.")

    organization = is_organization_exists(organization_name=name)
    if organization is not None:
        raise exceptions.ExistsError("The Organization name is already being used.")

    user = models.User.objects.create(first_name=first_name, last_name=last_name, username=email, is_staff=False, is_superuser=False, password=password)
    organization = models.Organization.objects.create(name=name,created_by=creator)
    # Bulk Create Education
    bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
    ]
    models.UserAppMappping.objects.bulk_create(bulk_app_access)
    bulk_project = [
        Projects(name=i,created_by=creator) for i in project_creationlist
    ]
    project_creation=Projects.objects.bulk_create(bulk_project)
    bulk_project_creation = [
        ProjectsOrganizationMapping(organization=organization, project=i,created_by=creator) for i in project_creation
    ]

    # bulk_project_mapping = [
    #     ProjectsOrganizationMapping(organization=organization, project=Projects.objects.filter(id=i).first(),created_by=creator) for i in project_list
    # ]
    # ProjectsOrganizationMapping.objects.bulk_create(bulk_project_mapping)
    ProjectsOrganizationMapping.objects.bulk_create(bulk_project_creation)

    models.Role.objects.create(user=user, organization=organization, role=models.Role.RoleName.admin)
    profile = models.Profile.objects.create(user=user, phone=phone)

def create_organization_user(first_name: str, last_name: str, email: str, phone: str, password: str,role: str,  organization,access_list:list) -> bool:
    user = models.User.objects.create(first_name=first_name, last_name=last_name, username=email, is_staff=False,is_superuser=False,is_active=False, password=password)
    profile = models.Profile.objects.create(user=user, phone=phone)
    models.Role.objects.create(user=user, organization=organization, role=role)
    bulk_app_access = [
        models.UserAppMappping(app_id=i,user=user) for i in access_list
    ]
    models.UserAppMappping.objects.bulk_create(bulk_app_access)

def create_feedback(creator, subject: str, description: str, is_visible: bool) -> bool:

    feedback = models.UserFeedback.objects.create(created_by=creator,
                                                 subject=subject, 
                                                 description=description, 
                                                 is_visible=is_visible
                                                 )

