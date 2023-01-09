from itertools import count
from unicodedata import name

from django.conf import settings
from . models import *
from projects.models import Projects
from users.models import *
from datetime import datetime
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F
import statistics
from projects.models import *
from django.core.exceptions import ValidationError
from .serializers import *
from django.db import connection
import psycopg2
from psycopg2.extras import RealDictCursor
from django.db.models import Max,Min

#establishing the connection
conn = psycopg2.connect(
   database=settings.DATABASES['default']['NAME'], user=settings.DATABASES['default']['USER'], password=settings.DATABASES['default']['PASSWORD'], host=settings.DATABASES['default']['HOST'], port= settings.DATABASES['default']['PORT']
)

#Setting auto commit false
conn.autocommit = True

#Creating a cursor object using the cursor() method
# cursor = conn.cursor(cursor_factory=RealDictCursor)

def projectdetails(userid,startingdate,endingdate,date_type):

    user_found=User.objects.get(id=userid)
    user_role=Role.objects.get(user=user_found)
    if(user_role.role=='superadmin'):
        # import pdb;pdb.set_trace()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # JSONB_AGG(jsonb_build_object('userid',user_id,'first_name',usr.first_name))
        # (SELECT role.organization_id as orgid,usr.id as userid,usr.first_name as first_name,usr.last_name as last_name,usr.username as username FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id)
        if(startingdate==None and endingdate==None):
            try:
                cursor.execute('''SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid''',(startingdate,endingdate))
            except psycopg2.ProgrammingError as exc:
                conn.rollback()
            except psycopg2.InterfaceError as exc:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            if date_type=="created_at":
                try:
                    cursor.execute('''SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id WHERE pro.created_at::date BETWEEN %s::date AND %s::date) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid''',(startingdate,endingdate))
                except psycopg2.ProgrammingError as exc:
                    conn.rollback()
                except psycopg2.InterfaceError as exc:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                try:
                    cursor.execute('''SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id WHERE pro.updated_at::date BETWEEN %s::date AND %s::date) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid''',(startingdate,endingdate))
                except psycopg2.ProgrammingError as exc:
                    conn.rollback()
                except psycopg2.InterfaceError as exc:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
        # cursor.execute('''SELECT usr.id,usr.first_name,usr.last_name,usr.username as collaborators FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id ;''')
        row = cursor.fetchall()
        cursor.close()
        for data in row:
            if not data['collaborators']:
                data['collaborators'] = []
            data['created_at'] = data['created_at'].strftime("%d-%m-%Y %I:%M:%S %p")
            data['updated_at'] = data['updated_at'].strftime("%d-%m-%Y %I:%M:%S %p")
            data['organizationId'] = data['organizationid']
        return row
        # if(startingdate==None and endingdate==None):
        #     projectdatas=ApiDetails.objects.all()
        # else:
        #     if date_type=="created_at":
        #         projectdatas=ApiDetails.objects.filter(project__created_at__range=[startingdate,endingdate])
        #         if (len(projectdatas)==0):
        #             projectdatas=ApiDetails.objects.filter(project__created_at__date=startingdate)
        #     else:
        #         projectdatas=ApiDetails.objects.filter(project__updated_at__range=[startingdate,endingdate])
        #         if (len(projectdatas)==0):
        #             projectdatas=ApiDetails.objects.filter(project__updated_at__date=startingdate)    
        # project_ids=[]
        # projs=[]
        # for i in projectdatas:
        #     cols=[]
        #     collabrole=Role.objects.filter(organization=i.organization)
        #     for c in collabrole:
        #         if(c.role=='admin'):
        #             cols.append({'userid': c.user.id, 'first_name':c.user.first_name , 'last_name':c.user.last_name,'username':c.user.username})
        #     if i.project.id in project_ids:
        #         pass
        #     else:
        #         project_ids.append(i.project.id)
        #         try:
        #             projs.append({'id':i.project.id,'title':i.project.name,'organizationId':i.organization.id,'created_by':i.project.created_by.username,'created_at':i.project.created_at.strftime("%d-%m-%Y %I:%M:%S %p"),'updated_at':i.project.updated_at.strftime("%d-%m-%Y %I:%M:%S %p"),'collaborators':cols})
        #         except AttributeError:
        #             projs.append({'id':i.project.id,'title':i.project.name,'organizationId':'','created_by':i.project.created_by.username,'created_at':i.project.created_at.strftime("%d-%m-%Y %I:%M:%S %p"),'updated_at':i.project.updated_at.strftime("%d-%m-%Y %I:%M:%S %p"),'collaborators':cols})
        # return projs
    elif(user_role.role=='admin' or user_role.role=='user'):
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if(startingdate==None and endingdate==None):
            cursor.execute("""SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid WHERE project.apiorgid='"""+str(user_role.organization.id)+"""'""")
        else:
            if date_type=="created_at":
                cursor.execute("""SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id WHERE pro.created_at::date BETWEEN %s::date AND %s::date) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid WHERE apiorgid='"""+str(user_role.organization.id)+"""'""",(startingdate,endingdate))
            else:
                cursor.execute("""SELECT project.proid as id,project.title as title,collaborators,users.orgid as organizationId,project.created_at as created_at,project.updated_at as updated_at FROM (SELECT DISTINCT(pro.id) as proid,pro.name as title,api.organization_id as apiorgid,pro.created_at as created_at,pro.updated_at as updated_at FROM public."ApiServices_apidetails" as api JOIN public."projects_projects" as pro ON api.project_id = pro.id WHERE pro.updated_at::date BETWEEN %s::date AND %s::date) as project LEFT JOIN (SELECT JSONB_AGG(jsonb_build_object('userid',usr.id,'first_name',usr.first_name,'last_name',usr.last_name,'username',usr.username)) as collaborators,role.organization_id as orgid FROM public."users_role" as role JOIN public."users_user" as usr ON usr.id=role.user_id GROUP BY role.organization_id) as users ON users.orgid = project.apiorgid WHERE apiorgid='"""+str(user_role.organization.id)+"""'""",(startingdate,endingdate))
        row = cursor.fetchall()
        cursor.close()
        for data in row:
            if not data['collaborators']:
                data['collaborators'] = []
            data['created_at'] = data['created_at'].strftime("%d-%m-%Y %I:%M:%S %p")
            data['updated_at'] = data['updated_at'].strftime("%d-%m-%Y %I:%M:%S %p")
            data['organizationId'] = data['organizationid']
        return row
        # if(startingdate=='' and endingdate==''):
        #     projectdatas=ApiDetails.objects.filter(organization=user_role.organization)
        # else:
        #     if date_type=="created_at":
        #         projectdatas=ApiDetails.objects.filter(organization=user_role.organization,project__created_at__range=[startingdate,endingdate])
        #         if (len(projectdatas)==0):
        #             projectdatas=ApiDetails.objects.filter(organization=user_role.organization,project__created_at__date=startingdate)
        #     else:
        #         projectdatas=ApiDetails.objects.filter(organization=user_role.organization,project__updated_at__range=[startingdate,endingdate])
        #         if (len(projectdatas)==0):
        #             projectdatas=ApiDetails.objects.filter(organization=user_role.organization,project__updated_at__date=startingdate)
        # project_ids=[]
        # projs=[]
        # for i in projectdatas:
        #     cols=[]
        #     collabrole=Role.objects.filter(organization=i.organization)
        #     for c in collabrole:
        #         if(c.role=='admin'):
        #             cols.append({'userid': c.user.id, 'first_name':c.user.first_name , 'last_name':c.user.last_name})
        #     if i.project.id in project_ids:
        #         pass
        #     else:
        #         project_ids.append(i.project.id)
        #         try:
        #             projs.append({'id':i.project.id,'title':i.project.name,'organizationId':i.organization.id,'created_by':i.project.created_by.username,'created_at':i.project.created_at,'updated_at':i.project.updated_at,'collaborators':cols})
        #         except AttributeError:
        #             projs.append({'id':i.project.id,'title':i.project.name,'organizationId':'','created_by':i.project.created_by.username,'created_at':i.project.created_at,'updated_at':i.project.updated_at,'collaborators':cols})
        # return projs


