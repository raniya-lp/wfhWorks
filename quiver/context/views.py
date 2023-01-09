from asyncio import tasks
from email.policy import default
from xmlrpc.client import boolean
from django.forms import CharField, IntegerField
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes as _permission_classes
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from generics import permissions,exceptions
from rest_framework import status, generics
from . import serializers
from . import models
from . import utils
import threading
from django.conf import settings
from users import models as user_models
from projects import models as project_model
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from uuid import UUID
from django.db.models import Q
from projects import models as prg_model
from users import models as user_model
from users import functions as user_fn
from users import configurations

@extend_schema(
    tags=['Context'],
    request   = None,
    responses = {
            200: dict,
            404: dict,
        }) 
class CanvasType(APIView):
    """
    A simple ViewSet for viewing and editing accounts.
    
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin ,]
    def get(self, request):
        queryset     = models.CanvasType.objects.all()
        serializer  = serializers.CanvasTypeSerializer(queryset, many=bool)
        return Response(serializer.data)


class Canvas(GenericViewSet):
    # permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin ,]
    pagination_class = LimitOffsetPagination
    serializer_class= serializers.CanvasSerializers
    def get_queryset(self):
        project_list=[]
        role = user_models.Role.objects.get(user = self.request.user).role
        
        if role=='admin':
            organization = user_models.Role.objects.get(user = self.request.user).organization
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
            # for projects in projectobj:
            #     project_id = projects['project']
            #     project_list.append(project_id)
            return models.Canvas.objects.filter(project_id__in=projectobj)
        elif role == 'user':
            user_id = self.request.user.id
            canvas=models.CanvasMembers.objects.filter(user_id=user_id).values_list('canvas',flat=True)
            canvas_share = models.CanvasShare.objects.filter(receiver_id=user_id).values_list('canvas',flat=True)
            final_list = list(canvas) + list(canvas_share)
            fl = [*set(final_list)]
            return models.Canvas.objects.filter(id__in=fl)
        else:
            return models.Canvas.objects.all()
    @extend_schema(
        tags=['Context'],
        request   = serializers.CanvasSerializers,
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
    )
    def create(self,request):
        serializer=serializers.CanvasSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.validated_data.get('project',None)
        if project is None:
            return Response(data={"error":["The project id should not be null"]},status=status.HTTP_400_BAD_REQUEST)
    
        title : CharField = serializer.validated_data.get('title',None)
        description : CharField = serializer.validated_data.get('description',None)
        user_type : CharField = serializer.validated_data.get('user_type',None)
        canvas_type : IntegerField = serializer.validated_data.get('canvas_type',None)
        user_list = serializer.validated_data.get('user_list')
        try:
            result=utils.canvas_creation(project,title,description,user_type,canvas_type,request.user,user_list)
            if user_type == 's':
                userid= request.user.id
                canvasid =  result.id 
                canvasmember = models.CanvasMembers.objects.create(canvas_id=canvasid,user_id_id=userid,count=0)
                #canvas_id=pk,user_id_id=user_id

        except exceptions.ExistsError as e:
            return Response(data={"detail":e.message},status=status.HTTP_409_CONFLICT)
        return Response(data={"id":result.id}, status=status.HTTP_201_CREATED)
    @extend_schema(
        tags=['Context'],
        request   = serializers.CanvasSerializers,
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
        serializ=serializers.CanvasProject(data=request.query_params)
        serializ.is_valid(raise_exception=True)
        project_id = serializ.validated_data.get('project_id',None)
        if project_id == None:
            queryset     = self.get_queryset().order_by('-created_at')
        else:
            queryset     = self.get_queryset().filter(project_id=project_id).order_by('-created_at')
        result_page=self.paginate_queryset(queryset)
        serializer=serializers.CanvasListSerializers(result_page,many=True,context={'user_id': request.user.id})
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        tags=['Context'],
        request   = serializers.CanvasUpdateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        }
)
    def update(self,request,pk=None):
        serializer=serializers.CanvasUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title : CharField = serializer.validated_data.get('title',None)
        description : CharField = serializer.validated_data.get('description',None)
        # user_type : CharField = serializer.validated_data.get('user_type',None)
        # canvas_type : IntegerField = serializer.validated_data.get('canvas_type',None)
        try:
            canvas = models.Canvas.objects.get(id=pk)
            utils.canvas_update(canvas,title,description,request) 
        except models.Canvas.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)

    # def singlecanvas(self,request,pk):
    #     canvas = models.Canvas.objects.filter(id=pk)
    #     serializer  = serializers.CanvasviewSerializers(canvas,many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
        tags=['Context'],
        request   = serializers.CanvasUpdateSerializer,
        responses = {
            201: dict,
            404: dict,
            409: dict
        } 
    )
    def destroy(self, request, pk=None):
        try:
            instance = models.Canvas.objects.get(id=pk)
        except models.Canvas.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)


class CanvasTask(viewsets.ViewSet): 
    # permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin ,] 
    permission_classes  = [AllowAny] 
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasTaskSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create Task
        """
        serializer = serializers.CanvasTaskSerializer(data=request.data)
        canvas_id: str = request.data.get('canvas_id', None)
        if canvas_id is None:
            return Response(data={"error": ["The canvas id should not be null"]}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        tasklist = serializer.validated_data.get('tasklist',None)
        canvatask=[]
        for i in tasklist:
            check=models.CanvasTask.objects.filter(canvas_id=canvas_id,question=i["question"])
            if check:
                return Response(data={"detail":i["question"]+' already exists'}, status=status.HTTP_409_CONFLICT)
            else:
                task =models.CanvasTask(canvas_id=canvas_id,question=i["question"],description=i["descriptionlist"],attachments=i["attachments"])
                canvatask.append(task)
        result=models.CanvasTask.objects.bulk_create(canvatask)
        return Response(data={"id":task.id},status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasTaskUpdateSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})        
    def update(self,request,pk=None):
        serializer=serializers.CanvasTaskUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question : str = serializer.validated_data.get('question',None)
        description : str = serializer.validated_data.get('description',None)
        attachments = serializer.validated_data.get('attachments')
       
        try:
            # task = models.CanvasTask.objects.get(id=pk)
            # utils.canvas_task_update(task,question,description,attachments)
            models.CanvasTask.objects.filter(id=pk).update(question=question, description=description,attachments=attachments) 
        except models.CanvasTask.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED) 
   
    @extend_schema(
    tags=['Context'],
    request   = serializers.TaskviewSerializers,
    responses = {201: dict,
            404: dict,
            409: dict})  
    def singletask(self,request,pk):
        task = models.CanvasTask.objects.filter(canvas=pk).order_by('created_at')
        if task is None:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer  = serializers.CanvasTasksListSerializer(task,many=True,context={'user':request.user})
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)  
    
    @extend_schema(
    tags=['Context'],
    request   = serializers.TaskviewSerializers,
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def destroy(self, request, pk=None):
        try:
            instance = models.CanvasTask.objects.get(id=pk)
        except models.CanvasTask.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)

