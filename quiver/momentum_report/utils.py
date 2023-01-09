from projects.models import *
from users.models import *
from . models import *
from django.db.models import Q
import math
import extcolors
from datetime import datetime, timedelta
import spintax
import tempfile
from django.shortcuts import render
from datetime import datetime
import os
from django.shortcuts import get_object_or_404
import base64
from . serializers import *

#to find user
def UserFind():
    user_found=User.objects.get(username='alexjohnson@logicplum.com')
    return user_found

def ListProjectsByOrganization(userid):  
    user_found=User.objects.get(id=userid)

    user_role=Role.objects.get(user=user_found)
    print('user role: ',user_role.role)
    if(user_role.role=='admin' or user_role.role=='user'):
        projectsListDb=ProjectFromWorkzone.objects.get(organization_data=user_role.organization)
        return projectsListDb
    elif(user_role.role=='superadmin'):
        projectsListDb=ProjectFromWorkzone.objects.all()
        return projectsListDb


def projectDbFinder(project_id):
    projectDb=ProjectFromWorkzone.objects.get(id=project_id)
    return projectDb

def ReportDbFinderByProjectId(project_id):
    report_id=Report.objects.filter(product_id=project_id).order_by('created_at').latest('created_at')
    return report_id.id

def FindReportWeekDate(report_id):
    reportDb=Report.objects.get(id=report_id)
    report_date_found=reportDb.created_at
    report_date=report_date_found.date()
    return report_date
    
def DeleteReportById(report_id):
    try:

        report_get=Report.objects.get(id=report_id)
        print('founded report')
        try:

            task_get=Task.objects.filter(reports=report_get)

            print('deleted all datas from',report_get.name)
            report_get.delete()
            return 'Report deleted'
        except:
            report_get.delete()
            print('report deleted')
            return 'Report deleted'
    except:
        print('nothing found')
        return 'No report found in this id'
    
    
def saveReportName(project_name):
    projectDb=ProjectFromWorkzone.objects.get(name=project_name)
    reportName=project_name+' Report'
    Report_Db=Report()
    Report_Db.product_id=projectDb
    Report_Db.report_name=reportName
    Report_Db.created_at=datetime.now()
    Report_Db.updated_at=datetime.now()
    Report_Db.save()
    return Report_Db

def CheckReportExist(project_id):
    if Report.objects.filter(product_id=project_id).exists():
        report=Report.objects.filter(product_id=project_id).order_by('created_at').latest('created_at')
        report_date=report.created_at
        date_today=datetime.now()
        created_Date=report_date
        time_difference=date_today.date()-created_Date.date()
        days_difference=time_difference.days
        return days_difference
    else:
        return 'NewProject'

def ReportNameList():
    reports=Report.objects.all()
    return reports

    
def FetchReportData(project_id,search_key,start_date,end_date):
    try:
        if start_date and end_date:
            reports=Report.objects.filter(product_id=project_id,created_at__range=[start_date,end_date]).order_by('-created_at')
            if(len(reports)==0):
                reports=Report.objects.filter(product_id=project_id,created_at__date=start_date).order_by('-created_at')

        else:
            reports=Report.objects.filter(product_id=project_id).order_by('-created_at')
        if reports:
            reports = reports.filter(Q(report_name__icontains=search_key)).order_by('-created_at')
        return reports
    except:
        return 'Report Id not found'

def FetchTaskData(report_id,search_key):
    try:
        #CHECKING IF PROJECT EXIST IN DB
        tasks=Task.objects.filter(reports__id=report_id).order_by('-startdate','-enddate')
        if tasks:
            tasks=tasks.filter(Q(task_title__icontains=search_key)|Q(workspacename__icontains=search_key)|Q(status__icontains=search_key))
        return tasks
        # active_tasks=Task.objects.filter(reports__id=report_id,status="Active")
        # pending_tasks=Task.objects.filter(reports__id=report_id,status="Penidng")
        # completed_tasks=Task.objects.filter(reports__id=report_id,status="Completed")
        # new_tasks=Task.objects.filter(reports__id=report_id,status="New")
        # return {active_tasks:active_tasks,pending_tasks:pending_tasks,completed_tasks:completed_tasks,new_tasks:new_tasks}
    except:
        #IF PROJECT NAME DOESN'T EXIST
        return 'Task Id not found'