def projectdetailsbyid(project_id):
    try:
        project_found=Projects.objects.get(id=project_id)
        project_details={'project_id':project_found.id,'project_name':project_found.name,'created_by':project_found.created_by.username,'status':project_found.status,'created_at':project_found.created_at,'updated_at':project_found.updated_at}
        return project_details
    except ValidationError:
        return 'no project found in this id'

def urldetails():
    urldatas=ApiDetails.objects.all()
    return urldatas
    # apis=[]
    # for i in urldatas:
    #     apis.append({'api_id':i.id,'project_name':i.project.name,'api_name':i.api_name})
    # return apis

def apiserviceViewall():

    apilist=ApiCallDetails.objects.all()
    details=[]
    url_id=[]
    count=0

    for i in apilist:         
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
           
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)

    return details


def apiserviceViewallbyUser(user):
    user_found=User.objects.get(id=user)
    apilist=ApiCallDetails.objects.filter(user=user_found)
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)

    return details

def apiserviceViewabyUrl(url_id):
    api_id=ApiDetails.objects.get(id=url_id)
    apilist=ApiCallDetails.objects.filter(apiname=api_id)
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)
    return details

def AllUrlsbydate(startdate,enddate,projectid):
    starting_date=startdate
    ending_date=enddate
    day=ending_date.date()-starting_date.date()
    day=day.days
    
    detailsbyproject=ApiCallDetails.objects.filter(apiname__project__id=projectid,processed_at__range=[starting_date,ending_date]).distinct("apiname__id")

    return detailsbyproject
    
    # cursor = conn.cursor(cursor_factory=RealDictCursor)
    # cursor.execute('''SELECT api.id as api_id,api.api_name as name,count(api.api_name) as url_count,((min(dt.latency)+max(dt.latency))/2) as latency_median,((min(dt.latency)+max(dt.latency))/2) as latency, count(CASE WHEN NOT dt.error_status THEN 1 END) as error_count,count(CASE WHEN NOT dt.error_status THEN 1 END)/count(api.api_name)::float*100 as error_percentage FROM public."ApiServices_apicalldetails" as dt JOIN public."ApiServices_apidetails" as api ON dt.apiname_id = api.id JOIN public."projects_projects" as pro ON pro.id = api.project_id WHERE pro.id = %s AND dt.processed_at BETWEEN %s AND %s GROUP BY api.api_name,api.id''',(projectid,startdate,enddate))
    # row = cursor.fetchall()
    # cursor.close()
    # count_api=ApiCallDetails.objects.filter(apiname__id=74)
    # for i in count_api:
    #     print(i.error_status)
    # return row

