from . import models
from projects.models import Projects
from generics import exceptions
from . import functions 
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from django.conf import settings
from users import models as user_model
from . import serializers




def roadmap_notifications(request):
    user = request.user
    org_id = user_model.Role.objects.filter(user=request.user).first()
    
    if org_id.role != "superadmin":

        pattern_notification = models.RoadMapNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        if pattern_notification:        
            serializer = serializers.RoadMapNotifcationSerializer(pattern_notification,many=True)
        else:
                return []
            
    elif org_id.role == "superadmin":
        
        history = models.RoadMapNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=request.user.id).order_by("-created_at")[:10]
        if history:
                
                serializer = serializers.RoadMapNotifcationSerializer(history,many=True)
        else:
            return []
    
    
    return serializer.data