class PriorityList(GenericViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasPrioritySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})   
 
    def get_list(self,request,pk):
        canvas_P =  models.Priority.objects.filter(canvas_type__in=models.Canvas.objects.filter(id=pk).values('canvas_type'))
        serializer=serializers.CanvasPrioritySerializer(canvas_P,many=True)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)  

class CanvasNotes(GenericViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasNotes,
    responses = {201: dict,
            404: dict,
            409: dict})  

    def create(self, request, *args, **kwargs):
        serializer=serializers.CanvasNotes(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_by =  request.user
        canvas = serializer.validated_data.get('canvas',None)
        if canvas is None:
            return Response(data={"error": ["The member id should not be null"]}, status=status.HTTP_400_BAD_REQUEST)
        question_list = serializer.validated_data.get('question_list',None)
        noteslist=[]
        for question in question_list: 
            models.CanvasNotes.objects.filter(canvas_task=question["canvas_task"]).delete()
            for answer in question["answer"]:
                check=models.CanvasNotes.objects.filter(canvas_task=question["canvas_task"],answer=answer["notes"])
                if check:
                    return Response(data={answer["notes"]+' already exists'}, status=status.HTTP_409_CONFLICT)
                else:
                    task =models.CanvasNotes(canvas_task_id=question["canvas_task"],answer=answer["notes"],priority_id=answer["priority"],colour=answer["colour"],created_by=created_by)
                    noteslist.append(task)
                task_object=models.CanvasNotes.objects.filter(canvas_task=question["canvas_task"],created_by=request.user)

        result=models.CanvasNotes.objects.bulk_create(noteslist)
        serializer=serializers.CanvasTaskNotesSerializer(task_object,many=True)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
        # return Response(data={task_object},status=status.HTTP_201_CREATED)
    
    # @extend_schema(
    # tags=['Context'],
    # request   = serializers.CanvasViewSerializer,
    # responses = {201: dict,
    #         404: dict,
    #         409: dict}) 
    # def list(self,request,pk):
    #     # user=user_models.User.objects.get(user = self.request.user)
    #     # queryset = models.CanvasNotes.objects.filter(canvas_task__in=models.Canvas.objects.filter(id=pk).values('canvas_task'),created_by=request.user)
    #     canvas = models.Canvas.objects.filter(id=pk)
    #     serializer=serializers.CanvasViewSerializer(canvas,many=True)
    #     return Response(serializer.data)
   
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasNotesSerializers,
    responses = {201: dict,
            404: dict,
            409: dict})
    def update(self,request,pk=None):
        serializer=serializers.CanvasNotesSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer : CharField = serializer.validated_data.get('notes',None)
        priority : IntegerField = serializer.validated_data.get('priority',None)
        colour : CharField = serializer.validated_data.get('colour',None)
        
        try:
            notes = models.CanvasNotes.objects.get(id=pk)
            print("kg")
            utils.notes_update(notes,answer,priority,colour) 
        except models.CanvasNotes.DoesNotExist:
            return Response({"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        task_object=models.CanvasNotes.objects.filter(canvas_task=notes.canvas_task_id,created_by=request.user)    
        serializer=serializers.CanvasTaskNotesSerializer(task_object,many=True)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
        # return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
    @extend_schema(
    tags=['Context'],
    responses = {201: dict,
            404: dict,
            409: dict})  

    def destroy(self, request, pk=None):
        try:
            instance = models.CanvasNotes.objects.get(id=pk)
        except models.CanvasNotes.DoesNotExist:
            return Response(data={"detail": f"{pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)    


class CanvasMembersview(viewsets.ViewSet):
    permissions_class =[permissions.IsOrganizationAdmin,]
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasMemberSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})   
    def create(self,request):
        serializer = serializers.CanvasMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        canvas_id: str = request.data.get('canvas_id', None)
        existing_list = serializer.validated_data.get('existing_list', None)
        new_member_user = serializer.validated_data.get('new_member_user', None)
        organization = user_models.Role.objects.get(user = self.request.user).organization
        try:
           utils.create_user(new_member_user,organization,canvas_id)
           utils.existing_user(canvas_id,existing_list)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)   
        return Response(data={'detail': ' created successfully'}, status=status.HTTP_201_CREATED)    


class DeleteCanvas(APIView):
    @extend_schema(
    tags=['Context'],
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def delete(self,request):
        serializer = serializers.CanvasDeleteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        canvas_id=serializer.validated_data.get('canvas_id', None)

        try:
            instance = models.Canvas.objects.get(id=canvas_id)
        except models.Canvas.DoesNotExist:
            return Response(data={"detail": f"{canvas_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(data={"status": "success"}, status=status.HTTP_202_ACCEPTED)  
   

class CanvasDetails(viewsets.ViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasSingleGetSerializer,
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def list(self,request,pk):
        canvas = models.Canvas.objects.filter(id=pk)
        serializer  = serializers.CanvasSingleGetSerializer(canvas,many=True)

        #For canvas notification status change
        if canvas:
           a = models.CanvasNotification.objects.filter(canvas__in=canvas,org_user=request.user,action_type__in=["create","update"],higlight_status="unseen",action_status__in=["unseen","seen"]).update(higlight_status="seen",action_status="seen")
          
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)  
        
class Canvasview(viewsets.ViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasViewSerializer,
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def list(self,request,pk):
        try:
          #  a =  models.Canvas.objects.get(id=pk)
            canvas = models.Canvas.objects.filter(id=pk)
            serializer  = serializers.CanvasViewSerializer(canvas,many=True,context={'user':request.user})
            return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
        except models.Canvas.DoesNotExist:
            
            return Response(data={"detail": "Canvas not exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response(data={"detail": e}, status=status.HTTP_400_BAD_REQUEST)

class CanvasInfo(GenericViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasInfoSerializer,
    responses = {201: dict,
            404: dict,
            409: dict}) 
    @method_decorator(csrf_exempt)
    def list(self,request,pk):
        try:
            canvas = models.Canvas.objects.filter(id=pk)
            serializer  = serializers.CanvasInfoSerializer(canvas,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except models.Canvas.DoesNotExist:
            
            return Response(data={"detail": "Canvas not exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response(data={"detail": e}, status=status.HTTP_400_BAD_REQUEST)
        


class CanvasStatus(APIView):
    @extend_schema(
    tags=['Context'],
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def put(self,request,pk):
        user_id =  request.user.id
        count=1
        member=models.CanvasMembers.objects.filter(canvas_id=pk,user_id_id=user_id).first()
        if member is None:
            return Response({"detail": f"member not found"}, status=status.HTTP_404_NOT_FOUND)
        utils.count_update(member,count) 
        return Response({"detail": f"Task Completed "}, status=status.HTTP_202_ACCEPTED)

    
    @extend_schema(
    tags=['Context'])
    def get(self,request,pk):
        user_id =  request.user.id
        
        #canvas =  models.CanvasMembers.objects.filter(canvas_id=pk,user_id_id=user_id).values("count")
        canvas =  models.CanvasMembers.objects.filter(canvas_id=pk).first()
       
        try:
            if canvas is not None:
                return Response(data={"is_submitted": canvas.count}, status=status.HTTP_202_ACCEPTED)    
   
            else:
                return Response({"detail": f"member not found"}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT) 
from itertools import chain
class canvaslist(GenericViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class= serializers.CanvasSerializers
    def get_queryset(self,org_id):
        role = user_models.Role.objects.get(user = self.request.user).role
        
        if role=='admin':
            organization = user_models.Role.objects.get(user = self.request.user).organization
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
            # for projects in projectobj:
            #     project_id = projects['project']
            #     project_list.append(project_id)
            return models.Canvas.objects.filter(project_id__in=projectobj)
        elif role == 'user':
            
            user_id = self.request.user.id
            
            canvas_member = models.CanvasMembers.objects.filter(user_id=user_id).values_list('canvas',flat=True)
            canvas_share =models.CanvasShare.objects.filter(receiver_id=user_id).values_list('canvas',flat=True)
            
            # model_combination = list(chain(canvas_member, canvas_share))
            # canvas=(canvas_member or  canvas_share).values_list('canvas',flat=True)
            # canvas_share = models.CanvasShare.objects.filter(receiver_id=user_id).values_list('canvas',flat=True)
            final_list = list(canvas_member) + list(canvas_share)
            fl = [*set(final_list)]
            
            return models.Canvas.objects.filter(id__in=fl)
        else:
            if org_id == None :
                return models.Canvas.objects.all().order_by('-created_at')
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=org_id).values_list('project',flat=True))
            return models.Canvas.objects.filter(project_id__in=projectobj)  
    @extend_schema(
        tags=['Context'],
        request   = serializers.CanvasSerializers,
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
        serializ=serializers.CanvasProject(data=request.query_params)
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
            serializer=serializers.CanvasListSerializers(result_page,many=True,context={'user_id': request.user.id})
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
        serializer=serializers.CanvasListSerializers(result_page,many=True,context={'user_id': request.user.id})
        return self.get_paginated_response(serializer.data)
                  
class NotificationView(viewsets.ViewSet):
    permission_classes=[permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser]
    @extend_schema(
        tags=['Context'])
    
    def list(self,request):
        try:
            arguments= utils.context_notifications(request)
            return Response(data={"detail": "Notification fetched","data":arguments}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    
    @extend_schema(
        tags=['Context'],
    request   = serializers.ContextNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.ContextNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.CanvasNotification.objects.filter(id__in=notif_list,action_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

class NotifiMarkAsRead(viewsets.ViewSet):
    
    @extend_schema(
        tags=['Context'],
    request   = serializers.CanvasNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = serializers.CanvasNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = models.CanvasNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


#======================================#
#   CANVAS  NOTIFICATION API END       #
#======================================#
class CanvasUserResponse(viewsets.ViewSet):
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasViewSerializer,
    responses = {201: dict,
            404: dict,
            409: dict}) 
    def list(self,request):
        try:
            serializ=serializers.CanvasViewsSerializer(data=request.query_params)
            serializ.is_valid(raise_exception=True)
            canvas_id = serializ.validated_data.get('canvas_id',None)
            user_id = serializ.validated_data.get('user_id',None)
            if user_id == None:
                user_id=request.user.id
            canvas = models.Canvas.objects.filter(id=canvas_id)
            serializer  = serializers.CanvasViewSerializer(canvas,many=True,context={'user':user_id})
            return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
        
        except models.Canvas.DoesNotExist:
            return Response(data={"detail": "Canvas not exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response(data={"detail": e}, status=status.HTTP_400_BAD_REQUEST)

class TaskCreationComplete(APIView):
    @extend_schema(
    tags=['Context'],
    responses = {201: dict,
            404: dict,
            409: dict})
    def post(self,request,pk):
        try:
            task=models.Canvas.objects.filter(id=pk).first() 
        except models.Canvas.DoesNotExist:
            return Response(data={"detail": "Canvas not exist"}, status=status.HTTP_404_NOT_FOUND)  
        organization = user_models.Role.objects.get(user = self.request.user).organization
        if organization is None:
            organization = prg_model.ProjectsOrganizationMapping.objects.get(project_id=task.project_id).organization

        utils.update_canvas_status(task)
        if task.user_list:
            utils.create_userlist(task.user_list,organization,task.id,request)
        else:
            canvas_member = models.CanvasMembers.objects.filter(canvas=task).values_list('user_id',flat=True)
            #For canvas notificationorganization
            canvas_obj = models.Canvas.objects.filter(id=task.id).first()
            # usr_lst = []        
            # list(map(lambda user: usr_lst.append(user.user_id.id), canvas_member))

            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=canvas_obj.project).values_list('organization',flat = True).get()
                org_user_list = user_models.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)  
            else:
                organization = user_models.Role.objects.filter(user=request.user).first()
                org_user_list = user_models.Role.objects.filter(organization=organization.organization,role__in=[user_models.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)     
            super_admin_list = user_models.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)
            final_user = list(canvas_member) + list(super_admin_list) + list(org_user_list)
            final_user = [*set(final_user)]
            
            canvas_notif = list(map(lambda user: models.CanvasNotification(canvas_id=task.id,action_user=request.user,action_type="create",org_user_id=user), final_user))
            models.CanvasNotification.objects.bulk_create(canvas_notif)
        return Response(data={"detail": "Created"}, status=status.HTTP_202_ACCEPTED) 
        



#=======================================#
#     CANVAS COMMENTS CRUD VIEW         #
#=======================================#

class CanvasCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete canvass comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    # serializer_class    = serializers.CanvasCreateSerializer
    request   = serializers.CanvasCommentSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,canvas):
        comments = models.CanvasComments.objects.filter(canvas_id= canvas)
        
        if comments:
             
            return comments
        else:
            return "NA"
    
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasCommentSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create canvas comments
        """
        try:
            serializer = serializers.CanvasCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)

            
            #For canvas notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.canvas.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                canvas_member = models.CanvasMembers.objects.filter(canvas=instance.canvas).values_list('user_id',flat=True)

                final_user = list(canvas_member) + list(super_admin_list) + list(org_user_list)

                final_user = [*set(final_user)]
                canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=instance.canvas,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.CanvasNotification.objects.bulk_create(canvas_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                canvas_member = models.CanvasMembers.objects.filter(canvas=instance.canvas).values_list('user_id',flat=True)

                final_user = list(canvas_member) + list(super_admin_list) + list(user_list)

                final_user = [*set(final_user)]
                canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=instance.canvas,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                models.CanvasNotification.objects.bulk_create(canvas_notif)
                
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)


    

    @extend_schema(
    tags=['Context'],
    request   = None,
    parameters=[

      OpenApiParameter(name='canvas_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.CanvasCommentListSerializer})
    
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        canvas = request.query_params.get('canvas_id')
        querset     = self.get_queryset(canvas)
        if querset != "NA":
            
            serializer  = serializers.CanvasCommentListSerializer(querset,many=True)
            comments_count = models.CanvasComments.objects.filter(canvas_id= canvas).values_list("id",flat=True)
            
            canvas = models.CanvasNotification.objects.filter(comment__in=list(comments_count),org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")

            reply_dt = models.CanvasCommentsReply.objects.filter(canvas_comment__in= comments_count).values_list("id",flat=True)
            
            
            canvas_reply = models.CanvasNotification.objects.filter(reply__in=list(reply_dt),org_user=request.user,action_type="reply",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            # return Response(serializer.data) 
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'No Comments found'}, status=status.HTTP_200_OK)

    
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasCommentUpdateSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.CanvasCommentUpdateSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.CanvasComments.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.CanvasCommentUpdateSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Context'],
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
        obj     = models.CanvasComments.objects.filter(id=comment_id)
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
    serializer_class    = serializers.CanvasCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        comments = models.CanvasComments.objects.filter(pk= pk).first()
        serializer = serializers.CanvasCommentListSerializer(comments)
        if comments:
                canvas = models.CanvasNotification.objects.filter(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
             
        return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
       

class SingleCommentReply(APIView):
    """
    APIs to get single comment
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.CanvasCommentListSerializer
    request   = None,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }

    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasCommentListSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})

    def get(self,request,pk):
        reply = models.CanvasCommentsReply.objects.filter(pk=pk).first()
        if reply:
            
            comments = models.CanvasComments.objects.filter(pk=reply.canvas_comment.id).first()
            serializer = serializers.CanvasCommentListSerializer(comments)
            if comments:
                    canvas = models.CanvasNotification.objects.filter((Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")|Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen")) | (Q(comment=comments,org_user=request.user,action_type="comment",higlight_status="unseen")&Q(reply=reply,org_user=request.user,action_type="reply",higlight_status="unseen"))).update(higlight_status="seen",action_status="seen")

                   
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
                
        
       



class CanvasReplyCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete canvass comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = serializers.CanvasReplySerializer
    request   = serializers.CanvasReplySerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,canvas):
        comments = models.CanvasComments.objects.filter(canvas_id= canvas)
        
        if comments:
             
            return comments
        else:
            return "NA"
  
    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasReplySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    

    def reply_comments(self, request, *args, **kwargs):
        """
        Create canvas comments
        """
        try:
            serializer = serializers.CanvasReplySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            #For canvas notificationorganization
            if request.user.is_superuser:
                org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=instance.canvas_comment.canvas.project).values_list('organization',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)
                
                canvas_member = models.CanvasMembers.objects.filter(canvas=instance.canvas_comment.canvas).values_list('user_id',flat=True)

                final_user = list(canvas_member) + list(super_admin_list) + list(org_user_list)

                final_user = [*set(final_user)]
                canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=instance.canvas_comment.canvas,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.CanvasNotification.objects.bulk_create(canvas_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                canvas_member = models.CanvasMembers.objects.filter(canvas=instance.canvas_comment.canvas).values_list('user_id',flat=True)

                final_user = list(canvas_member) + list(super_admin_list) + list(user_list)

                final_user = [*set(final_user)]
                canvas_notif = list(map(lambda user: models.CanvasNotification(canvas=instance.canvas_comment.canvas,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                models.CanvasNotification.objects.bulk_create(canvas_notif)
            
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Context'],
    request   = serializers.CanvasReplyUpdationSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: serializers.CanvasReplyUpdationSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = models.CanvasCommentsReply.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = serializers.CanvasReplyUpdationSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Context'],
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
        obj     = models.CanvasCommentsReply.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    



#======================================#
#   CANVAS CRUD API END                #
#======================================#


#=============================================#
#   CANVAS  DOCUMENTATION SHARE API START     #
#=============================================#


class DocumentShare(viewsets.ViewSet):
    @extend_schema(
        tags=['Context'],
    request   = serializers.CanvasDocumentShareSerializer,
    responses = {200: dict})
    def create(self,request):
        try:
            user= request.user
            serializer = serializers.CanvasDocumentShareSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(sender=user)
            canvas_id = serializer.validated_data["canvas_id"]
            message = serializer.validated_data["message"]
            if obj:
                receiver_user = obj.receiver
                email_args = {
                'full_name': f"{receiver_user.first_name} {receiver_user.last_name}".strip(),
                'email': receiver_user.username,
                'origin'  : f"{configurations.CONTEXT_SHARE_URL}{canvas_id}",
                'app'    : "Context",
                'message':message
                }
                
                # Send Email as non blocking thread. Reduces request waiting time.
                t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_canvas_document_email)
                t.start() 
            return Response(data={"detail": "Successfully Shared "}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)



#=============================================#
#   CANVAS  DOCUMENTATION SHARE API END       #
#=============================================#
class CanvasFilterApi(viewsets.ViewSet):
   
    def get_queryset(self):
        
        role = user_models.Role.objects.get(user = self.request.user).role
        
        if role=='admin':
            organization = user_models.Role.objects.get(user = self.request.user).organization
            projectobj = list(project_model.ProjectsOrganizationMapping.objects.filter(organization=organization).values_list('project',flat=True))
            # for projects in projectobj:
            #     project_id = projects['project']
            #     project_list.append(project_id)
            return models.Canvas.objects.filter(project_id__in=projectobj)
        elif role == 'user':
            user_id = self.request.user.id
            canvas=models.CanvasMembers.objects.filter(user_id=user_id).values_list('canvas',flat=True)
            return models.Canvas.objects.filter(id__in=canvas)
        else:
            return models.Canvas.objects.all()
    @extend_schema(
        tags=['Context'],
    request   = serializers.CanvasFilterSerializer,
    responses = {200: dict})
    def filter(self,request):
       
        try:
            queryset     = self.get_queryset().order_by('-created_at')
            serializer = serializers.CanvasFilterSerializer(data=request.data)
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
            serializer_class = serializers.CanvasFilterListSerializer(queryset,many=True)
            # instance = models.BluePrint.objects.filter(id=pk)
            # serializer  = serializers.BlueprintGetSerilizer(instance,many=True)
        except models.Canvas.DoesNotExist:
            return Response({"detail": "Pattern does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data={"detail": "Data Fetched Successfully","data":serializer_class.data}, status=status.HTTP_200_OK)