def apidetailsbydate(url_id,startdate,enddate):
    starting_date=startdate
    ending_date=enddate
    day=ending_date.date()-starting_date.date()
    day=day.days
    if(day<=0): 
        api_id=ApiDetails.objects.get(id=url_id)
        apilist=ApiCallDetails.objects.filter(apiname=api_id,processed_at__date=starting_date.date())
        if len(apilist)==0:
            apilist=ApiCallDetails.objects.filter(apiname=api_id,processed_at__date=ending_date.date())

        details=[]
        url_id=[]
        for i in apilist:            
            if(i.apiname.api_name in url_id):    
                for d in range(len(details)):
                    if(details[d]['name']==i.apiname.api_name):
                        url_count=int(details[d]['url_count'])+1
                        error_count=int(details[d]['error_count'])
                        details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                        details[d]['url_count']=url_count
                        if(i.error_status==False):
                            error_found=error_count+1
                            error_percentage=(error_found/url_count)*100
                            details[d]['error_count']=error_found
                            details[d]['error_percentage']=error_percentage
                        else:
                            error_percentage=(error_count/url_count)*100
                            details[d]['error_percentage']=error_percentage             
            else:
                url_id.append(i.apiname.api_name)
                if(i.error_status==False):
                    error=1
                    error_percentage=100
                else:
                    error=0
                    error_percentage=0
                details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
        apiid=ApiDetails.objects.all()
        for name in apiid:
            latdata=[]
            apilatency=ApiCallDetails.objects.filter(apiname=name)
            for lat in apilatency:
                latdata.append(lat.latency)
                for d in range(len(details)):

                    if(details[d]['name']==name.api_name):
                        details[d]['latency_median']=statistics.median(latdata)

        return details
    else:
        api_id=ApiDetails.objects.get(id=url_id)
        apilist=ApiCallDetails.objects.filter(apiname=api_id,processed_at__range=[starting_date,ending_date])
        details=[]
        url_id=[]
        for i in apilist:            
            if(i.apiname.api_name in url_id):    
                for d in range(len(details)):
                    if(details[d]['name']==i.apiname.api_name):
                        url_count=int(details[d]['url_count'])+1
                        error_count=int(details[d]['error_count'])
                        details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                        details[d]['url_count']=url_count
                        if(i.error_status==False):
                            error_found=error_count+1
                            error_percentage=(error_found/url_count)*100
                            details[d]['error_count']=error_found
                            details[d]['error_percentage']=error_percentage
                        else:
                            error_percentage=(error_count/url_count)*100
                            details[d]['error_percentage']=error_percentage             
            else:
                url_id.append(i.apiname.api_name)
                if(i.error_status==False):
                    error=1
                    error_percentage=100
                else:
                    error=0
                    error_percentage=0
                details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
        apiid=ApiDetails.objects.all()
        for name in apiid:
            latdata=[]
            apilatency=ApiCallDetails.objects.filter(apiname=name)
            for lat in apilatency:
                latdata.append(lat.latency)
                for d in range(len(details)):

                    if(details[d]['name']==name.api_name):
                        details[d]['latency_median']=statistics.median(latdata)

        return details