def saveNewTaskDb(newTask,report):
    for i in range(1,len(newTask)):

        new_taskDb=Task()
        new_taskDb.reports=report
        new_taskDb.task_id=newTask[i]['taskid']
        new_taskDb.task_title=(newTask[i]['taskname'].replace('\\',''))
        new_taskDb.status=newTask[i]['status']
        new_taskDb.workspacename=newTask[i]['workspacename']
        new_taskDb.startdate=newTask[i]['startdate']
        new_taskDb.enddate=newTask[i]['enddate']
        new_taskDb.save()

def saveCompletedTaskDb(completeTask,report):
    
    for i in range(1,len(completeTask)):
        completed_taskDb=Task()
        completed_taskDb.reports=report
        completed_taskDb.task_id=completeTask[i]['taskid']
        completed_taskDb.task_title=(completeTask[i]['taskname'].replace('\\',''))
        completed_taskDb.status=completeTask[i]['status']
        completed_taskDb.workspacename=completeTask[i]['workspacename']
        completed_taskDb.startdate=completeTask[i]['startdate']
        completed_taskDb.enddate=completeTask[i]['enddate']
    
        completed_taskDb.save()

def saveActiveTaskDb(activeTask,report):
    
    for i in range(1,len(activeTask)):
        active_taskDb=Task()
        active_taskDb.reports=report
        active_taskDb.task_id=activeTask[i]['taskid']
        active_taskDb.task_title=(activeTask[i]['taskname'].replace('\\',''))
        active_taskDb.status=activeTask[i]['status']
        active_taskDb.workspacename=activeTask[i]['workspacename']
        active_taskDb.startdate=activeTask[i]['startdate']
        active_taskDb.enddate=activeTask[i]['enddate']
        active_taskDb.save()


def dbTaskData(report_id):
    report_found=Report.objects.get(id=report_id)
    completed=[]
    active=[]
    new=[]
    final_date=[]
    tasks=Task.objects.filter(reports=report_found)
    for i in tasks:
        task_name=i.task_title
        final_date.append(i.enddate)
        if i.status=='Completed':
            completed.append({'taskid':i.task_id,'taskname':task_name,'status':i.status,'workspacename':i.workspacename,'startdate':i.startdate,'enddate':i.enddate})
        elif(i.status=='New'):
            new.append({'taskid':i.task_id,'taskname':task_name,'status':i.status,'workspacename':i.workspacename,'startdate':i.startdate,'enddate':i.enddate})
        else:
            active.append({'taskid':i.task_id,'taskname':task_name,'status':i.status,'workspacename':i.workspacename,'startdate':i.startdate,'enddate':i.enddate})
    tasklist=[completed,active,new,final_date]
    return tasklist

def findReportName(report_id):
    report_id_found=Report.objects.get(id=report_id)
    project_name=report_id_found.product_id.name
    return project_name

def findProjectIdByName(project_name):

    project_name=ProjectFromWorkzone.objects.get(name=project_name)
    return project_name


def isLightOrDark(rgbColor):
        [r,g,b]=rgbColor
        hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        if (hsp>200):
            return 'light'
        else:
            return 'dark'

def convert_bytes(size):
    """ Convert bytes to KB, or MB or GB"""
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
        
def LogoImageSave(project_id,imageLogo):
    project=ProjectFromWorkzone.objects.get(id=project_id)
    try:
        DbLogo=get_object_or_404(ProjectLogo,project_id=project)
        if DbLogo.logo_image:
            DbLogo.logo_image.delete()
        DbLogo.delete()

        DbLogo=ProjectLogo()
        DbLogo.project_id=project
        DbLogo.logo_image=imageLogo
        DbLogo.save()
        
        return 'saved to db'

    except:
        DbLogo=ProjectLogo()
        DbLogo.project_id=project
        DbLogo.logo_image=imageLogo
        DbLogo.save()
        return 'saved to db'

