from django.db import models
from model_utils import FieldTracker
from generics import mixins
from users import models as user_models 
from simple_history.models import HistoricalRecords
from users.models import User



class Projects(mixins.GenericModelMixin):
    class Status(models.TextChoices):
        active        = "active", "Active"
        archive       = "archive", "Archive"
    name = models.CharField(null=False, max_length=50, unique=False)
    # organization = models.ForeignKey(user_models.Organization,null=True,on_delete=models.CASCADE)
    created_by = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    status = models.CharField(null=False, max_length=20, choices=Status.choices, default=Status.active)
    history = HistoricalRecords()
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Projects"

class ProjectsOrganizationMapping(mixins.GenericModelMixin):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE,related_name="project_data")
    organization = models.ForeignKey(user_models.Organization,null=True,on_delete=models.CASCADE)
    created_by = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.project.name}  {self.organization.name}"

    class Meta:
        verbose_name_plural = "ProjectsOrganizationMapping"

class RoadMaps(mixins.GenericModelMixin):
    name = models.CharField(null=False, max_length=500, unique=False)
    description = models.TextField(null=True)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    created_by = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "RoadMaps"

class RoadMapFeatures(mixins.GenericModelMixin):
    class FeatureStatus(models.TextChoices):
        active        = "active", "Active"
        archive       = "archive", "Archive"
        complete      = "complete", "Complete"
    name = models.CharField(null=False, max_length=500, unique=False)
    reach = models.FloatField(null=False, default=0.0)
    impact = models.FloatField(null=False, default=0.0)
    confidence = models.FloatField(null=False, default=0.0)
    effort = models.FloatField(null=False, default=0.0)
    score = models.FloatField(null=False, default=0.0)
    rice_score = models.FloatField(null=False, default=0.0)
    status = models.CharField(null=False, max_length=20, choices=FeatureStatus.choices, default=FeatureStatus.active)
    roadmap = models.ForeignKey(RoadMaps, on_delete=models.CASCADE)
    created_by = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    order = models.IntegerField(null=False, default=0)
    image = models.JSONField(blank=True,default=dict)
    description = models.TextField(null=True,  unique=False)
    history = HistoricalRecords()


    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "RoadMapFeatures"

class Collaborator(mixins.GenericModelMixin):
    roadmap = models.ForeignKey(RoadMaps, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    write = models.BooleanField(null=False, default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Collaborator"



class RoadMapComments(mixins.GenericModelMixin):
    roadmap = models.ForeignKey(RoadMaps, on_delete=models.CASCADE)
    feature = models.ForeignKey(RoadMapFeatures, on_delete=models.CASCADE)    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    
    def __str__(self):
        return f"{self.roadmap}"

    class Meta:
        verbose_name_plural = "RoadMapComments"

class RoadMapCommentsReply(mixins.GenericModelMixin):
    roadmap_comment = models.ForeignKey(RoadMapComments, on_delete=models.CASCADE,related_name="reply")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    
    def __str__(self):
        return f"{self.roadmap_comment}"

    class Meta:
        verbose_name_plural = "RoadMapCommentsReply"


class RoadMapShare(mixins.GenericModelMixin):
    roadmap = models.ForeignKey(RoadMaps, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='roadmap_receiver')
    status = models.CharField(null=False, max_length=100,default="sent")
    message = models.CharField(null=True, max_length=1000)
    
    def __str__(self):
        return f"{self.roadmap}"

    class Meta:
        verbose_name_plural = "RoadMapShare"


class RoadMapNotification(mixins.GenericModelMixin):
    class Action(models.TextChoices):
        
        create          = "create", "Create"
        update          = "update", "Update"
        delete          = "delete", "Delete"
        comment         = "comment", "Comment"
        reply           = "reply" ,  "Reply"
        product_create  = "Product_create", "product_create"
        product_update  = "Product_update", "product_update"
        feature_create  = "feature_create","Feature_create"
        feature_update  = "feature_update","Feature_update"
    
    class Status(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"

    
    class HighLightStatus(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"

    roadmap = models.ForeignKey(RoadMaps, on_delete=models.CASCADE,null=True)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="action_user_road")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE)
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    comment = models.ForeignKey(RoadMapComments, on_delete=models.CASCADE,null=True)
    reply = models.ForeignKey(RoadMapCommentsReply, on_delete=models.CASCADE,null=True)
    feature =  models.ForeignKey(RoadMapFeatures, on_delete=models.CASCADE,null=True)
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)