def detailsbyHour(hour):
    enddate=timezone.now()
    ending_time=enddate
    starting_time=ending_time-timedelta(hours=hour)
    
    apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time])
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)

    return details


def ApibyHour(url_id,hour):
    enddate=timezone.now()
    ending_time=enddate
    starting_time=ending_time-timedelta(hours=hour)
    
    api_id=ApiDetails.objects.get(id=url_id)
    apilist=ApiCallDetails.objects.filter(apiname=api_id,processed_at__range=[starting_time,ending_time])
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)

    return details


def detailsbyDate(days):
    enddate=timezone.now()
    ending_time=enddate
    starting_time=ending_time-timedelta(days=days)
    
    apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time])
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)
    return details

def ApibyDate(url_id,days):
    enddate=timezone.now()
    ending_time=enddate
    starting_time=ending_time-timedelta(days=days)
    
    api_id=ApiDetails.objects.get(id=url_id)
    apilist=ApiCallDetails.objects.filter(apiname=api_id,processed_at__range=[starting_time,ending_time])
    details=[]
    url_id=[]
    count=0
    for i in apilist:            
        if(i.apiname.api_name in url_id):    
            for d in range(len(details)):
                if(details[d]['name']==i.apiname.api_name):
                    count+=1
                    url_count=int(details[d]['url_count'])+1
                    error_count=int(details[d]['error_count'])
                    details[d]['latency']=float(details[d]['latency'])+float(i.latency)
                    details[d]['url_count']=url_count
                    if(i.error_status==False):
                        error_found=error_count+1
                        error_percentage=(error_found/url_count)*100
                        details[d]['error_count']=error_found
                        details[d]['error_percentage']=error_percentage
                    else:
                        error_percentage=(error_count/url_count)*100
                        details[d]['error_percentage']=error_percentage             
        else:
            url_id.append(i.apiname.api_name)
            count+=1
            if(i.error_status==False):
                error=1
                error_percentage=100
            else:
                error=0
                error_percentage=0
            details.append({'name':i.apiname.api_name,'latency':i.latency,'latency_median':0,'url_count':1,'error_count':error,'error_percentage':error_percentage})
    apiid=ApiDetails.objects.all()
    for name in apiid:
        latdata=[]
        apilatency=ApiCallDetails.objects.filter(apiname=name)
        for lat in apilatency:
            latdata.append(lat.latency)
            for d in range(len(details)):

                if(details[d]['name']==name.api_name):
                    details[d]['latency_median']=statistics.median(latdata)

    return details

