import json
import datetime
import pytz
from rest_framework_simplejwt.backends import TokenBackend

from . import models
from . import configurations
from . import utils


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.content_type == "multipart/form-data":
            request_body = request.POST
        elif request.content_type == "json" or request.content_type == "application/json":
            request_body = json.loads(request.body.decode("utf-8"))
        else:
            request_body = {}
        response = self.get_response(request)
        # If wrong request, then return response
        if request.resolver_match is None:
            return response

        # No need to save activity if the request is for getting docs
        exceptional_urls = ('schema', 'swagger', 'redoc')
        if request.resolver_match.url_name in exceptional_urls:
            return response

        # No need to save activity if the request hit is not a successful
        if not str(response.status_code).startswith(
                "2") or request.method == "OPTIONS":
            return response

        # request_config = configurations.USER_ACTIONS.get(request.method, None)
        # if request_config is None:
        #     raise ValueError(
        #         f"Please set the {request.method} (USER_ACTIONS) for the request in `users/configurations.py` file."
        #     )

        # url_config = request_config.get(request.resolver_match.url_name, None)
        # if url_config is None:
        #     raise ValueError(
        #         f"Please set the {request.resolver_match.url_name} (USER_ACTIONS) for the request in `users/configurations.py` file."
        #     )

        # description = url_config.get("description", None)
        # if description is None:
        #     raise ValueError(
        #         "Please set the description (USER_ACTIONS) for the request in `users/configurations.py` file."
        #     )

        user = request.user
        # Track user when click the activity link in the notification email
        
        from_email = request.GET.get('from_email',None)

        if from_email is not None and from_email=="true":
            if request.resolver_match.url_name == 'projects-list':
                request.resolver_match.url_name = 'Products'
            utils.user_activity_log(user=user,name=f'visited {request.resolver_match.url_name} page from email',arguments={'name':user.username, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})

        # Getting user for `login` and `refresh` (AnonymousUser)
        if request.resolver_match.url_name == 'login':
            username = request_body.get('username', None)
            user = models.User.objects.filter(username=username).first()
            utils.user_activity_log(user=user,name=request.resolver_match.url_name,arguments={'name':user.username, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S')})
        # elif request.resolver_match.url_name == 'refresh':
        #     refresh = request_body.get('refresh', None)
        #     valid_data = TokenBackend(algorithm='HS256').decode(refresh,
        #                                                         verify=False)
        #     user_id = valid_data.get('user_id', None)
        #     user = models.User.objects.filter(id=user_id).first()

        # if user is not None:
        #     models.Activity.objects.create(
        #         user=user,
        #         name=request.resolver_match.url_name,
        #         description=description)
        
        return response
