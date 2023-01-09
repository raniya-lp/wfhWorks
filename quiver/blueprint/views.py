from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import *
from . import utils
from django.conf import settings
import threading
from blueprint.models import BluePrint
from .serializers import BlueprintListSerilizer,BlueprintCreateSerializer,SectionCreateSerializer
from rest_framework.permissions import IsAuthenticated
from generics import permissions
from rest_framework import status, viewsets
from rest_framework.response import Response
from . import serializers
# from . import utils
from generics import exceptions
from users import models as user_model
from projects import models as project_model
from blueprint.models import BluePrint
from blueprint.models import Sections
from users.models import Role
from drf_spectacular.utils import extend_schema
from . import models
import json
from rest_framework.decorators import action
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from django.db.models import Q
from uuid import UUID
from projects import models as prg_model
from users import models as user_model
from users import functions as user_fn
from rest_framework.viewsets import GenericViewSet
from users import configurations
# Create your views here.







# Create your views here.

class BlueprintDataView(GenericViewSet):
    """
    APIs to create,retrieve,update and delete blueprints
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.BlueprintListSerilizer
    request   = serializers.BlueprintListSerilizer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }
    def get_queryset(self,org_id):
        role = Role.objects.get(user = self.request.user)
        if role.role=='superadmin':
            if org_id == None :
                query_set=models.BluePrint.objects.all().order_by('-created_at')
                return query_set
            projects=prg_model.ProjectsOrganizationMapping.objects.filter(organization_id=org_id).values('project')
            query_set=BluePrint.objects.filter(project__in=projects).order_by('-created_at')
        else:
            projects=prg_model.ProjectsOrganizationMapping.objects.filter(organization=role.organization).values('project')
            query_set=models.BluePrint.objects.filter(project__in=projects).order_by('-created_at')
        return query_set

    # @extend_schema(
    #     tags=['Blueprint'],
    # request   = None,
    # responses = {201: serializers.BlueprintListSerilizer}) 
   
    # def list(self, request):
    #     """
    #     Lists all blueprints
        
    #     """ 
    #      ####
    #     logged_user = request.user
    #     #print(logged_user)
    #     project_list =[]
        
    #     role = user_model.Role.objects.filter(user=logged_user).first()
        
    #     if role:
    #         if role.role == "admin" or role.role == "user":
    #             organisation = role.organization
    #             projectobj = project_model.ProjectsOrganizationMapping.objects.filter(organization=organisation).values_list('project',flat=True)
               
    #             blueprints = models.BluePrint.objects.filter(project_id__in=projectobj).order_by("-created_at")
    #         elif role.role == "superadmin":
    #             blueprints = models.BluePrint.objects.all().order_by("-created_at")
    #         serializer  = serializers.BlueprintListSerilizer(blueprints, many=bool,context={"request":request})
    #         # return Response(data={"detail": "Data Fetched Successfully","data":serializer.data}, status=status.HTTP_200_OK)
    #         return Response(serializer.data)
    #     else:
    #         return Response(data={"detail": "No Data Found","data":[]}, status=status.HTTP_200_OK)



    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BlueprintListSerilizer,
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
        serializ=serializers.BluePrintProject(data=request.query_params)
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
            serializer=serializers.BlueprintListSerilizer(result_page,many=True,context={'request': request})
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
        serializer=serializers.BlueprintListSerilizer(result_page,many=True,context={'request': request})
        return self.get_paginated_response(serializer.data)
        






    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BlueprintCreateSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create blueprints
        """
        serializer = serializers.BlueprintCreateSerializer(data=request.data)
        project_id       : str = request.data.get('project_id', None)
        
        if project_id is None:
            return Response(data={"error": ["Please select a project"]}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        title            : str = serializer.validated_data.get('title', None)
        description      : str = serializer.validated_data.get('description', None)
        blueprint_details      : json = serializer.validated_data.get('blueprint_details', None)
        created_by = request.user
        updated_by =  request.user

        if models.BluePrint.objects.filter(title=title,project_id=project_id):
            return Response(data={"error": ["The blueprint already exists"]}, status=status.HTTP_400_BAD_REQUEST)

        try:
           
            result=utils.blueprint_creation(project_id,title,description,request.user,created_by,updated_by,request,blueprint_details)
            
            blueprint_id =  result        
           
            # if blueprint_id is None:
            #     return Response(data={"error": ["The blueprint id may no be null"]}, status=status.HTTP_400_BAD_REQUEST)
               
            # else:
            #     #sectionserializer.is_valid(raise_exception=True)
            #     processdata       : str = request.data.get('processdata', None)
            #     for i in processdata:
            #         name = i['name']
            #         subline_text = i['subline_text']
            #         process_item_id = i['process_item_id']
            #         data = i['data']
            #         blueprint_id =  result 
            
            #         section_create=models.Sections.objects.create(blue_print_id=blueprint_id,name=name,subline_text=subline_text,process_item_id=process_item_id,data=data,created_by=created_by)
               
                    # section_add =  utils.section_creation(blueprint_id,name,subline_text,request.user,process_item_id,data,#created_by=1)
           
            return Response(data={"detail": " Created Successfully","data":{"blueprint_id":blueprint_id}}, status=status.HTTP_201_CREATED)
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)



    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BlueprintUpdateSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def update(self,request,pk=None):
        """
        update blueprints
        """
        
        instance = models.BluePrint.objects.get(pk=pk)
        if instance:
            serializer = serializers.BlueprintUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            title            : str = serializer.validated_data.get('title', None)
            description      : str = serializer.validated_data.get('description', None)
            blueprint_details      : json = serializer.validated_data.get('blueprint_details', None)
            try:
                result=utils.blueprint_updation(instance,title,description,request.user,request,blueprint_details)
                # utils.section_updation(instance,blueprint_section,request.user)
                return Response(data={"detail": "Updated Successfully"}, status=status.HTTP_201_CREATED)
            except exceptions.ExistsError as e:
                return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)

    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BlueprintUpdateReqstSerilizer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def destroy(self, request,pk):
        """
        Delete blueprintsections
        """
        
        try:
           instance = models.BluePrint.objects.get(pk=pk)
           if instance:
                obj = models.Sections.objects.filter(blue_print=instance)

                models.Sections.objects.filter(blue_print=instance).delete()

                instance.delete()
           return Response(data={'detail': 'Blueprint deleted successfully'}, status=status.HTTP_202_ACCEPTED)

        except models.BluePrint.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)
    




class GetSingleSectionView(APIView):
    @extend_schema(
        tags=['Blueprint'],
    request   = serializers.SectionListSerializer,

    responses = {200: dict})
    def get(self,request,pk):
        try:
            instance = models.BluePrint.objects.filter(id=pk).first()
            
            serializer  = serializers.BlueprintGetSerilizer(instance)

            if instance:

                a = models.BluePrintNotification.objects.filter(blueprint=instance,org_user=request.user,action_type__in=["create","update"],higlight_status="unseen",action_status__in=["unseen","seen"]).update(higlight_status="seen",action_status="seen")
            blueprint_share = models.BluePrintShare.objects.filter(blueprint=instance,receiver=request.user,status="sent")
            
            if blueprint_share:
                blueprint_share.update(status= "seen")
        except models.Sections.DoesNotExist:
            return Response({"detail": "Sections does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data={"detail": "Data Fetched Successfully","data":serializer.data}, status=status.HTTP_200_OK)

#=======================================#
#     blueprint NOTIFICATION  START     #
#=======================================#        

class NotificationView(viewsets.ViewSet):
    permission_classes=[permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser]
    @extend_schema(
        tags=['Blueprint'])
    
    def list(self,request):
        try:
            arguments= utils.blueprint_notifications(request)
            return Response(data={"detail": "Notification fetched","data":arguments}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    
    @extend_schema(
        tags=['Blueprint'],
    request   = serializers.BluePrinttNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.BluePrinttNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.BluePrintNotification.objects.filter(id__in=notif_list,action_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


class NotifiMarkAsRead(viewsets.ViewSet):
    
    @extend_schema(
        tags=['Blueprint'],
    request   = serializers.BluePrintNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.BluePrintNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.BluePrintNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

#=======================================#
#     blueprint NOTIFICATION  END       #
#=======================================#


#=======================================#
#     blueprint COMMENTS CRUD VIEW      #
#=======================================#

class BluePrintCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete blueprints comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.BluePrintCommentSerializer
    request   = serializers.BluePrintCommentSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,blueprint):
        comments = models.BluePrintComments.objects.filter(blueprint_id= blueprint)
        
        if comments:
             
            return comments
        else:
            return "NA"
    
    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintCommentSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create blueprint comments
        """
        try:
            serializer = serializers.BluePrintCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)

            
            #For blueprint notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.blueprint.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)

                blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=instance.blueprint,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.BluePrintNotification.objects.bulk_create(blueprint_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=instance.blueprint,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.BluePrintNotification.objects.bulk_create(blueprint_notif)
                
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)


    

    @extend_schema(
    tags=['Blueprint'],
    request   = None,
    parameters=[

      OpenApiParameter(name='blueprint_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.BluePrintCommentListSerializer})
    
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        blueprint = request.query_params.get('blueprint_id')
        querset     = self.get_queryset(blueprint)
        if querset != "NA":
            
            serializer  = serializers.BluePrintCommentListSerializer(querset,many=True)
            comments_count = models.BluePrintComments.objects.filter(blueprint_id= blueprint).values_list("id",flat=True)
            
            blueprint = models.BluePrintNotification.objects.filter(comment__in=list(comments_count),org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")


            reply_dt = models.BluePrintCommentsReply.objects.filter(blueprint_comment__in= comments_count).values_list("id",flat=True)
            
            
            blueprint_reply = models.BluePrintNotification.objects.filter(reply__in=list(reply_dt),org_user=request.user,action_type="reply",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            # return Response(serializer.data) 
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'No Comments found'}, status=status.HTTP_200_OK)

    
    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintCommentUpdateSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.BluePrintCommentUpdateSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.BluePrintComments.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.BluePrintCommentUpdateSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Blueprint'],
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
        obj     = models.BluePrintComments.objects.filter(id=comment_id)
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
    serializer_class    = serializers.BluePrintCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        comments = models.BluePrintComments.objects.filter(pk= pk).first()
        serializer = serializers.BluePrintCommentListSerializer(comments)
        if comments:
                blueprint = models.BluePrintNotification.objects.filter(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
             
        return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
       

class SingleCommentReply(APIView):
    """
    APIs to get single comment
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.BluePrintCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        reply = models.BluePrintCommentsReply.objects.filter(pk=pk).first()
        if reply:
            
            comments = models.BluePrintComments.objects.filter(pk=reply.blueprint_comment.id).first()
            serializer = serializers.BluePrintCommentListSerializer(comments)
            if comments:
                    blueprint = models.BluePrintNotification.objects.filter((Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")|Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen")) | (Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")&Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen"))).update(higlight_status="seen",action_status="seen")

                   
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
                
        
       



class BluePrintReplyCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete blueprints comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.BluePrintReplySerializer
    request   = serializers.BluePrintReplySerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,blueprint):
        comments = models.BluePrintComments.objects.filter(blueprint_id= blueprint)
        
        if comments:
             
            return comments
        else:
            return "NA"
  
    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintReplySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    

    def reply_comments(self, request, *args, **kwargs):
        """
        Create blueprint comments
        """
        try:
            serializer = serializers.BluePrintReplySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            #For blueprint notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.blueprint_comment.blueprint.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)

                blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=instance.blueprint_comment.blueprint,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.BluePrintNotification.objects.bulk_create(blueprint_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                blueprint_notif = list(map(lambda user: models.BluePrintNotification(blueprint=instance.blueprint_comment.blueprint,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.BluePrintNotification.objects.bulk_create(blueprint_notif)
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Blueprint'],
    request   = serializers.BluePrintReplyUpdationSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.BluePrintReplyUpdationSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.BluePrintCommentsReply.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.BluePrintReplyUpdationSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Blueprint'],
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
        obj     = models.BluePrintCommentsReply.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    



#======================================#
#   blueprintS CRUD API START          #
#======================================#


#=============================================#
#   PATTERN DOCUMENTATION SHARE API START     #
#=============================================#


class DocumentShare(viewsets.ViewSet):
    @extend_schema(
        tags=['Blueprint'],
    request   = serializers.BluePrintDocumentShareSerializer,
    responses = {200: dict})
    def create(self,request):
        try:
            user= request.user
            serializer = serializers.BluePrintDocumentShareSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(sender=user)
            blueprint_id = serializer.validated_data["blueprint_id"]
            message = serializer.validated_data["message"]
            if obj:
                receiver_user = obj.receiver
                email_args = {
                'full_name': f"{receiver_user.first_name} {receiver_user.last_name}".strip(),
                'email': receiver_user.username,
                'origin'  : f"{configurations.BLUEPRINT_SHARE_URL}{blueprint_id}",
                'app'    : "Service BluePrint",
                'message':message
                }
                # Send Email as non blocking thread. Reduces request waiting time.
                t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_blueprint_document_email)
                t.start() 
            return Response(data={"detail": "Successfully Shared "}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)








#=============================================#
#   PATTERN DOCUMENTATION SHARE API END       #
#=============================================#