def ApiNotificationSave(api,project,organization):
    print('\n\n\n inside api notif save')
    superusers = User.objects.filter(is_superuser=True)
    superadmin=User.objects.filter(is_superuser=True)[:1].get()
    try:
        print('\n\n\n inside api notif save try')
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
        print('\n\n\n notification saved to db \n\n\n')
    except:
        print('\n\n\nnotif save inside except')
        for i in superusers:
            notification.apiname=api
            notification.action_user=superadmin
            notification.action_type="create"
            notification.org_user=i
            notification.product=project
            notification.save()

        print('\n\n\n notification saved to db \n\n\n')

def saveApiListDb(apiname,orgname,projectname,request,latency,error_code,error_msg,ip_address,system_name):
    success={200:'OK',201:'CREATED',202:'ACCEPTED',203:'NON_AUTHORITATIVE_INFORMATION',204:'NO_CONTENT',205:'RESET_CONTENT',206:'PARTIAL_CONTENT',207:'MULTI_STATUS',208:'ALREADY_REPORTED',226:'IM_USED'}
    redirection={300:'MULTIPLE_CHOICES',301:'MOVED_PERMANENTLY',302:'FOUND',303:'SEE_OTHER',304:'NOT_MODIFIED',305:'USE_PROXY',306:'RESERVED',307:'TEMPORARY_REDIRECT',308:'PERMANENT_REDIRECT'}
    clienterror={400:'Bad Request',401:'Unauthorized',402:'Payment Required',403:'Forbidden',404:'Not Found',405:'Method Not Allowed',406:'Not Acceptable',407:'Proxy Authentication Required',408:'Request Timeout',409:'Conflict',410:'Gone',411:'Length Required',412:'Precondition Failed',413:'Request Too Large',414:'Request-URI Too Long',415:'Unsupported Media Type',416:'Range Not Satisfiable',417:'Expectation Failed'}
    servererror={500:'Internal Server Error',501:'Not Implemented',502:'Bad Gateway',503:'Service Unavailable',504:'Gateway Timeout',505:'HTTP Version Not Supported',511:'Network Authentication Required'}
    print('\n\n\n inside save1')
    if int(error_code) in success.keys():
        error_message=success[int(error_code)]
        error_status=1

    elif int(error_code) in redirection.keys():
        error_message=redirection[int(error_code)]
        error_status=0

    elif int(error_code) in clienterror.keys():
        error_message=error_msg
        error_status=0

    elif int(error_code) in servererror.keys():
        error_message=error_msg
        error_status=0
    user=request.user.id
    print('\n\n\n',request.user,request.user.id)
    print('\n\n\n inside save',apiname,orgname,projectname,user,latency,error_code,error_message,error_status)
    user_found=User.objects.get(id=user)

    if ApiDetails.objects.filter(api_name=apiname).exists():
        ApiList=ApiDetails.objects.get(api_name=apiname)

        apidata=ApiCallDetails()
        apidata.user=user_found
        apidata.apiname=ApiList
        apidata.latency=latency
        apidata.error_status=error_status
        apidata.status_message=error_message
        apidata.ip_address=ip_address
        apidata.system_name=system_name
        apidata.save()

        return apidata
    else:
        organization_name=Organization.objects.get(name=orgname)
        print('\n\norganization name: ',organization_name)
        projectname=Projects.objects.get(name=projectname)
        print('\n\nprojectname name: ',projectname)
        ApiList=ApiDetails()
        ApiList.organization=organization_name
        ApiList.project=projectname
        ApiList.api_name=apiname
        ApiList.save()

        api_notification_save=ApiNotificationSave(ApiList,projectname,organization_name)

        apidata=ApiCallDetails()
        apidata.user=user_found
        apidata.apiname=ApiList
        apidata.latency=latency
        apidata.error_status=error_status
        apidata.status_message=error_message
        apidata.ip_address=ip_address
        apidata.system_name=system_name
        apidata.save()

        return apidata

