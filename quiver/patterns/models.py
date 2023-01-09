from django.db import models
from generics import mixins
from projects .models import Projects
from users.models import User
from simple_history.models import HistoricalRecords
# Create your models here.

class Pattern(mixins.GenericModelMixin):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(null=False, max_length=50, unique=False)
    description = models.TextField(blank=True, null=True)
    section = models.JSONField(null=True, default=list)
    history = HistoricalRecords(inherit=True)
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Patterns"
        
class PatternSection(mixins.GenericModelMixin):
    class SectionTypes(models.TextChoices):
        list        = "list", "list"
        image       = "image", "image"
        text        = "text", "text"
        # url         = "url", "url"
        # font_file   =  "font_file","font_file"
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    name = models.CharField(null=False, max_length=50, unique=False)
    has_sub_section = models.BooleanField(null=False, default=False)
    section_icon = models.JSONField(null=True, default=dict)
    section_type = models.CharField(null=False, max_length=20, choices=SectionTypes.choices)
    level =  models.IntegerField(default=1)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "PatternSections"

class PatternFont(mixins.GenericModelMixin):
    class FontTypes(models.TextChoices):
        file       = "file", "file"
        url        = "url", "url"
        text       = "text", "text"
    name           = models.CharField(null=False, max_length=50, unique=False)
    generic        = models.CharField(null=True, max_length=50, unique=False)
    upload_flag    = models.BooleanField(null=False, default=False)
    data_file_path = models.TextField(blank=True, null=True)
    url            = models.TextField(blank=True, null=True)
    font_type      = models.CharField(max_length=50, unique=False,choices=FontTypes.choices,null=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "PatternFont"
        
class PatternSubSection(mixins.GenericModelMixin):
    pattern_section = models.ForeignKey(PatternSection, on_delete=models.CASCADE)
    name = models.CharField(null=False, max_length=50, unique=False)
    level = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "PatternSubSections"
        
class PatternSectionCollection(mixins.GenericModelMixin):
    pattern_section = models.ForeignKey(PatternSection, on_delete=models.CASCADE,null=True)
    pattern_sub_section = models.ForeignKey(PatternSubSection, on_delete=models.CASCADE,null=True)
    data_list = models.JSONField(null=True, default=list)
    data_text = models.TextField(null=True)
    data_image = models.JSONField(null=True, default=list)


    def __str__(self):
        return f"{self.pattern_section} {self.pattern_sub_section}"

    class Meta:
        verbose_name_plural = "PatternSectionCollections"
        
# class PatternSubSectionCollection(mixins.GenericModelMixin):
#     pattern_sub_section = models.ForeignKey(PatternSectionCollection, on_delete=models.CASCADE)
#     data_list = models.JSONField(null=True, default=list)
#     data_text = models.TextField(null=False)
#     data_image = models.BinaryField(null=False)


#     def __str__(self):
#         return self.pattern_sub_section

#     class Meta:



class PatterComments(mixins.GenericModelMixin):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.pattern}"

    class Meta:
        verbose_name_plural = "PatterComments"

class PatterCommentsReply(mixins.GenericModelMixin):
    pattern_comment = models.ForeignKey(PatterComments, on_delete=models.CASCADE,related_name="reply")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # comments = models.CharField(null=False, max_length=3000)
    comments = models.JSONField(null=True, default=dict)
    attachments = models.JSONField(null=True, default=list)
    history = HistoricalRecords(inherit=True)
    def __str__(self):
        return f"{self.pattern_comment}"

    class Meta:
        verbose_name_plural = "PatterCommentsReply"


class PatterShare(mixins.GenericModelMixin):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='receiver')
    status = models.CharField(null=False, max_length=100,default="sent")
    message = models.CharField(null=True, max_length=1000)
    
    def __str__(self):
        return f"{self.pattern}"

    class Meta:
        verbose_name_plural = "PatterShare"


class PatternNotification(mixins.GenericModelMixin):
    class Action(models.TextChoices):
        
        create       = "create", "Create"
        update       = "update", "Update"
        delete       = "delete", "Delete"
        comment      = "comment", "Comment"
        reply        = "reply" ,  "Reply"
        product_create  = "Product_create", "product_create"
        product_update  = "Product_update", "product_update"
    
    class Status(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"

    
    class HighLightStatus(models.TextChoices):

        seen =   "seen" , "Seen"
        unseen =  "unseen", "Useen"

    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE,null=True)
    action_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="action_user")
    action_type = models.CharField(null=False, max_length=100,choices=Action.choices)
    action_status = models.CharField(null=False, max_length=100,choices=Status.choices,default="unseen")
    org_user = models.ForeignKey(User, on_delete=models.CASCADE)
    higlight_status = models.CharField(null=False, max_length=100,choices=HighLightStatus.choices,default="unseen")
    comment = models.ForeignKey(PatterComments, on_delete=models.CASCADE,null=True)
    reply = models.ForeignKey(PatterCommentsReply, on_delete=models.CASCADE,null=True)
    product =  models.ForeignKey(Projects, on_delete=models.CASCADE,null=True)


