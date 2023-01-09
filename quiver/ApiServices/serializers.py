
from datetime import datetime, timedelta
from rest_framework import fields,serializers
from traitlets import default
from . models import *
from projects.models import *
from django.db.models import Max,Min
#serializer to fetch credentials for wokzone api
class projectIdSerializer(serializers.Serializer):
    project_id=serializers.CharField(max_length=100)
    
class usernameSerializer(serializers.Serializer):
    user_id=serializers.CharField(max_length=100)

class urlidSerializer(serializers.Serializer):
    url_id=serializers.CharField(max_length=100)

class detailsbyDateSerializer(serializers.Serializer):
    project_id=serializers.CharField(max_length=100)
    startdate= serializers.DateTimeField()
    endingdate=serializers.DateTimeField()

class apiDateSerializer(serializers.Serializer):
    startdate= serializers.DateTimeField()
    endingdate=serializers.DateTimeField()
    url_id=serializers.CharField(max_length=100)

class hourSerializer(serializers.Serializer):
    project_id=serializers.CharField(max_length=100)
    hour=serializers.IntegerField()

class urlByHourSerializer(serializers.Serializer):
    url_id=serializers.CharField(max_length=100)
    hour=serializers.IntegerField()

class DaySerializer(serializers.Serializer):
    project_id=serializers.CharField(max_length=100)
    days=serializers.IntegerField()

class urlByDaySerializer(serializers.Serializer):
    url_id=serializers.CharField(max_length=100)
    days=serializers.IntegerField()

class ApiNotifcationStatusSerializer(serializers.Serializer):

    notification_list = serializers.ListField(
        child=serializers.UUIDField(required=False)
    )

class ListdetailsbyDateSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    date_type = serializers.CharField(required=False)


class UrldetailsbyParmeterSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    hour = serializers.IntegerField(required=False)
    days=serializers.IntegerField(required=False)


class ApiDetailsSerializer(serializers.ModelSerializer):
    organization_name=serializers.CharField(source="organization.name")
    project_name=serializers.CharField(source="project.name")
    class Meta:
        model=ApiDetails
        fields=["id","organization","project","api_name","organization_name","project_name"]

class ApiCallDetailsSerializer(serializers.ModelSerializer):
    user_id=serializers.CharField(source="user.id")
    user_name=serializers.CharField(source="user.username")
    api_name=serializers.CharField(source="apiname.name")

    class Meta:
        model=ApiCallDetails
        fields=["user_id","user_name","api_name","api_id","latency","error_status","status_message","processed_at","ip_address","system_name"]

class apiListByProjectId(serializers.ModelSerializer):
    api_id=serializers.CharField(source="apiname.id")
    name=serializers.CharField(source="apiname.api_name")
    url_count=serializers.SerializerMethodField()
    latency_median=serializers.SerializerMethodField()
    latency=serializers.SerializerMethodField()
    error_count=serializers.SerializerMethodField()
    error_percentage=serializers.SerializerMethodField()

    class Meta:
        model=ApiCallDetails
        fields=["api_id","name","url_count","latency_median","latency",'error_count','error_percentage']

    def get_url_count(self,obj):
        start_date=self.context.get("start_date")
        end_date=self.context.get("end_date")
        count_api=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id,processed_at__range=[start_date,end_date]).count()
        
        return count_api
    
    def get_latency_median(self,obj):
        max_lat=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id).aggregate(Max('latency'))
        min_lat=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id).aggregate(Min('latency'))
        lat_median=((float(max_lat['latency__max'])+float(min_lat['latency__min']))/2)
        
        return lat_median
    
    def get_latency(self,obj):
        max_lat=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id).aggregate(Max('latency'))
        min_lat=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id).aggregate(Min('latency'))
        lat_median=((float(max_lat['latency__max'])+float(min_lat['latency__min']))/2)

        return lat_median
    
    def get_error_count(self,obj):
        start_date=self.context.get("start_date")
        end_date=self.context.get("end_date")
        error_count=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id,processed_at__range=[start_date,end_date],error_status=True).count()
        return error_count

    def get_error_percentage(self,obj):
        start_date=self.context.get("start_date")
        end_date=self.context.get("end_date")
        count_api=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id,processed_at__range=[start_date,end_date]).count()
        error_count_found=ApiCallDetails.objects.filter(apiname__id=obj.apiname.id,processed_at__range=[start_date,end_date],error_status=True).count()
        error_percent=((float(error_count_found))/float(count_api))*100
        return error_percent