def chartbyhour(hr,project_id):
    count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
    error=[{'xName':'0 hour','yValue':0}]
    latency=[{'xName':'0 hour','yValue':0}]
    final=[]
    ending_time=timezone.now()
    if(hr<=5):
        if(hr==1):
            for hour in range(1,61,10):
          
                er=0
                lt=0
                starting_time=ending_time-timedelta(minutes=10)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
                count.append({'xName':str(hour)+' min','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' min','yValue':er})
                latency.append({'xName':str(hour)+' min','yValue': "{:.2f}".format(lt)})

                ending_time=starting_time
        else:
            endhr=hr*60
            cd=int(endhr/6)
            for hour in range(1,endhr,cd):
              
                er=0
                lt=0
                starting_time=ending_time-timedelta(minutes=cd)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
                count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' min','yValue':er})
                latency.append({'xName':str(hour)+' min','yValue': "{:.2f}".format(lt)})

                ending_time=starting_time

    else:
        difference=hr/6

        for hour in range(1,hr+1,int(difference)):
        
            er=0
            lt=0
            starting_time=ending_time-timedelta(hours=int(difference))
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(hour)+' hour','yValue':er})
            latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
    final.append({'traffic':count,'error':error,'latency':latency})
    return final

def chartByDay(day,project_id):

    count=[]
    error=[]
    latency=[]
    final=[]

    ending_time=timezone.now()
    dayhours=24*day
    

    if day==1:
        count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 hour','yValue':0}]
        latency=[{'xName':'0 hour','yValue':0}]
        for hour in range(1,25,4):        
            er=0
            lt=0
            starting_time=ending_time-timedelta(hours=4)
            
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(hour)+' hour','yValue':er})
            latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final
    elif day==4:
        count=[{'xName':'0 day','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 day','yValue':0}]
        latency=[{'xName':'0 day','yValue':0}]
        difference=dayhours/6
        print('\n\n',difference)
        for hour in range(1,day+1):
       
            er=0
            lt=0
            starting_time=ending_time-timedelta(days=1)
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            count.append({'xName':str(hour)+' day','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(hour)+' day','yValue':er})
            latency.append({'xName':str(hour)+' day','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final

    else:
        count=[{'xName':'0 day','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 day','yValue':0}]
        latency=[{'xName':'0 day','yValue':0}]
        difference=dayhours/6
        print('\n\n',difference)
        
        for hour in range(1,dayhours+1,int(difference)):
            er=0
            lt=0
            starting_time=ending_time-timedelta(hours=int(difference))
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            daydate=int(hour/24)
            if daydate==0:
                daydate=1
            count.append({'xName':str(daydate)+' days','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(daydate)+' days','yValue':er})
            latency.append({'xName':str(daydate)+' days','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final


def chartByTwoDates(startdate,enddate,project_id):
    starting_time=startdate
    ending_time=enddate
    day=ending_time.date()-starting_time.date()
    day=day.days
    print('\n\ndays: ',day)
    count=[]
    error=[]
    latency=[]
    final=[]

    dayhours=24*day
    print('\n\nhours: ',dayhours)
    if day<=1:
        ending_time=starting_time
        count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 hour','yValue':0}]
        latency=[{'xName':'0 hour','yValue':0}]

        for hour in range(1,25,6):
  
            er=0
            lt=0
            starting_time=ending_time-timedelta(hours=6)
            apilist=ApiCallDetails.objects.filter(processed_at__date=starting_time,apiname__project__id=project_id)
            count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(hour)+' hour','yValue':er})
            latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final
  
    elif day==4:
        count=[{'xName':'0 day','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 day','yValue':0}]
        latency=[{'xName':'0 day','yValue':0}]
        difference=dayhours/6
        print('\n\n',difference)
        for hour in range(1,day+1):

            er=0
            lt=0
            starting_time=ending_time-timedelta(days=1)
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(hour)+' day','yValue':er})
            latency.append({'xName':str(hour)+' day','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final

    else:
        count=[{'xName':'0 day','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 day','yValue':0}]
        latency=[{'xName':'0 day','yValue':0}]
        difference=dayhours/6
        print('\n\n',difference)
        for hour in range(1,dayhours+1,int(difference)):
          
            er=0
            lt=0
            starting_time=ending_time-timedelta(hours=int(difference))
            apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname__project__id=project_id)
            daydate=int(hour/24)
            if(daydate==0):
                daydate=1
            count.append({'xName':str(daydate)+' days','yValue':len(apilist),'date':starting_time,'end':ending_time})
            for api in apilist:
                lt+=float(api.latency)
                if (api.error_status==False):
                    er+=1
            error.append({'xName':str(daydate)+' days','yValue':er})
            latency.append({'xName':str(daydate)+' days','yValue':"{:.2f}".format(lt)})
            ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final

def viewApiNotification(request):
    user = request.user
    org_id = Role.objects.filter(user=user).first()
    print('\n\n role: ',org_id.role)
    notif=[]

    if org_id.role != "superadmin":

        api_notification = ApiNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        print('\n\n\napinotif1',api_notification)
        for api in api_notification:
            notif.append({
            "id": api.id,
            "api_id": api.apiname.id,
            "api_name":api.apiname.api_name,
            "project_name": api.product.name,
            "action_type": "create",
            "created_by": api.product.created_by.username,
            "created_at": api.created_at,
            "updated_at": api.updated_at,
            "action_status": "unseen",
            "higlight_status": "unseen",
            "user_role":org_id.role,
            },)
    elif org_id.role == "superadmin":
        
        history = ApiNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=user).order_by("-created_at")[:10]
        print('\n\n\napinotif2',history)
        for api in history:
            notif.append({
            "id": api.id,
            "api_id": api.apiname.id,
            "api_name":api.apiname.api_name,
            "project_name": api.product.name,
            "action_type": "create",
            "created_by": api.product.created_by.username,
            "created_at": api.created_at,
            "updated_at": api.updated_at,
            "action_status": "unseen",
            "higlight_status": "unseen",
            "user_role":org_id.role,
            },)
    return notif

def chartbyUrl(url_id,startdate,enddate,hour,days):
    url_data=ApiDetails.objects.get(id=url_id)
    #======================================#
    #   to view whole chart                #
    #======================================#
    if(startdate==None and enddate==None and hour==None and days==None):
        count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 hour','yValue':0}]
        latency=[{'xName':'0 hour','yValue':0}]
        
        apilist=ApiCallDetails.objects.filter(apiname=url_data).order_by("processed_at")
        len_apilist=len(apilist)

        starting_time=apilist[0].processed_at
        ending_time=apilist[len_apilist-1].processed_at

        day=ending_time.date()-starting_time.date()
        day=day.days
        print('\n\ndays: ',day)
        count=[]
        error=[]
        latency=[]
        final=[]

        dayhours=24*day
        print('\n\nhours: ',dayhours)
        if day<=1:
            ending_time=starting_time
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]

            for hour in range(1,25,6):
    
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=6)
                apilist=ApiCallDetails.objects.filter(processed_at__date=starting_time,apiname=url_data)
                count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' hour','yValue':er})
                latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final
    
        elif day==4:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            for hour in range(1,day+1):

                er=0
                lt=0
                starting_time=ending_time-timedelta(days=1)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(hour)+' day','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' day','yValue':er})
                latency.append({'xName':str(hour)+' day','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final

        else:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            for hour in range(1,dayhours+1,int(difference)):
            
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=int(difference))
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(int(hour/24))+' days','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(int(hour/24))+' days','yValue':er})
                latency.append({'xName':str(int(hour/24))+' days','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final


    #======================================#
    #   to view chart  by day filter       #
    #======================================#
    elif(startdate==None and enddate==None and hour==None):
        day=days
        count=[]
        error=[]
        latency=[]
        final=[]

        ending_time=timezone.now()
        dayhours=24*day
        

        if day==1:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            for hour in range(1,25,4):        
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=4)
                
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' hour','yValue':er})
                latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final
        elif day==4:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            for hour in range(1,day+1):
        
                er=0
                lt=0
                starting_time=ending_time-timedelta(days=1)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(hour)+' day','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' day','yValue':er})
                latency.append({'xName':str(hour)+' day','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final

        else:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            
            for hour in range(1,dayhours+1,int(difference)):
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=int(difference))
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(int(hour/24))+' days','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(int(hour/24))+' days','yValue':er})
                latency.append({'xName':str(int(hour/24))+' days','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final

    #======================================#
    #   to view chart  by date filter      #
    #======================================#
    elif(startdate==None and enddate==None and days==None):
        hr=hour

        count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
        error=[{'xName':'0 hour','yValue':0}]
        latency=[{'xName':'0 hour','yValue':0}]
        final=[]
        ending_time=timezone.now()
        if(hr<=5):
            if(hr==1):
                for hour in range(1,61,10):
            
                    er=0
                    lt=0
                    starting_time=ending_time-timedelta(minutes=10)
                    apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                    count.append({'xName':str(hour)+' min','yValue':len(apilist),'date':starting_time,'end':ending_time})
                    for api in apilist:
                        lt+=float(api.latency)
                        if (api.error_status==False):
                            er+=1
                    error.append({'xName':str(hour)+' min','yValue':er})
                    latency.append({'xName':str(hour)+' min','yValue': "{:.2f}".format(lt)})

                    ending_time=starting_time
            else:
                endhr=hr*60
                cd=int(endhr/6)
                for hour in range(1,endhr,cd):
                
                    er=0
                    lt=0
                    starting_time=ending_time-timedelta(minutes=cd)
                    apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                    count.append({'xName':str(hour)+' min','yValue':len(apilist),'date':starting_time,'end':ending_time})
                    for api in apilist:
                        lt+=float(api.latency)
                        if (api.error_status==False):
                            er+=1
                    error.append({'xName':str(hour)+' min','yValue':er})
                    latency.append({'xName':str(hour)+' min','yValue': "{:.2f}".format(lt)})

                    ending_time=starting_time

        else:
            difference=hr/6

            for hour in range(1,hr+1,int(difference)):
            
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=int(difference))
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' hour','yValue':er})
                latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
        final.append({'traffic':count,'error':error,'latency':latency})
        return final

    #======================================#
    #   to view chart  by dates filter     #
    #======================================#

    elif(hour==None and days==None):
        starting_time=startdate
        ending_time=enddate
        day=ending_time.date()-starting_time.date()
        day=day.days
        print('\n\ndays: ',day)
        count=[]
        error=[]
        latency=[]
        final=[]

        dayhours=24*day
        print('\n\nhours: ',dayhours)
        if day<=1:
            ending_time=starting_time
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]

            for hour in range(1,25,6):
    
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=6)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                print('\n\n\n1 day list: ',apilist)
                count.append({'xName':str(hour)+' hour','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' hour','yValue':er})
                latency.append({'xName':str(hour)+' hour','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final
    
        elif day==4:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            for hour in range(1,day+1):

                er=0
                lt=0
                starting_time=ending_time-timedelta(days=1)
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(hour)+' day','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(hour)+' day','yValue':er})
                latency.append({'xName':str(hour)+' day','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final

        else:
            count=[{'xName':'0 hour','yValue':0,'date':'','end':''}]
            error=[{'xName':'0 hour','yValue':0}]
            latency=[{'xName':'0 hour','yValue':0}]
            difference=dayhours/6
            print('\n\n',difference)
            for hour in range(1,dayhours+1,int(difference)):
            
                er=0
                lt=0
                starting_time=ending_time-timedelta(hours=int(difference))
                apilist=ApiCallDetails.objects.filter(processed_at__range=[starting_time,ending_time],apiname=url_data)
                count.append({'xName':str(int(hour/24))+' days','yValue':len(apilist),'date':starting_time,'end':ending_time})
                for api in apilist:
                    lt+=float(api.latency)
                    if (api.error_status==False):
                        er+=1
                error.append({'xName':str(int(hour/24))+' days','yValue':er})
                latency.append({'xName':str(int(hour/24))+' days','yValue':"{:.2f}".format(lt)})
                ending_time=starting_time
            final.append({'traffic':count,'error':error,'latency':latency})
            return final
            