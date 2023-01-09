from tracemalloc import start
from django.shortcuts import render,redirect
from rest_framework.response import Response 
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from . import utils
from . serializers import *
from . middleware import *
import json
from rest_framework import status,viewsets
import time
from users.models import *
from . models import *
from generics import exceptions
from rest_framework import generics
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from django.db.models import Q
from rest_framework.permissions import AllowAny

# Create your views here.

class APiByUrlView(GenericViewSet):
    @extend_schema(
        tags=['Api Services'],
        request=UrldetailsbyParmeterSerializer,
        parameters=[

            OpenApiParameter(name='limit', required=False, type=int,location=OpenApiParameter.QUERY),
            OpenApiParameter(name='offset', required=False, type=int,location=OpenApiParameter.QUERY),

            ],
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewurl(self,request,url_id):
        serializ=UrldetailsbyParmeterSerializer(data=request.query_params)
        serializ.is_valid(raise_exception=True)

        start_date  = serializ.validated_data.get('start_date', None)
        end_date    = serializ.validated_data.get('end_date', None)
        hour = serializ.validated_data.get('hour', None)
        days = serializ.validated_data.get('days', None)

        urldatas=utils.chartbyUrl(url_id,start_date,end_date,hour,days)

        return Response(data={'apiDetails':urldatas})

class UrlIdView(GenericViewSet):
    @extend_schema(
        tags=['Api Services'],
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewurl(self,request):
        urldatas=utils.urldetails()
        sv=ApiDetailsSerializer(urldatas,many=True)
        return Response(data={'apiDetails':sv.data})

class projectApiListView123(GenericViewSet):
    @extend_schema(
        tags=['Api Services'],
        request   = ListdetailsbyDateSerializer,
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
        serializ=serializers.ListdetailsbyDateSerializer(data=request.query_params)
        serializ.is_valid(raise_exception=True)

        start_date  = serializ.validated_data.get('start_date', None)
        end_date    = serializ.validated_data.get('end_date', None)
        date_type = serializ.validated_data.get('date_type', None)
        
        if start_date == None:
            
            result_page=self.paginate_queryset(queryset)
            serializer=serializers.PatternAllListSerializer(result_page,many=True,context={'request': request})
        else:
            
            if date_type == "created_at":
                queryset=queryset.filter(Q(created_at__date__range=(start_date,end_date))
                    ).distinct()
            else:
                queryset=queryset.filter(
                        Q(updated_at__date__range=(start_date,end_date))
                    ).distinct()
 
class projectApiListView(GenericViewSet):
    @extend_schema(
        tags=['Api Services'],
        request   = ListdetailsbyDateSerializer,
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
        serializ=ListdetailsbyDateSerializer(data=request.query_params)
        serializ.is_valid(raise_exception=True)

        start_date  = serializ.validated_data.get('start_date', None)
        end_date    = serializ.validated_data.get('end_date', None)
        date_type = serializ.validated_data.get('date_type', None)

        print('\n\n\ndates',start_date,end_date,date_type)
        projectlist=utils.projectdetails(request.user.id,start_date,end_date,date_type)
        print('\n\nproject list',projectlist)

        return Response(data={'results':projectlist})

class projectApiListByIdView(GenericViewSet):

    serializer_class= projectIdSerializer
    @extend_schema(
        tags=['Api Services'],
        request=projectIdSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyid(self,request):
        sv=projectIdSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        project_id=sv.validated_data.get('project_id')
        projectdata=utils.projectdetailsbyid(project_id)
        return Response(data={'result':projectdata})



class ApiUrlDetails(GenericViewSet):

    @extend_schema(
        tags=['Api Services'],
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewdata(self,request):
        apilist=utils.apiserviceViewall()
        return Response(data={'apicalls':apilist})

class ApiUrlDetailsByUser(GenericViewSet):

    serializer_class= usernameSerializer
    @extend_schema(
        tags=['Api Services'],
        request=usernameSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyuser(self,request):
        sv=usernameSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        userid=sv.validated_data.get('user_id')
        apilist=utils.apiserviceViewallbyUser(userid)
        result={'result':apilist}
        return Response(data={'apicalls':result})


class ApiUrlDetailsByUrl(GenericViewSet):

    serializer_class= urlidSerializer
    @extend_schema(
        tags=['Api Services'],
        request=urlidSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrl(self,request):
        sv=urlidSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        urlid=sv.validated_data.get('url_id')
        apilist=utils.apiserviceViewabyUrl(urlid)
        count=len(apilist)
        result={'result':apilist}
        return Response(data={'apicalls':result})

class AllDetailsByDate(GenericViewSet):

    serializer_class= detailsbyDateSerializer
    @extend_schema(
        tags=['Api Services'],
        request=detailsbyDateSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewdatabyUrlDate(self,request):
        sv=detailsbyDateSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        startdate=sv.validated_data.get('startdate')
        endingdate=sv.validated_data.get('endingdate')
        projectid=sv.validated_data.get('project_id')

        datefilterdata=utils.AllUrlsbydate(startdate,endingdate,projectid)
        srdata=apiListByProjectId(datefilterdata,many=True, context={'start_date': startdate,'end_date':endingdate}).data
        return Response(data={'apicalls':srdata})
        # return Response(data={'apicalls':datefilterdata})

class ApiUrlDetailsByDate(GenericViewSet):

    serializer_class= urlidSerializer
    @extend_schema(
        tags=['Api Services'],
        request=apiDateSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewdatabyUrlDate(self,request):
        sv=apiDateSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        urlid=sv.validated_data.get('url_id')
        startdate=sv.validated_data.get('startdate')
        endingdate=sv.validated_data.get('endingdate')

        datefilterdata=utils.apidetailsbydate(urlid,startdate,endingdate)

        return Response(data={'apicalls':datefilterdata})

class DetailsByHour(GenericViewSet):

    serializer_class= hourSerializer
    @extend_schema(
        tags=['Api Services'],
        request=hourSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=hourSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        hours=sv.validated_data.get('hour')

        datefilterdata=utils.detailsbyHour(hours)

        return Response(data={'apicalls':datefilterdata})


class ApiUrlDetailsByHour(GenericViewSet):

    serializer_class= urlByHourSerializer
    @extend_schema(
        tags=['Api Services'],
        request=urlByHourSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=urlByHourSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        url_id=sv.validated_data.get('url_id')
        hours=sv.validated_data.get('hour')

        datefilterdata=utils.ApibyHour(url_id,hours)

        return Response(data={'apicalls':datefilterdata})
        
class DetailsByDays(GenericViewSet):

    serializer_class= DaySerializer
    @extend_schema(
        tags=['Api Services'],
        request=DaySerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=DaySerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        days=sv.validated_data.get('days')

        datefilterdata=utils.detailsbyDate(days)

        return Response(data={'apicalls':datefilterdata})


class ApiUrlDetailsByDays(GenericViewSet):

    serializer_class= urlByDaySerializer
    @extend_schema(
        tags=['Api Services'],
        request=urlByDaySerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=urlByDaySerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        url_id=sv.validated_data.get('url_id')
        days=sv.validated_data.get('days')

        datefilterdata=utils.ApibyDate(url_id,days)

        return Response(data={'apicalls':datefilterdata})

class HourChartView(GenericViewSet):

    serializer_class= hourSerializer
    @extend_schema(
        tags=['Api Services'],
        request=hourSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=hourSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        proj_id=sv.validated_data.get('project_id')
        hours=sv.validated_data.get('hour')

        datefilterdata=utils.chartbyhour(hours,proj_id)

        return Response(data={'result':datefilterdata})
        
class DayChartView(GenericViewSet):

    serializer_class= DaySerializer
    @extend_schema(
        tags=['Api Services'],
        request=DaySerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlHour(self,request):
        sv=DaySerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        proj_id=sv.validated_data.get('project_id')
        days=sv.validated_data.get('days')

        datefilterdata=utils.chartByDay(days,proj_id)

        return Response(data={'result':datefilterdata})

class DateChartView(GenericViewSet):

    serializer_class= detailsbyDateSerializer
    @extend_schema(
        tags=['Api Services'],
        request=detailsbyDateSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )


    def viewdatabyUrlDate(self,request):
        sv=detailsbyDateSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        proj_id=sv.validated_data.get('project_id')
        startdate=sv.validated_data.get('startdate')
        endingdate=sv.validated_data.get('endingdate')

        datefilterdata=utils.chartByTwoDates(startdate,endingdate,proj_id)

        return Response(data={'apicalls':datefilterdata})


class ApiNotificationView(viewsets.ViewSet):
    @extend_schema(
        tags=['Api Services'],
        responses={
            200:dict,
            400:dict,
        }
    )

    def viewdata(self,request):
        apilist=utils.viewApiNotification(request)
        return Response(data={'data':apilist})

    @extend_schema(
        tags=['Api Services'],
    request   = ApiNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = ApiNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = ApiNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

class ApiNotificationStatusChange(viewsets.ViewSet):
    @extend_schema(
        tags=['Api Services'],
    request   = ApiNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = ApiNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = ApiNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


class ApiSave(APIView):
    """
    APIs to get sin
    """
    permission_classes  = [AllowAny]
    @extend_schema(
    tags=['Api Services'],
    responses = {201: dict,
            404: dict,
            409: dict}) 
    # def saveApiListDb(apiname,orgname,projectname,request,latency,error_code,error_msg,ip_address,system_name):
    def post(self,request):
        # import pdb;pdb.set_trace()
        data = request.POST
        success={200:'OK',201:'CREATED',202:'ACCEPTED',203:'NON_AUTHORITATIVE_INFORMATION',204:'NO_CONTENT',205:'RESET_CONTENT',206:'PARTIAL_CONTENT',207:'MULTI_STATUS',208:'ALREADY_REPORTED',226:'IM_USED'}
        redirection={300:'MULTIPLE_CHOICES',301:'MOVED_PERMANENTLY',302:'FOUND',303:'SEE_OTHER',304:'NOT_MODIFIED',305:'USE_PROXY',306:'RESERVED',307:'TEMPORARY_REDIRECT',308:'PERMANENT_REDIRECT'}
        clienterror={400:'Bad Request',401:'Unauthorized',402:'Payment Required',403:'Forbidden',404:'Not Found',405:'Method Not Allowed',406:'Not Acceptable',407:'Proxy Authentication Required',408:'Request Timeout',409:'Conflict',410:'Gone',411:'Length Required',412:'Precondition Failed',413:'Request Too Large',414:'Request-URI Too Long',415:'Unsupported Media Type',416:'Range Not Satisfiable',417:'Expectation Failed'}
        servererror={500:'Internal Server Error',501:'Not Implemented',502:'Bad Gateway',503:'Service Unavailable',504:'Gateway Timeout',505:'HTTP Version Not Supported',511:'Network Authentication Required'}
        print('\n\n\n inside save1')
        if int(data['error_code']) in success.keys():
            error_message=success[int(data['error_code'])]
            error_status=1

        elif int(data['error_code']) in redirection.keys():
            error_message=redirection[int(data['error_code'])]
            error_status=0

        elif int(data['error_code']) in clienterror.keys():
            error_message=data['error_msg']
            error_status=0

        elif int(data['error_code']) in servererror.keys():
            error_message=data['error_msg']
            error_status=0
        user=data['user']
        # print('\n\n\n',data['user'],data['user'])
        # print('\n\n\n inside save',data['apiname'],data['orgname'],projectname,user,data['latency'],data['error_code'],error_message,error_status)
        if user:
            user_found=User.objects.get(id=user)
        else:
            user_found= None
        
        if ApiDetails.objects.filter(api_name=data['apiname']).exists():
            ApiList=ApiDetails.objects.get(api_name=data['apiname'])

            apidata=ApiCallDetails()
            apidata.user=user_found
            apidata.apiname=ApiList
            apidata.latency=data['latency']
            apidata.error_status=error_status
            apidata.status_message=error_message
            apidata.ip_address=data['ip_address']
            apidata.system_name=data['system_name']
            apidata.save()
        else:
            organization_name=Organization.objects.get(name=data['orgname'])
            print('\n\norganization name: ',organization_name)
            projectname=Projects.objects.get(name=data['projectname'])
            print('\n\nprojectname name: ',projectname)
            ApiList=ApiDetails()
            ApiList.organization=organization_name
            ApiList.project=projectname
            ApiList.api_name=data['apiname']
            ApiList.save()

            api_notification_save=ApiNotificationSave(ApiList,projectname,organization_name)

            apidata=ApiCallDetails()
            apidata.user=user_found
            apidata.apiname=ApiList
            apidata.latency=data['latency']
            apidata.error_status=error_status
            apidata.status_message=error_message
            apidata.ip_address=data['ip_address']
            apidata.system_name=data['system_name']
            apidata.save()

            # return apidata
        return Response(data={"detail": "Success"}, status=status.HTTP_200_OK)
def ApiNotificationSave(api,project,organization):
    superusers = User.objects.filter(is_superuser=True)
    superadmin=User.objects.filter(is_superuser=True)[:1].get()
    try:
        usr=[]
        orgadmin=Role.objects.filter(organization=organization)
        
        for i in orgadmin:            
            if(i in usr):
                pass
            else:
                usr.append(i.user)
                notification=ApiNotification()
                notification.apiname=api
                notification.action_user=superadmin
                notification.action_type="create"
                notification.org_user=i.user
                notification.product=project
                notification.save()

        for i in superusers:
            if(i in usr):
                pass
            else:
                notification=ApiNotification()
                notification.apiname=api
                notification.action_user=superadmin
                notification.action_type="create"
                notification.org_user=i.user
                notification.product=project
                notification.save()
    except:
        for i in superusers:
            notification.apiname=api
            notification.action_user=superadmin
            notification.action_type="create"
            notification.org_user=i
            notification.product=project
            notification.save()