def LogoGetImage(project_id):
    try:
        image=ProjectLogo.objects.get(project_id=project_id)
        return image
    except:
        image=default_logo.objects.all()[:1].get()
        return image
def save_pdf_url(report_id,encoded_string,size_pdf):   
    print('\n\n\ninside utils save pdf')
    report=Report.objects.get(id=report_id)
    pdf_save=Report_Pdf()
    pdf_save.report_id=report
    pdf_save.report_pdf=encoded_string 
    pdf_save.report_size=size_pdf
    pdf_save.save()

    return pdf_save
    # except:
    #     pass

def get_url_pdf(report_id):
    report_found=Report.objects.get(id=report_id)
    print('\n\n\nReport id: ',report_found,'\n\n\n')
    report_url=Report_Pdf.objects.get(report_id=report_found)
    return report_url

def pdfToBase64view(url):
    with open(url, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
    
    return encoded_string

def task_notifications(request):
    user = request.user
    org_id = Role.objects.filter(user=request.user).first()
    if org_id.role != "superadmin":

        task_notification = TaskNotification.objects.filter(org_user=user,higlight_status="unseen").order_by("-created_at")[:10]   
        if task_notification:        
            serializer = TaskNotifcationSerializer(task_notification,many=True)
        else:
                return []
            
    elif org_id.role == "superadmin":
        
        history = TaskNotification.objects.filter(org_user=user,higlight_status="unseen").exclude(action_user=request.user.id).order_by("-created_at")[:10]
        if history:
                
                serializer = TaskNotifcationSerializer(history,many=True)
        else:
            return []
    return serializer.data
def saveReadStatus(user,report_id):
    user_found=User.objects.get(id=user)
    try:
        share_list=ReportShare.objects.filter(receiver__id=user,report__id=report_id,status="sent").update(status='seen')
        # new_list = []
        # for data in share_list:
        #     data.id = None
        #     data.status = 'seen'
        #     data.save()
        return 'status changed to seen'
    
    except:
        return 'user not found'

def organizationProjectMap(project_id):
    project=ProjectFromWorkzone.objects.get(id=project_id)
    if project.organization_data==None:
        project_name=project.name
        project_name_cap=project_name.lower()
        if Organization.objects.filter(name=project_name).exists():
            organization_found=Organization.objects.get(name=project_name)
            project_name_save=ProjectFromWorkzone.objects.get(id=project_id)
            project_name_save.organization_data=organization_found
            project_name_save.save()
            return organization_found
        elif Organization.objects.filter(name=project_name_cap).exists():
            organization_found=Organization.objects.get(name=project_name_cap)
            project_name_save=ProjectFromWorkzone.objects.get(id=project_id)
            project_name_save.organization_data=organization_found
            project_name_save.save()
            return organization_found
        else:
            pass
    else:
        pass

def ReportNotification(report):
    superusers = User.objects.filter(is_superuser=True)
    superadmin=User.objects.filter(is_superuser=True)[:1].get()
    try:
        usr=[]
        organization=report.product_id.organization_data
        orgadmin=Role.objects.filter(organization=organization)
        
        for i in orgadmin:            
            if(i in usr):
                pass
            else:
                usr.append(i.user)
                notification=TaskNotification()
                notification.report=report
                notification.action_user=superadmin
                notification.action_type="create"
                notification.org_user=i.user
                notification.save()

        for i in superusers:
            if(i in usr):
                pass
            else:
                notification=TaskNotification()
                notification.report=report
                notification.action_user=superadmin
                notification.action_type="create"
                notification.org_user=i
                notification.save()
        print('\n\n\n notification saved to db \n\n\n')
    except:
        for i in superusers:
            notification=TaskNotification()
            notification.report=report
            notification.action_user=superadmin
            notification.action_type="create"
            notification.org_user=i
            notification.save()

        print('\n\n\n notification saved to db \n\n\n')

    
    


