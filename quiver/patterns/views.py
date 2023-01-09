from uuid import UUID
from django.conf import settings
from django.forms import UUIDField
from generics import permissions
from rest_framework import status, viewsets
from rest_framework.response import Response
from . import serializers
from . import utils
from generics import exceptions
from users.models import Role
from patterns.models import Pattern, PatternFont
from projects.models import ProjectsOrganizationMapping
from drf_spectacular.utils import extend_schema
from . import models
import json
from rest_framework.decorators import action
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from django.db.models import Q
from projects import models as prg_model
from users import models as user_model
import threading
from users import functions as user_fn
from rest_framework.viewsets import GenericViewSet
from users import configurations

# Create your views here.
class PatternsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete patterns
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin ,]
    serializer_class    = serializers.PatternCreateSerializer
    request   = serializers.PatternCreateSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }
    def get_queryset(self):
        role = Role.objects.get(user = self.request.user)
        if role.role=='superadmin':
            query_set=Pattern.objects.all().order_by('-created_at')
        else:
            projects=ProjectsOrganizationMapping.objects.filter(organization=role.organization).values('project')
            query_set=Pattern.objects.filter(project__in=projects).order_by('-created_at')
        return query_set
    
    @extend_schema(
    tags=['Quiver'],
    request   = serializers.PatternCreateSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create patterns
        """
        serializer = serializers.PatternCreateSerializer(data=request.data)
        project_id       : str = request.data.get('project_id', None)
        if project_id is None:
            return Response(data={"error": ["The project id should not be null"]}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        title            : str = serializer.validated_data.get('title', None)
        description      : str = serializer.validated_data.get('description', None)
        # pattern_section  : str = serializer.validated_data.get('pattern_section', None)
        try:
            result=utils.patten_creation(project_id,title,description,request.user)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={"id":result.id}, status=status.HTTP_201_CREATED)
    @extend_schema(
    tags=['Quiver'],
    request   = None,
    responses = {201: serializers.PatternAllListSerializer})
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        querset     = self.get_queryset()
        serializer  = serializers.PatternAllListSerializer(querset, many=bool)
        return Response(serializer.data)
        #return Response(data={'detail': 'Project created successfully'}, status=status.HTTP_201_CREATED)
    

    @extend_schema(
    tags=['Quiver'],
    request   = None,
    responses = {202: dict,
            404: dict,})
    def destroy(self, request,pk):
        """
        Delete patternsections
        """
        
        try:
            pattern_obj=models.PatternSection.objects.filter(id=pk)
            pattern_obj.delete()
            return Response(data={'detail': 'Pattern deleted successfully'}, status=status.HTTP_202_ACCEPTED)

        except models.PatternSection.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
    tags=['Quiver'],
    request   = None,
    responses = {202: dict,
            404: dict,})
    
    @action(detail=True,methods=['delete'], url_path='pattern_destroy')

    def pattern_destroy(self, request,pk):
        """
        Delete pattern
        """
        
        try:
            pattern_obj=models.Pattern.objects.filter(id=pk)
            pattern_obj.delete()
            return Response(data={'detail': 'Pattern deleted successfully'}, status=status.HTTP_202_ACCEPTED)

        except models.Pattern.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


    @extend_schema(
        tags=['Quiver'],
        request   = serializers.PatternUpdateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
    )     
    def update(self, request, pk=None):
        """
        Update patterns, section, subsection \n
        @TODO:
        \n 
        \t-if edit_pattern_section == true\n 
        \t\t- title *required field\n
        \t-if edit_pattern_section == false\n
        \t\t- pattern_section_id and pattern_section *required field
        """
        try:
            instance = models.Pattern.objects.get(pk=pk)
            serializer = serializers.PatternUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            title            : str = serializer.validated_data.get('title', None)
            description      : str = serializer.validated_data.get('description', None)
            edit_pattern_section : str = serializer.validated_data.get('edit_pattern_section', None)
            pattern_section_id : str = serializer.validated_data.get('pattern_section_id', None)
            pattern_section    : json = serializer.validated_data.get('pattern_section',None)
            try:
                if edit_pattern_section == True:
                    try:
                        pattern_section_obj=models.PatternSection.objects.get(id=pattern_section_id)
                    except models.PatternSection.DoesNotExist:
                        return Response({"detail":"Pattern Section not found"}, status=status.HTTP_404_NOT_FOUND)
                    result=utils.pattern_section_update(instance,pattern_section_id,pattern_section)
                else:
                    result=utils.pattern_update(instance,title,description)
                    
            except exceptions.ExistsError as e:
                    return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        except models.Pattern.DoesNotExist:
                return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)

        
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.PatternAddSerializer,

    responses = {201: dict})

    @action(detail=False,methods=['post'], url_path='session_addition')

    def session_addition(self, request):
        """
        Add pattern sections\n
        Params 
        ------
        pattern_id      : UUID of pattern
        pattern_section : Pattern section details
        """
        serializer = serializers.PatternAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pattern_id      : str = serializer.validated_data.get('pattern_id', None)

        pattern_section  : str = serializer.validated_data.get('pattern_section', None)
        try:
            result=utils.patten_add(pattern_id ,pattern_section)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={'detail': 'Pattern sections added successfully'}, status=status.HTTP_201_CREATED)
        
    @extend_schema(
        tags=['Quiver'],
    request   = serializers.PatternFontSerializer,

    responses = {201: dict})

    @action(detail=False,methods=['post'], url_path='font_upload')

    def font_upload(self, request):
        """
        Add pattern sections\n
        Params 
        ------
        name      : Font name
        file      : Font file
        generic   : generic name
        font_type  :file/url
        url        :url
        """
        serializer = serializers.PatternFontSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name : str = serializer.validated_data.get('name', None)
        file : str = serializer.validated_data.get('file', None)
        generic: str = serializer.validated_data.get('generic', None)
        font_type: str = serializer.validated_data.get('font_type', None)
        url: str = serializer.validated_data.get('url', None)
        try:
            result=utils.patten_font_upload(name ,file,generic,font_type,url)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={'detail': 'Font file uploaded successfully'}, status=status.HTTP_201_CREATED)
        
        
class GetSinglePatternView(APIView):
    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternListSerializer,
    responses = {200: dict})
    def get(self,request,pk):
        try:
            instance = models.Pattern.objects.get(pk=pk)
            serializer  = serializers.PatternListSerializer(instance)
            if instance:

                # pattern = models.PatternNotification.objects.filter((Q(pattern=instance,org_user=request.user,action_type="create",higlight_status="unseen",action_status="unseen") | Q(pattern=instance,org_user=request.user,action_type="update",higlight_status="unseen",action_status="unseen")) | (Q(pattern=instance,org_user=request.user,action_type="create",higlight_status="unseen",action_status="unseen") & Q(pattern=instance,org_user=request.user,action_type="update",higlight_status="unseen",action_status="unseen"))).update(higlight_status="seen",action_status="seen")
                a = models.PatternNotification.objects.filter(pattern=instance,org_user=request.user,action_type__in=["create","update"],higlight_status="unseen",action_status__in=["unseen","seen"]).update(higlight_status="seen",action_status="seen")
            pattern_share = models.PatterShare.objects.filter(pattern=instance,receiver=request.user,status="sent")
            
            if pattern_share:
                pattern_share.update(status= "seen") 

        except models.Pattern.DoesNotExist:
            return Response({"detail": "Pattern does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data)
class GetFontFetchView(APIView):
    @extend_schema(
        tags=['Pattern'],
    request   = None,
    responses = {201: serializers.PatternFontfetchSerializer}) 
   
    def get(self, request):
        """
        Lists all Fonts
        
        """ 
        fontobj = models.PatternFont.objects.all()
        serializer  = serializers.PatternFontfetchSerializer(fontobj, many=bool)
        return Response(serializer.data)
    


#=======================================#
#     PATTERN COMMENTS CRUD VIEW        #
#=======================================#

class PatternsCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete patterns comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.PatternCreateSerializer
    request   = serializers.PatternCommentSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,pattern):
        comments = models.PatterComments.objects.filter(pattern_id= pattern)
        
        if comments:
             
            return comments
        else:
            return "NA"
    
    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternCommentSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create pattern comments
        """
        try:
            serializer = serializers.PatternCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)

            
            #For pattern notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.pattern.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)

                pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance.pattern,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.PatternNotification.objects.bulk_create(pattern_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance.pattern,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.PatternNotification.objects.bulk_create(pattern_notif)
                
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)


    

    @extend_schema(
    tags=['Pattern'],
    request   = None,
    parameters=[

      OpenApiParameter(name='pattern_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.PatternCommentListSerializer})
    
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        pattern = request.query_params.get('pattern_id')
        querset     = self.get_queryset(pattern)
        if querset != "NA":
            
            serializer  = serializers.PatternCommentListSerializer(querset,many=True)
            comments_count = models.PatterComments.objects.filter(pattern_id= pattern).values_list("id",flat=True)
            
            pattern = models.PatternNotification.objects.filter(comment__in=list(comments_count),org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            reply_dt = models.PatterCommentsReply.objects.filter(pattern_comment__in= comments_count).values_list("id",flat=True)
            
            
            pattern_reply = models.PatternNotification.objects.filter(reply__in=list(reply_dt),org_user=request.user,action_type="reply",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            # return Response(serializer.data) 
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'No Comments found'}, status=status.HTTP_200_OK)

    
    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternCommentUpdateSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.PatternCommentUpdateSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.PatterComments.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.PatternCommentUpdateSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Pattern'],
    request   = None,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {202: dict,
            404: dict,})
    
    def destroy(self, request):
        """
        Delete comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        obj     = models.PatterComments.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    


class SingleComment(APIView):
    """
    APIs to get single comment
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.PatternCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        comments = models.PatterComments.objects.filter(pk= pk).first()
        serializer = serializers.PatternCommentListSerializer(comments)
        if comments:
                pattern = models.PatternNotification.objects.filter(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
             
        return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
       

class SingleCommentReply(APIView):
    """
    APIs to get single comment
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.PatternCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        reply = models.PatterCommentsReply.objects.filter(pk=pk).first()
        if reply:
            
            comments = models.PatterComments.objects.filter(pk=reply.pattern_comment.id).first()
            serializer = serializers.PatternCommentListSerializer(comments)
            if comments:
                    pattern = models.PatternNotification.objects.filter((Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")|Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen")) | (Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")&Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen"))).update(higlight_status="seen",action_status="seen")

                   
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
                
        
       



class PatternsReplyCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete patterns comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.PatternReplySerializer
    request   = serializers.PatternReplySerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,pattern):
        comments = models.PatterComments.objects.filter(pattern_id= pattern)
        
        if comments:
             
            return comments
        else:
            return "NA"
  
    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternReplySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    

    def reply_comments(self, request, *args, **kwargs):
        """
        Create pattern comments
        """
        try:
            serializer = serializers.PatternReplySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            #For pattern notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.pattern_comment.pattern.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)

                pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance.pattern_comment.pattern,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.PatternNotification.objects.bulk_create(pattern_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                pattern_notif = list(map(lambda user: models.PatternNotification(pattern=instance.pattern_comment.pattern,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.PatternNotification.objects.bulk_create(pattern_notif)
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternReplyUpdationSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.PatternReplyUpdationSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.PatterCommentsReply.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.PatternReplyUpdationSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Pattern'],
    request   = None,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {202: dict,
            404: dict,})
    
    def destroy(self, request):
        """
        Delete comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        obj     = models.PatterCommentsReply.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    



#======================================#
#   PATTERNS CRUD API START            #
#======================================#


class PatternsCRUDApi(GenericViewSet):
    """
    APIs to create,retrieve,update and delete patterns
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin ,]
    serializer_class    = serializers.PatternCreationSerializer
    request   = serializers.PatternCreationSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }
    def get_queryset(self,org_id):
        role = Role.objects.get(user = self.request.user)
        if role.role=='superadmin':
            if org_id == None :
                query_set=Pattern.objects.all().order_by('-created_at')
                return query_set
            projects=ProjectsOrganizationMapping.objects.filter(organization_id=org_id).values('project')
            query_set=Pattern.objects.filter(project__in=projects).order_by('-created_at')
            # query_set=Pattern.objects.all().order_by('-created_at')
        else:
            projects=ProjectsOrganizationMapping.objects.filter(organization=role.organization).values('project')
            query_set=Pattern.objects.filter(project__in=projects).order_by('-created_at')
        return query_set
    
    @extend_schema(
    tags=['Pattern'],
    request   = serializers.PatternCreationSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create patterns
        """
        serializer = serializers.PatternCreationSerializer(data=request.data)
        project_id       : str = request.data.get('project_id', None)
        if project_id is None:
            return Response(data={"error": ["The project id should not be null"]}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        title            : str = serializer.validated_data.get('title', None)
        description      : str = serializer.validated_data.get('description', None)
        pattern_section  : str = serializer.validated_data.get('section', None)
        try:
            result=utils.creat_pattern(project_id,title,description,pattern_section,request.user,request)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={"id":result.id}, status=status.HTTP_201_CREATED)

    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    # @extend_schema(
    # tags=['Pattern'],
    # request   = None,
    # responses = {201: serializers.PatternAllListSerializer})
    
    # def list(self, request):
    #     """
    #     Lists all ScheduleGroups
        
    #     @TODO: Add pagination
    #     """
    #     querset     = self.get_queryset()
    #     serializer  = serializers.PatternAllListSerializer(querset, many=bool,context={"request":request})
    #     return Response(serializer.data)
        #return Response(data={'detail': 'Project created successfully'}, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        tags=['Pattern'],
        request   = serializers.PatternAllListSerializer,
          parameters=[

            OpenApiParameter(name='limit', required=False, type=int,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='offset', required=False, type=int,location=OpenApiParameter.QUERY),

            ],
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
)
    def list(self,request):
        serializ=serializers.PatternProject(data=request.query_params)
        serializ.is_valid(raise_exception=True)
        project_id = serializ.validated_data.get('project_id',None)
        org_id = serializ.validated_data.get('org_id',None)
        
        if project_id == None:
            queryset     = self.get_queryset(org_id).order_by('-created_at')
        else:
            queryset     = self.get_queryset(org_id).filter(project_id=project_id).order_by('-created_at')
        
        start_date  = serializ.validated_data.get('start_date', None)
        end_date    = serializ.validated_data.get('end_date', None)
        date_type = serializ.validated_data.get('date_type', None)
        
        if start_date == None:
            
            result_page=self.paginate_queryset(queryset)
            serializer=serializers.PatternAllListSerializer(result_page,many=True,context={'request': request})
        else:
            
            if date_type == "created_at":
                queryset=queryset.filter(
                        Q(created_at__date__range=(start_date,end_date))
                    ).distinct()
            else:
                queryset=queryset.filter(
                        Q(updated_at__date__range=(start_date,end_date))
                    ).distinct()
        
        result_page=self.paginate_queryset(queryset)
        serializer=serializers.PatternAllListSerializer(result_page,many=True,context={'request': request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(
    tags=['Pattern'],
    request   = None,
    responses = {202: dict,
            404: dict,})
    def destroy(self, request,pk):
        """
        Delete patternsections
        """
        
        try:
            pattern_obj=models.Pattern.objects.filter(id=pk)
            pattern_obj.delete()
            return Response(data={'detail': 'Pattern deleted successfully'}, status=status.HTTP_202_ACCEPTED)

        except models.PatternSection.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


    @extend_schema(
        tags=['Pattern'],
        request   = serializers.PatternUpdationSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
    )     
    def update(self, request, pk=None):
        """
        Update patterns, section, subsection \n
        @TODO:
        \n 
        \t-if edit_pattern_section == true\n 
        \t\t- title *required field\n
        \t-if edit_pattern_section == false\n
        \t\t- pattern_section_id and pattern_section *required field
        """
        try:
            instance = models.Pattern.objects.filter(pk=pk).first()
            serializer = serializers.PatternUpdationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            title            : str = serializer.validated_data.get('title', None)
            description      : str = serializer.validated_data.get('description', None)
            pattern_section  = serializer.validated_data.get('section', None)
            
            try:
                
                
                result=utils.update_pattern(instance,title,description,pattern_section,request)
                
                    
            except exceptions.ExistsError as e:
                    return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        except models.Pattern.DoesNotExist:
                return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)



    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternFontSerializer,

    responses = {201: dict})

    @action(detail=False,methods=['post'], url_path='font_upload')

    def font_upload(self, request):
        """
        Add pattern sections\n
        Params 
        ------
        name      : Font name
        file      : Font file
        generic   : generic name
        font_type  :file/url
        url        :url
        """
        serializer = serializers.PatternFontSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name : str = serializer.validated_data.get('name', None)
        file : str = serializer.validated_data.get('file', None)
        generic: str = serializer.validated_data.get('generic', None)
        font_type: str = serializer.validated_data.get('font_type', None)
        url: str = serializer.validated_data.get('url', None)
        try:
            result=utils.patten_font_upload(name ,file,generic,font_type,url)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response(data={'detail': 'Font file uploaded successfully'}, status=status.HTTP_201_CREATED)




#======================================#
#   PATTERNS CRUD API END              #
#======================================#


#======================================#
#   PATTERN FILTER API  START          #
#======================================#

class PatternFilterApi(viewsets.ViewSet):
    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternFilterSerializer,
    responses = {200: dict})
    def filter(self,request):
        try:
            role = user_model.Role.objects.get(user = self.request.user).role
        
            if role=='admin':
                organization = user_model.Role.objects.get(user = self.request.user).organization
                projectobj = list(prg_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
                queryset = models.Pattern.objects.filter(project_id__in=projectobj)


            elif role == 'user':
                organization = user_model.Role.objects.get(user = self.request.user).organization
                projectobj = list(prg_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
                queryset = models.Pattern.objects.filter(project_id__in=projectobj)
                
            else:
                queryset = models.Pattern.objects.all().order_by("-created_at")

                
            serializer = serializers.PatternFilterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            start_date  = serializer.validated_data.get('start_date', None)
            end_date    = serializer.validated_data.get('end_date', None)
            date_type = serializer.validated_data.get('date_type', None)
            if date_type == "created_at":
                queryset=queryset.filter(
                        Q(created_at__date__range=(start_date,end_date))
                    ).distinct()
            else:
                queryset=queryset.filter(
                        Q(updated_at__date__range=(start_date,end_date))
                    ).distinct()
            # print("qr",queryset)
            # queryset=self.filter_queryset(queryset)  
            serializer_class = serializers.PatternFilterListSerializer(queryset,many=True,context={'request': request})
            # instance = models.BluePrint.objects.filter(id=pk)
            # serializer  = serializers.BlueprintGetSerilizer(instance,many=True)
        except models.Pattern.DoesNotExist:
            return Response({"detail": "Pattern does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data={"detail": "Data Fetched Successfully","data":serializer_class.data}, status=status.HTTP_200_OK)


#======================================#
#   PATTERN FILTER API  END            #
#======================================#


#======================================#
#   PATTERN NOTIFICATION API START     #
#======================================#


class NotificationView(viewsets.ViewSet):
    @extend_schema(
        tags=['Pattern'])
    def list(self,request):
        try:
            arguments= utils.patter_notifications(request)
            return Response(data={"detail": "Notification fetched","data":arguments}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.PatternNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.PatternNotification.objects.filter(id__in=notif_list,action_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


class NotifiMarkAsRead(viewsets.ViewSet):
    
    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.PatternNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.PatternNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


#======================================#
#   PATTERN NOTIFICATION API END       #
#======================================#



#=============================================#
#   PATTERN DOCUMENTATION SHARE API START     #
#=============================================#


class DocumentShare(viewsets.ViewSet):
    @extend_schema(
        tags=['Pattern'],
    request   = serializers.PatternDocumentShareSerializer,
    responses = {200: dict})
    def create(self,request):
        try:
            user= request.user
            serializer = serializers.PatternDocumentShareSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(sender=user)
            pattern_id = serializer.validated_data["pattern_id"]
            message = serializer.validated_data["message"]
            if obj:
                receiver_user = obj.receiver
                email_args = {
                'full_name': f"{receiver_user.first_name} {receiver_user.last_name}".strip(),
                'email': receiver_user.username,
                'origin'  : f"{configurations.PATTERN_SHARE_URL}{pattern_id}",
                'app'    : "Pattern Library",
                'message':message
                }
                # Send Email as non blocking thread. Reduces request waiting time.
                t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_pattern_document_email)
                t.start() 
            return Response(data={"detail": "Successfully Shared "}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)








#=============================================#
#   PATTERN DOCUMENTATION SHARE API END       #
#=============================================#


