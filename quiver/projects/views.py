from rest_framework.response import Response
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes as _permission_classes
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import status, viewsets
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from generics import mixins
from generics import permissions
from generics import exceptions
from users import models as user_models
from users import utils
from . import serializers
from . import models
from . import functions
import datetime
import pytz
from uuid import UUID
from rest_framework.viewsets import GenericViewSet
from users import models as user_models
from projects import models as project_model
from . import utils as pr_utils
from rest_framework.pagination import LimitOffsetPagination
import threading
from users import configurations
from users import functions as user_fn
from patterns import models as pattern_model
from context import models as context_model
from blueprint import models as blueprint_model


class ProjectCRUDView(mixins.PermissionsPerMethodMixin,viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete projects
    """
    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.ProjectListSerializer

    def get_queryset(self):
        status = self.request.query_params.get('status','active')
        role = user_models.Role.objects.get(user = self.request.user).role
        organization = user_models.Role.objects.get(user = self.request.user).organization
        if role=='admin':
            # user_org_roles = user_models.Role.objects.filter(organization=organization).values_list('user', flat=True)
            project_org=models.ProjectsOrganizationMapping.objects.filter(organization=organization,project__status=status)
            return project_org
            # return models.Projects.objects.filter(id=project_org, status=status)
        elif role=='user':
            roadmap_id = models.Collaborator.objects.filter(user=self.request.user).values_list('roadmap',flat=True)
            project_id = models.RoadMaps.objects.filter(id__in=roadmap_id).values_list('project',flat=True)
            # return models.Projects.objects.filter(id__in=project_id, status=status)
            project_org=models.ProjectsOrganizationMapping.objects.filter(organization=organization,project__status=status,project__in=project_id)
            return project_org
        else:
            return models.ProjectsOrganizationMapping.objects.filter(project__status=status)
            # return models.Projects.objects.filter(status=status)
            

    @extend_schema(
        tags=['Common for Roadmap and Quiver'],
        request   = serializers.ProjectCreateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
    )
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def create(self, request, *args, **kwargs):
        """
        Create projects\n
        Parameters for quiver project creation\n
        \tname : name of project
        """
        serializer = serializers.ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name   : str = serializer.validated_data.get('name', None)
        project_status   : str = serializer.validated_data.get('status', 'active')
        org_id : str = serializer.validated_data.get('organization', None)
        
        try:
            obj =models.ProjectsOrganizationMapping.objects.filter(organization=org_id,project__name__iexact = name).first()
            if obj:

                return Response(data={"detail": "Product name already exist"}, status=status.HTTP_409_CONFLICT)
            
            else:
                project = functions.create_project(creator=request.user,request=request, name=name, status=project_status,org_id=org_id)
                # local_dt = timezone.localtime(project.created_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))

                #utils.user_activity_log(user=request.user,name='product created',arguments={'name':project.name, 'date':utils.time_conversion(project.created_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"create"})
        except exceptions.ExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={'detail': 'Product created successfully'}, status=status.HTTP_201_CREATED)

    @extend_schema(
    request   = None,
     parameters=[

      OpenApiParameter(name='search', required=False, type=str,location=OpenApiParameter.QUERY),
      OpenApiParameter(name='field', required=False, type=str,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.ProjectListSerializer}
    )
    # @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def list(self, request):
        """
        Lists all projects
        
        """
        
        if "search" in request.query_params:
                 search = request.query_params.get('search')
                 queryset     = self.get_queryset().order_by('-created_at')
                 queryset =queryset.filter(project__name__icontains=search)
                 if "field" in request.query_params:
                    field = request.query_params.get('field')
                    queryset     = queryset.order_by(field)
        elif "field" in request.query_params:
            field = request.query_params.get('field')
            queryset     = self.get_queryset().order_by(field)
        else:
            queryset     = self.get_queryset().order_by('-created_at')

        serializer  = self.serializer_class(queryset, many=bool)
        # print(list(queryset.values_list("project",flat=True)))
        
        roadmap_dt = models.RoadMapNotification.objects.filter(product__in=list(queryset.values_list("project",flat=True)),org_user=request.user,action_type__in=["product_create","product_update"],higlight_status="unseen").update(higlight_status="seen",action_status="seen")

        pattern_dt = pattern_model.PatternNotification.objects.filter(product__in=list(queryset.values_list("project",flat=True)),org_user=request.user,action_type__in=["product_create","product_update"],higlight_status="unseen").update(higlight_status="seen",action_status="seen")

        canvas_dt = context_model.CanvasNotification.objects.filter(product__in=list(queryset.values_list("project",flat=True)),org_user=request.user,action_type__in=["product_create","product_update"],higlight_status="unseen").update(higlight_status="seen",action_status="seen")

        blueprint_dt = blueprint_model.BluePrintNotification.objects.filter(product__in=list(queryset.values_list("project",flat=True)),org_user=request.user,action_type__in=["product_create","product_update"],higlight_status="unseen").update(higlight_status="seen",action_status="seen")
        return Response(serializer.data)

    @extend_schema(
    request   = serializers.ProjectsOrganizationSerializer,
    responses = {201: serializers.ProjectsOrganizationSerializer}
    )
    @action(detail=True,methods=['put'], url_path='project_update')

    def organizationmapping_update(self, request, pk=None):

        """
        Organizationmapping_id
        
        """
       
        serializer = serializers.ProjectsOrganizationSerializer( data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        project_name : str= serializer.validated_data.get('project_name', None) 
 
        try:
            obj=models.Projects.objects.filter(id=pk).first()
            if obj:
                instance = models.Projects.objects.filter(name__iexact = project_name).exclude(id=pk).first()
                if instance :
                    return Response(data={'detail': 'Product already exist'}, status=status.HTTP_409_CONFLICT)
                else:
                    obj.name = project_name
                    obj.save()
                    functions.product_update_notif(obj,request)
                    return Response(data={"status": "Product Updated successully"}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response(data={'detail': 'Project does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(data={'detail': 'Error fetching product'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request   = serializers.ProjectSerializer,
        responses = {201: serializers.ProjectSerializer}
    )

    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def update(self, request, pk=None):
        try:
            instance = models.Projects.objects.get(pk=pk)
        except models.Project.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = serializers.ProjectSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # local_dt = timezone.localtime(instance.updated_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
        # utils.user_activity_log(user=request.user,name='product updated',arguments={'name':instance.name, 'date':utils.time_conversion(instance.updated_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"update"})
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        responses = {
            202: dict,
            404: dict
            }
    )
    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    def destroy(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except models.Projects.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        if models.RoadMaps.objects.filter(project=instance).exists():
            models.RoadMaps.objects.filter(project=instance).delete()
        # local_dt = timezone.localtime(datetime.datetime.now().replace(tzinfo=pytz.UTC), pytz.timezone(settings.CENTRAL_TIME_ZONE))
        # utils.user_activity_log(user=request.user,name='product deleted',arguments={'name':instance.name, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S'),"type":"delete"})
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)
          
    @extend_schema(
        tags=['Quiver'],
    	request   = serializers.QuiverProjectListSerializer,
        responses = {200: dict})
    @action(detail=False,methods=['get'], url_path='list')
    def options_project_list(self, request):
        """
        Lists all projects
        
        """
        queryset     = models.Projects.objects.filter(status='active').order_by('-created_at')
        serializer  = serializers.QuiverProjectListSerializer(queryset, many=bool)
        return Response(serializer.data)

class RoadMapList(GenericViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class= serializers.RoadMapListSerializer
    def get_queryset(self,org_id):
        
        role = user_models.Role.objects.get(user = self.request.user).role
        
        if role=='admin':
            organization = user_models.Role.objects.get(user = self.request.user).organization
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
            # for projects in projectobj:
            #     project_id = projects['project']
            #     project_list.append(project_id)
            return models.RoadMaps.objects.filter(project_id__in=projectobj)
        elif role == 'user':
            user_id = self.request.user.id
            # canvas=models.CanvasMembers.objects.filter(user_id=user_id).values_list('canvas',flat=True)
            coll = (models.Collaborator.objects.filter(user=user_id)or(models.RoadMapShare.objects.filter(receiver_id=user_id)))
            collb =models.Collaborator.objects.filter(user=user_id).values_list('roadmap__id', flat=True)

            share = models.RoadMapShare.objects.filter(receiver_id=user_id).values_list('roadmap__id', flat=True)

            final_list = list(collb) + list(share)
            fl = [*set(final_list)]
            if fl:
                # print("col")
                # roadmap_ids=coll.values_list('roadmap__id', flat=True)
                roadmaps = models.RoadMaps.objects.filter(Q(id__in=fl) | Q(created_by=user_id ))
            else:
                roadmaps = models.RoadMaps.objects.filter(created_by=user_id)
            return roadmaps
        else:
           if org_id == None :
            return models.RoadMaps.objects.all().order_by('-created_at')
           projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=org_id).values_list('project',flat=True))
           return models.RoadMaps.objects.filter(project_id__in=projectobj)   
    @extend_schema(
        tags=['Roadmap'],
        request   = serializers.RoadMapListSerializer,
          parameters=[

            OpenApiParameter(name='limit', required=False, type=int,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='offset', required=False, type=int,location=OpenApiParameter.QUERY),

            ],
        responses = {
            201: dict,
            404: dict,
            409: dict
        })        
    def list(self,request):
        serializ=serializers.RoadmapProject(data=request.query_params)
        serializ.is_valid(raise_exception=True)
        org_id = serializ.validated_data.get('org_id',None)
        project_id = serializ.validated_data.get('project_id',None)
        if project_id == None:
            queryset     = self.get_queryset(org_id).order_by('-created_at')
        else:
            queryset     = self.get_queryset(org_id).filter(project_id=project_id).order_by('-created_at')   
        start_date  = serializ.validated_data.get('start_date', None)
        end_date    = serializ.validated_data.get('end_date', None)
        date_type = serializ.validated_data.get('date_type', None)
        
        if start_date == None:
            result_page=self.paginate_queryset(queryset)
            serializer=serializers.RoadMapListSerializer(result_page,many=True,context={'user_id': request.user.id})
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
        serializer=serializers.RoadMapListSerializer(result_page,many=True,context={'user_id': request.user.id})
        return self.get_paginated_response(serializer.data)    
class RoadMapView(APIView):
    """
    API for list create update and delte roadmap.
    """

    # permission_classes  = [IsAuthenticated, ]
    # serializer_class    = serializers.RoadMapListSerializer
    
    # def get(self,request,pk):

    #     try:
    #         project = models.Projects.objects.get(id=pk)
    #     except (models.Projects.DoesNotExist) as error:
    #         return Response({"detail": error.message}, status=status.HTTP_404_NOT_FOUND)
    #     try:
    #         current_role = user_models.Role.objects.get(user=request.user)
    #     except user_models.Role.DoesNotExist:
    #         Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

    #     if (current_role.role == user_models.Role.RoleName.user):
    #         coll = models.Collaborator.objects.filter(user=request.user)
    #         if coll:
    #             roadmap_ids=coll.values_list('roadmap__id', flat=True)
    #             roadmaps = models.RoadMaps.objects.filter(Q(project=project,id__in=roadmap_ids) | Q(project=project,created_by=request.user)).order_by('-created_at')
    #         else:
    #             roadmaps = models.RoadMaps.objects.filter(project=project, created_by=request.user).order_by('-created_at')
    #     else:
    #         roadmaps = models.RoadMaps.objects.filter(project=project).order_by('-created_at')
    #     return Response(data=serializers.RoadMapListSerializer(roadmaps, many=True, context={'id': pk}).data, status=status.HTTP_200_OK)
    @extend_schema(
        tags=['Roadmap'],
        request   = serializers.RoadMapCreateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        })
    def post(self, request,pk):

        serializer = serializers.RoadMapCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name  : str = serializer.validated_data.get('name', None)
        description : str = serializer.validated_data.get('description', None)
        collaborators : str  = serializer.validated_data.get('collaborators', None)
        # project_id  : str = serializer.validated_data.get('project_id', None)

        try:
            project = models.Projects.objects.get(id=pk)

        except (models.Projects.DoesNotExist,django.core.exceptions.ValidationError) as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)
        roadmap_obj= models.RoadMaps.objects.filter(name=name,project=project).first() 
        if roadmap_obj is  not None:
            return Response(data={"detail": "The RoadMap is already being used with the same name"}, status=status.HTTP_404_NOT_FOUND)    
        try:
            roadmap = functions.create_roadmap(creator=request.user, name=name, description=description, project=project, collaborators=collaborators,request=request)
            # local_dt = timezone.localtime(roadmap.created_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
            org=models.ProjectsOrganizationMapping.objects.get(project=project).organization
            utils.user_activity_log(user=request.user,name='roadmap created',arguments={'name':roadmap.name, 'date':utils.time_conversion(roadmap.created_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"create"},org_id=org,project_id=pk)
        except exceptions.ExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={'detail': 'RoadMap created successfully','roadmap_id':roadmap.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Roadmap'],
        request   = serializers.RoadMapSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        })
    def put(self,request,pk):
        try:
            roadmap = models.RoadMaps.objects.get(id=pk)
        except models.RoadMaps.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)
        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
           return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (current_role.role == user_models.Role.RoleName.user) and (roadmap.created_by.id != request.user.id) and not request.user.collaborator_set.filter(roadmap=roadmap).first().write:    
           return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.RoadMapSerializer(roadmap, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # local_dt = timezone.localtime(roadmap.updated_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
        org=models.ProjectsOrganizationMapping.objects.get(project=roadmap.project).organization
        utils.user_activity_log(user=request.user,name='roadmap updated',arguments={'name':roadmap.name, 'date':utils.time_conversion(roadmap.updated_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"update"},org_id=org,project_id=roadmap.project.id)
        collaborators = request.data.get('collaborators', None)
        
        if collaborators:
            models.Collaborator.objects.filter(roadmap=roadmap).delete()
            # users = user_models.User.objects.filter(id__in=collaborators)
            # Bulk Create Collaborators
            bulk_collaborator = [
        models.Collaborator(roadmap=roadmap, user=user_models.User.objects.get(id=i['user']),write=i['write'])
        for i in collaborators
        ]
            models.Collaborator.objects.bulk_create(bulk_collaborator)

        functions.roadmap_update_notification(roadmap,request)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    @extend_schema(
        tags=['Roadmap'],
        responses = {
            201: dict,
            404: dict,
            409: dict
        })
    def delete(self,request,pk):

        try:
            roadmap = models.RoadMaps.objects.get(id=pk)
        except models.RoadMaps.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
           return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (current_role.role == user_models.Role.RoleName.user) and (roadmap.created_by.id != request.user.id):    
           return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)
        # local_dt = timezone.localtime(datetime.datetime.now().replace(tzinfo=pytz.UTC), pytz.timezone(settings.CENTRAL_TIME_ZONE))
        org=models.ProjectsOrganizationMapping.objects.get(project=roadmap.project).organization
        utils.user_activity_log(user=request.user,name='roadmap deleted',arguments={'name':roadmap.name, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S'),"type":"delete"},org_id=org,project_id=roadmap.project.id)
        roadmap.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)


class RoadMapFeatureView(APIView):
    """
    API for list create update and delte roadmap features
    """

    permission_classes  = [IsAuthenticated, ]
    serializer_class    = serializers.RoadMapFeatureListSerializer

    def get(self,request,pk):

        try:
            roadmap = models.RoadMaps.objects.filter(id=pk).first()
        except models.RoadMaps.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        role = user_models.Role.objects.get(user =request.user.id).role
        if role =='user':
            collaborator = models.Collaborator.objects.filter(roadmap=roadmap,user=request.user.id).first()
            if collaborator:
               write = collaborator.write
            else:
                write=False    
        else:
            write= True 
 
        roadmap_features = models.RoadMapFeatures.objects.filter(roadmap=roadmap).order_by('-rice_score')
        features=serializers.RoadMapFeatureListSerializer(roadmap_features,many=True)

        a = models.RoadMapNotification.objects.filter(roadmap=roadmap,org_user=request.user,action_type__in=["create","update","feature_create","feature_update"],higlight_status="unseen",action_status__in=["unseen","seen"]).update(higlight_status="seen",action_status="seen")
        org = project_model.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).first()   
        return Response(data={"id": roadmap.id, "name": roadmap.name,"description":roadmap.description,"created_at":roadmap.created_at,"write":write,"updated_at":roadmap.updated_at,"project_id":roadmap.project_id,"project":roadmap.project.name,"org_id":org.organization.id,"org_name" :org.organization.name,"features":features.data}, status=status.HTTP_200_OK)

    def post(self, request,pk):
        
        serializer = serializers.RoadMapFeatureCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name  : str = serializer.validated_data.get('name', None)
        description : str = serializer.validated_data.get('description', None)
        image  : str = serializer.validated_data.get('image', None)
        reach  : str = serializer.validated_data.get('reach', None)
        impact  : str = serializer.validated_data.get('impact', None)
        confidence  : str = serializer.validated_data.get('confidence', None)
        effort  : str = serializer.validated_data.get('effort', None)
       

        try:
            roadmap = models.RoadMaps.objects.get(id=pk)
        except models.RoadMaps.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)
        if (current_role.role == user_models.Role.RoleName.user):
            coll = models.Collaborator.objects.filter(roadmap=roadmap, user=request.user).first()
            if coll and not coll.write:
                return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        try:
            roadmap_feature = functions.create_roadmap_features(creator=request.user, name=name, roadmap=roadmap, reach=reach, impact=impact, confidence=confidence, effort=effort, request=request,description=description,image=image)
           
            # local_dt = timezone.localtime(roadmap_feature.created_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
            org=models.ProjectsOrganizationMapping.objects.get(project=roadmap.project).organization
            utils.user_activity_log(user=request.user,name='feature created',arguments={'name':roadmap_feature.name, 'date':utils.time_conversion(roadmap_feature.created_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"create"},org_id=org,project_id=roadmap.project.id)
        except exceptions.ExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_409_CONFLICT)
        except exceptions.NotExistsError as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={'detail': 'Feature created successfully'}, status=status.HTTP_201_CREATED)


    def put(self,request,pk):
        try:
            roadmap_feature = models.RoadMapFeatures.objects.get(id=pk)
        except models.RoadMapFeatures.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (current_role.role == user_models.Role.RoleName.user):
            coll = models.Collaborator.objects.filter(roadmap=roadmap_feature.roadmap, user=request.user).first()
            if coll and not coll.write:
                return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if request.data.get('status'):
            roadmap_feature.status=request.data.get('status')
            roadmap_feature.save()

        serializer = serializers.RoadMapFeatureSerializer(roadmap_feature, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        functions.rice_calculation(roadmap_feature)
        # local_dt = timezone.localtime(roadmap_feature.updated_at, pytz.timezone(settings.CENTRAL_TIME_ZONE))
        org=models.ProjectsOrganizationMapping.objects.get(project=roadmap_feature.roadmap.project).organization
        utils.user_activity_log(user=request.user,name='feature updated',arguments={'name':roadmap_feature.name, 'date':utils.time_conversion(roadmap_feature.updated_at).strftime('%d-%m-%Y %H:%M:%S'),"type":"update"},org_id=org,project_id=roadmap_feature.roadmap.project.id)
        functions.feature_update_notification(roadmap_feature.roadmap,request,roadmap_feature)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self,request,pk):

        try:
            roadmap_feature = models.RoadMapFeatures.objects.get(id=pk)
        except models.RoadMapFeatures.DoesNotExist as error:
            return Response(data={"detail": error.message}, status=status.HTTP_404_NOT_FOUND)

        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (current_role.role == user_models.Role.RoleName.user):
            coll = models.Collaborator.objects.filter(roadmap=roadmap_feature.roadmap, user=request.user).first()
            if coll and not coll.write:
                return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)
        # local_dt = timezone.localtime(datetime.datetime.now().replace(tzinfo=pytz.UTC), pytz.timezone(settings.CENTRAL_TIME_ZONE))
        org=models.ProjectsOrganizationMapping.objects.get(project=roadmap_feature.roadmap.project).organization
        utils.user_activity_log(user=request.user,name='feature deleted',arguments={'name':roadmap_feature.name, 'date':utils.time_conversion(datetime.datetime.now().replace(tzinfo=pytz.UTC)).strftime('%d-%m-%Y %H:%M:%S'),"type":"delete"},org_id=org,project_id=roadmap_feature.roadmap.project.id)
        roadmap_id=roadmap_feature.roadmap
        roadmap_feature.delete()
        feature = models.RoadMapFeatures.objects.filter(roadmap=roadmap_id).first()
        if feature:
            functions.rice_calculation(feature)
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)

class FeatureOrderUpdateView(APIView):
    """
    API for update order of features
    """

    permission_classes  = [IsAuthenticated, ]

    def post(self, request):

        datas = request.data.get('data')
        
        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        if (current_role.role == user_models.Role.RoleName.user):
            coll = models.Collaborator.objects.filter(roadmap=roadmap_feature.roadmap, user=request.user).first()
            if coll and not coll.write:
                return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        for data in datas:
            try:
                feature = models.RoadMapFeatures.objects.get(id=data['id'])
            except:
                return Response(data={"detail": 'Feature not Found'}, status=status.HTTP_404_NOT_FOUND)
            functions.update_feature_order(data['order'],feature)
        feature_ids = [k['id'] for k in datas]
        roadmap_features = models.RoadMapFeatures.objects.filter(id__in=feature_ids)  
        return Response(data=serializers.RoadMapFeatureListSerializer(roadmap_features,many=True).data, status=status.HTTP_202_ACCEPTED)

class FeatureBulkUpdateView(APIView):
    """
    API for update order of features
    """

    permission_classes  = [IsAuthenticated, ]

    def put(self, request):

        datas = request.data.get('data')
        
        try:
            current_role = user_models.Role.objects.get(user=request.user)
        except models.Role.DoesNotExist:
            Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        # if (current_role.role == user_models.Role.RoleName.user):
        #     coll = models.Collaborator.objects.filter(roadmap=roadmap_feature.roadmap, user=request.user).first()
        #     if coll and not coll.write:
        #         return Response(data={"detail": "You do not have permission to access this."}, status=status.HTTP_403_FORBIDDEN)

        for data in datas:
            try:
                feature = models.RoadMapFeatures.objects.get(id=data['id'])
            except:
                return Response(data={"detail": 'Feature not Found'}, status=status.HTTP_404_NOT_FOUND)
            functions.bulk_update_feature(data, feature)
        
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)


class ProductDeleteView(APIView):
    @extend_schema(
        responses = {
            202: dict,
            404: dict
            }
    )

    @_permission_classes((permissions.IsSuperUser|permissions.IsOrganizationAdmin,))
    
    def delete(self, request, pk=None):
        '''
        Project Organization mapping delete
        '''
        try:
            instance = models.ProjectsOrganizationMapping.objects.get(id=pk)
            proj_id=instance.project_id
            instance.delete()
            obj = models.ProjectsOrganizationMapping.objects.filter(project_id=proj_id)
            if obj.first() is None:
                models.Projects.objects.filter(id=proj_id).delete()
            return Response(data={"status": "Product Deleted successully "}, status=status.HTTP_202_ACCEPTED)
        except models.ProjectsOrganizationMapping.DoesNotExist:
            return Response(data={"detail": "ProjectsOrganizationMapping not found"}, status=status.HTTP_404_NOT_FOUND)





#======================================#
#   ROADMAP NOTIFICATION API START     #
#======================================#


class NotificationView(viewsets.ViewSet):
    @extend_schema(
        tags=['Roadmap'])
    def list(self,request):
        try:
            arguments= pr_utils.roadmap_notifications(request)
            return Response(data={"detail": "Notification fetched","data":arguments}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Roadmap'],
    request   = serializers.RoadMapNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.RoadMapNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.RoadMapNotification.objects.filter(id__in=notif_list,action_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


class NotifiMarkAsRead(viewsets.ViewSet):
    
    @extend_schema(
        tags=['Roadmap'],
    request   = serializers.RoadMapNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.RoadMapNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.RoadMapNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


#======================================#
#   ROADMAP NOTIFICATION API END       #
#======================================#




#=======================================#
#     ROADMAP COMMENTS CRUD VIEW        #
#=======================================#

class RoadMapCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete roadmaps comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.RoadMapCommentSerializer
    request   = serializers.RoadMapCommentSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,roadmap):
        print(roadmap)
        comments = models.RoadMapComments.objects.filter(feature_id= roadmap)
        
        if comments:
             
            return comments
        else:
            return "NA"
    
    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapCommentSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create roadmap comments
        """
        try:
            # print("lplpl")
            serializer = serializers.RoadMapCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            colb_data = models.Collaborator.objects.filter(roadmap=instance.roadmap)
            usr_lst = []        
            list(map(lambda user: usr_lst.append(user.user.id), colb_data))
            # print("user",usr_lst)
            #For roadmap notificationorganization
            if request.user.is_superuser:
                org_id = models.ProjectsOrganizationMapping.objects.filter(project=instance.roadmap.project).values_list('organization',flat = True).get()
                org_user_list = user_models.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)


                final_user = list(usr_lst) + list(org_user_list) + list(super_admin_list)
                
                final_user = [*set(final_user)]
                
                roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=instance.roadmap,action_user=request.user,action_type="comment",org_user_id=user,comment=instance,feature=instance.feature), final_user))
                models.RoadMapNotification.objects.bulk_create(roadmap_notif)
            else:
                
                organization = user_models.Role.objects.filter(user=request.user).first()
                user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(usr_lst) +  list(user_list) + list(super_admin_list)

                final_user = [*set(final_user)]
                roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=instance.roadmap,action_user=request.user,action_type="comment",org_user_id=user,comment=instance,feature=instance.feature), final_user))
                models.RoadMapNotification.objects.bulk_create(roadmap_notif)
                
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)


    

    @extend_schema(
    tags=['Roadmap'],
    request   = None,
    parameters=[

      OpenApiParameter(name='feature_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.RoadMapCommentListSerializer})
    
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        roadmap = request.query_params.get('feature_id')
        querset     = self.get_queryset(roadmap)
        if querset != "NA":
            
            serializer  = serializers.RoadMapCommentListSerializer(querset,many=True)
            comments_count = models.RoadMapComments.objects.filter(feature_id= roadmap).values_list("id",flat=True)
            
            roadmap = models.RoadMapNotification.objects.filter(comment__in=list(comments_count),org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")

            reply_dt = models.RoadMapCommentsReply.objects.filter(roadmap_comment__in= comments_count).values_list("id",flat=True)
            
            
            roadmap_reply = models.RoadMapNotification.objects.filter(reply__in=list(reply_dt),org_user=request.user,action_type="reply",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            # return Response(serializer.data) 
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'No Comments found'}, status=status.HTTP_200_OK)

    
    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapCommentUpdateSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.RoadMapCommentUpdateSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.RoadMapComments.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.RoadMapCommentUpdateSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Roadmap'],
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
        obj     = models.RoadMapComments.objects.filter(id=comment_id)
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
    serializer_class    = serializers.RoadMapCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        comments = models.RoadMapComments.objects.filter(pk= pk).first()
        serializer = serializers.RoadMapCommentListSerializer(comments)
        if comments:
                roadmap = models.RoadMapNotification.objects.filter(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
             
        return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
       

class SingleCommentReply(APIView):
    """
    APIs to get single comment
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.RoadMapCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        reply = models.RoadMapCommentsReply.objects.filter(pk=pk).first()
        if reply:
            
            comments = models.RoadMapComments.objects.filter(pk=reply.roadmap_comment.id).first()
            serializer = serializers.RoadMapCommentListSerializer(comments)
            if comments:
                    roadmap = models.RoadMapNotification.objects.filter((Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")|Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen")) | (Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")&Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen"))).update(higlight_status="seen",action_status="seen")

                   
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
                
        
       



class RoadMapReplyCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete roadmaps comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.RoadMapReplySerializer
    request   = serializers.RoadMapReplySerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,roadmap):
        comments = models.RoadMapComments.objects.filter(roadmap_id= roadmap)
        
        if comments:
             
            return comments
        else:
            return "NA"
  
    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapReplySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    

    def reply_comments(self, request, *args, **kwargs):
        """
        Create roadmap comments
        """
        try:
            serializer = serializers.RoadMapReplySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            colb_data = models.Collaborator.objects.filter(roadmap=instance.roadmap_comment.roadmap)
            usr_lst = []        
            list(map(lambda user: usr_lst.append(user.user.id), colb_data))
            #For roadmap notificationorganization
            if request.user.is_superuser:
                org_id = models.ProjectsOrganizationMapping.objects.filter(project=instance.roadmap_comment.roadmap.project).values_list('organization',flat = True).get()
                org_user_list = user_models.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(usr_lst) + list(org_user_list) + list(super_admin_list)
                
                final_user = [*set(final_user)]
                roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=instance.roadmap_comment.roadmap,action_user=request.user,action_type="reply",org_user_id=user,reply=instance,feature=instance.roadmap_comment.feature), final_user))
                models.RoadMapNotification.objects.bulk_create(roadmap_notif)
            else:
                
                organization = user_models.Role.objects.filter(user=request.user).first()
                user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(usr_lst) + list(user_list) + list(super_admin_list)

                final_user = [*set(final_user)]
                roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=instance.roadmap_comment.roadmap,action_user=request.user,action_type="reply",org_user_id=user,reply=instance,feature=instance.roadmap_comment.feature), final_user))
                models.RoadMapNotification.objects.bulk_create(roadmap_notif)
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Roadmap'],
    request   = serializers.RoadMapReplyUpdationSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.RoadMapReplyUpdationSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.RoadMapCommentsReply.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.RoadMapReplyUpdationSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Roadmap'],
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
        obj     = models.RoadMapCommentsReply.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    

#=============================================#
#   PATTERN DOCUMENTATION SHARE API START     #
#=============================================#


class DocumentShare(viewsets.ViewSet):
    @extend_schema(
        tags=['Roadmap'],
    request   = serializers.RoadMapDocumentShareSerializer,
    responses = {200: dict})
    def create(self,request):
        try:
            user= request.user
            serializer = serializers.RoadMapDocumentShareSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(sender=user)
            roadmap_id = serializer.validated_data["roadmap_id"]
            message = serializer.validated_data["message"]
            if obj:
                receiver_user = obj.receiver
                email_args = {
                'full_name': f"{receiver_user.first_name} {receiver_user.last_name}".strip(),
                'email': receiver_user.username,
                'origin'  : f"{configurations.ROADMAP_SHARE_URL}{roadmap_id}",
                'app'    : "Roadmap Live",
                'message':message
                }
                # Send Email as non blocking thread. Reduces request waiting time.
                t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_roadmap_document_email)
                t.start() 
            return Response(data={"detail": "Successfully Shared "}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)








#=============================================#
#   PATTERN DOCUMENTATION SHARE API END       #
#=============================================#
class RoadmapFilterApi(viewsets.ViewSet):
    def get_queryset(self):
        
        role = user_models.Role.objects.get(user = self.request.user).role
        
        if role=='admin':
            organization = user_models.Role.objects.get(user = self.request.user).organization
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
            # for projects in projectobj:
            #     project_id = projects['project']
            #     project_list.append(project_id)
            return models.RoadMaps.objects.filter(project_id__in=projectobj)
        elif role == 'user':
            user_id = self.request.user.id
            # canvas=models.CanvasMembers.objects.filter(user_id=user_id).values_list('canvas',flat=True)
            coll = models.Collaborator.objects.filter(user=user_id)
            if coll:
                roadmap_ids=coll.values_list('roadmap__id', flat=True)
                roadmaps = models.RoadMaps.objects.filter(Q(id__in=roadmap_ids) | Q(created_by=user_id ))
            else:
                roadmaps = models.RoadMaps.objects.filter(created_by=user_id)
            return roadmaps
        else:
           return models.RoadMaps.objects.all()
    @extend_schema(
        tags=['Roadmap'],
    request   = serializers.RoadmapFilterSerializer,
    responses = {200: dict})
    def filter(self,request):
        try:
            queryset = self.get_queryset().order_by("-created_at")
            serializer = serializers.RoadmapFilterSerializer(data=request.data)
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
            serializer_class = serializers.RoadmapFilterListSerializer(queryset,many=True)
            # instance = models.BluePrint.objects.filter(id=pk)
            # serializer  = serializers.BlueprintGetSerilizer(instance,many=True)
        except models.RoadMaps.DoesNotExist:
            return Response({"detail": "Roadmap does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data={"detail": "Data Fetched Successfully","data":serializer_class.data}, status=status.HTTP_200_OK)


class RoadmapSingleGet(APIView):
    """
    API for Roadmap get
    """
    permission_classes  = [IsAuthenticated, ]
    @extend_schema(
        tags=['Roadmap'],
    request   = serializers.RoadMapsingleSerializer,
    responses = {200: dict})
    def get(self,request,pk):

       roadmap= models.RoadMaps.objects.filter(id=pk).first()
       serializer_class = serializers.RoadMapsingleSerializer(roadmap)
       return Response(data={"data":serializer_class.data},status=status.HTTP_200_OK)
