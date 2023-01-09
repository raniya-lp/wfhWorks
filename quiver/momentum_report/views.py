import base64
from ctypes import util
from http import client
from traceback import print_tb
from venv import create
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render

from users.models import Organization, Role
from . serializers import *
from . models import *
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.viewsets import GenericViewSet
from projects .models import Projects
from . import utils
from . import workzone_functions
from users.models import User,Organization,Role
import math
import extcolors
from datetime import datetime, timedelta
import spintax
import tempfile
import platform
import pdfkit
import os
from pandas.io import json 
from PIL import Image
import tempfile
from momentum_report import utils
from generics import permissions
from projects import models as prg_model
from projects.models import ProjectsOrganizationMapping
from users import models as user_model
from generics import exceptions
from uuid import UUID
from django.template import RequestContext
from django.conf import settings
import cgi
import os
from django.core.files.storage import FileSystemStorage
from django.shortcuts import HttpResponse
from django.template.loader import get_template, render_to_string
from io import BytesIO
from django.template import loader,Context
from momentum_report import utils
from django.core.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.generics import GenericAPIView
import threading
from users import functions as user_fn
from django.core.files.storage import FileSystemStorage
from users import configurations
from django.db.models import F

# Create your views here.


#function to scheduling report on fridays. 
#this will reset all tasks and projects from db and will create new report ids and task ids.

def update_Report():

    #this will check in workzone if any new workzone names are created, if created, it will ba saved to database.

    workspace_names=workzone_functions.saveProjectToDb()

    #to save all workspace ids
    workspace_db_ids=[]

    #for passing values to front end
    output_workspace=[]

    #fetching each workspace name from workzone and collecting ids from our database
    for workspace_name in workspace_names:
        try:
            workspace_id=utils.findProjectIdByName(workspace_name)
            workspace_db_ids.append(workspace_id.id)
        except:
            pass
    
    #using each workspace id, creating each new reports and generating all task lists and saving it to database
    for project_id in workspace_db_ids:
        organization_update=utils.organizationProjectMap(project_id)
        #a try to in case project name doeant existed in db
        try:
            project_name_db=utils.projectDbFinder(project_id)

            project_name=project_name_db.name

            #saving new report id with current workzone status
            saveReport=utils.saveReportName(project_name)
            #FETCHING PROJECT DETAILS
            projectData=workzone_functions.projectIdFromWorkzone(project_name,'XLZGTfYP-rJnBoiG','b7nWz-RLavkv2j_YUHslRFywfNFAJSwF','client_credentials')
            for i in projectData:

                #workzone connection and data collection
                projectReportData=workzone_functions.projectReportDataFetch('XLZGTfYP-rJnBoiG','b7nWz-RLavkv2j_YUHslRFywfNFAJSwF','client_credentials',i['id'])
                #to save new tasks to db
                if(len(projectReportData[0]['new'])>1):

                    saveNew=utils.saveNewTaskDb(projectReportData[0]['new'],saveReport)

                #to save active task
                if(len(projectReportData[0]['active'])>1):

                    saveActive=utils.saveActiveTaskDb(projectReportData[0]['active'],saveReport)

                #to save completed tasks
                if(len(projectReportData[0]['completed'])>1):

                    saveCompleted=utils.saveCompletedTaskDb(projectReportData[0]['completed'],saveReport)
                
            report_id=saveReport.id
            #saving each tasks to db using each report id and project id
            taskData=utils.dbTaskData(report_id)
            if(len(taskData[0])==0 and len(taskData[1])==0 and len(taskData[2])==0):
                pass
            else:
                #taking report ids and details to create pdf
                project_name=utils.findReportName(report_id)
                #finding folder
                project_folder=project_name.lower().replace(" ","_")
                #fetching logo image for the corresponding workzone from db
                img_found=utils.LogoGetImage(project_name_db.id)
                
                #image path
                logo=img_found.logo_image
                
                #collecting colors from corersponding logo
                colors, pixel_count = extcolors.extract_from_path(logo)
                selected_colors=[]
                for color_item in colors:
                    if(utils.isLightOrDark(color_item[0])=='dark'):
                        selected_colors.append(color_item[0])
                #pdf sizes and conditions
                options = {
                        'page-size': 'A4',
                        'margin-top': '0in',
                        'margin-right': '0in',
                        'margin-bottom': '0.4in',
                        'margin-left': '0in',
                        'encoding': "UTF-8", 
                        'custom-header' : [('Accept-Encoding', 'gzip')],
                        'no-outline':None 
                        }

            #taking report ids and details to create pdf
            project_name=utils.findReportName(report_id)
            #finding folder
            project_folder=project_name.lower().replace(" ","_")
            print('\n\n\n',project_folder,'\n\n\n')
            #fetching logo image for the corresponding workzone from db
            img_found=utils.LogoGetImage(project_name_db.id)
            
            print('\n\nImage foun: ',img_found.logo_image)
            #image path
            logo=img_found.logo_image
            print('\n\nLogo: ',logo)
            
            #collecting colors from corersponding logo
            colors, pixel_count = extcolors.extract_from_path(logo)
            selected_colors=[]
            for color_item in colors:
                if(utils.isLightOrDark(color_item[0])=='dark'):
                    selected_colors.append(color_item[0])
            #pdf sizes and conditions
            options = {
                    'page-size': 'A4',
                    'margin-top': '0in',
                    'margin-right': '0in',
                    'margin-bottom': '0.4in',
                    'margin-left': '0in',
                    'encoding': "UTF-8", 
                    'custom-header' : [('Accept-Encoding', 'gzip')],
                    'no-outline':None 
                    }

            #Report date to print in pdf cover page
            report_date=utils.FindReportWeekDate(report_id)
            # if (len(taskData[3])==0):
            #     final_project_date='not defined'
            # else:
            try:
                final_project_date=max(taskData[3])
                
                #temporary file for footer
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                    options['--footer-html'] = header.name
                    header.write(
                        render_to_string('footer.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'color':selected_colors[0]}).encode('utf-8')
                    )

                #temporary file for header
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                    options['--header-html'] = header.name
                    header.write(
                        render_to_string('header.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'report_date':report_date,'color':selected_colors[0]}).encode('utf-8')
                    )

                #temporary file for cover
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as cover:
                    cover.write(
                        render_to_string('cover.html',{'project_name':project_name,'report_date':report_date,'finish_date':final_project_date,'rooturl':settings.ROOT_URL,'logo':img_found,'colors':selected_colors}).encode('utf-8')
                    )
                try:
                    os.mkdir(settings.MEDIA_ROOTPDF+project_folder)
                except FileExistsError:
                    pass
                #folder to save pdf reports to the corresponding folders
                output_file=f"{project_folder}/{report_id}report.pdf"       
                print('\n\n\n'+output_file+'\n\n\n')
                Pdfurl=settings.MEDIA_URLPDF+output_file
                print('url: ',Pdfurl)           
                        
                print('\n\n\ncolors total: ',selected_colors,'\n\n\n')

                #passing all collected details to html
                organization_users=utils.ReportNotification(saveReport)
                pdf = render_to_string('view-report.html',{'project_name':project_name,'report_date':report_date, 'itemsCompleted':taskData[0],'itemsActive':taskData[1],'itemsNew':taskData[2],'rooturl':settings.ROOT_URL,'zip':zip,'colors':selected_colors[0],'options':options})
                print('pdf rendering')
                filename_output=f"{settings.MEDIA_ROOTPDF}{output_file}"
                try:
                #pip install pdfkit
                #pdf kit to convert all the htmls collected to pdf file.
                    pdfop=pdfkit.from_string(pdf,f"{settings.MEDIA_ROOTPDF}{output_file}",configuration=settings.CONFIGPDF,options=options,cover=cover.name, cover_first=True)
                    file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                    print('file :',file_size_bytes)
                    file_size=utils.convert_bytes(file_size_bytes)
                    print('returning')
                    output_workspace.append(project_id)
                    print(filename_output)
                    print('\n\n-------------\ninside try\n------\n\n')
                
                    file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                    pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 

                
            
                #os error occurs sometimes eventhough we get the correct output. so and exception in advance.
                except OSError:
                    output_workspace.append(project_id)
                    print(filename_output)
                    print('\n\n-------------\ninside except\n------\n\n')
                    
                    file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                    print('file :',file_size_bytes)
                    file_size=utils.convert_bytes(file_size_bytes)
                    file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                    pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 
                
                org_id = ProjectFromWorkzone.objects.filter(id=project_id).values_list('organization_data__id',flat = True).get()
                super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).values_list('user',flat=True)
                mail_org_name=ProjectFromWorkzone.objects.get(id=project_id)
                #to get output as day-monthinwords-year
                mon=report_date.strftime('%B')
                dt_mom=mon+' '+str(report_date.strftime('%d'))+','+str(report_date.strftime('%Y'))

                if org_id:
                    final_user = list(org_user_list) + list(super_admin_list)
                else:
                    final_user = list(super_admin_list)
                for i in final_user:
                    receiver_user = user_model.User.objects.get(id=i)
                    email_args = {
                    'full_name': f"{receiver_user.first_name}".strip(),
                    'email': receiver_user.username,
                    'origin'  : f"{configurations.MOMENTUM_SHARE_URL}{report_id}",
                    'app'    : "Momentum Report: "+str(mail_org_name.name)+str('(Week of '+dt_mom+')'),
                    }
                    # Send Email as non blocking thread. Reduces request waiting time.
                    t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_momentum_auto_report_email)
                    t.start() 
            except ValueError:
                pass
        except ValidationError:
            print('Project id not found')
    
    return output_workspace

#an api to check whether scheduling api works or not.
class SchedulingApiTesting(GenericViewSet):
    
    @extend_schema(
        tags=['Momentum Report'],
        responses={
            200:dict,
            400:dict,
        }
    )
    def getlist(self,request):
        #to schedule report weekly.api to customize it.
        upd=update_Report()
        return HttpResponse(upd)

#to upload logo to each workzones
class ProjectLogoUploadView(GenericViewSet):
    
    serializer_class= LogoImageSerializer
    @extend_schema(
        tags=['Momentum Report'],
        request=LogoImageSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def create(self,request):
        sv=LogoImageSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        project_id=sv.validated_data.get('project_id')
        image=sv.validated_data.get('image')
        #function to save logo and project id to database
        DbLogoSave=utils.LogoImageSave(project_id,image)
        return HttpResponse(DbLogoSave)


#to save project names to db
class saveProjectToDbView(GenericViewSet):
    
    @extend_schema(
        tags=['Momentum Report'],
        responses={
            200:dict,
            400:dict,
        }
    )
    def getlist(self,request):
        #this will save all workzone workspace name to database
        dbDataSave=workzone_functions.saveProjectToDb()
        return Response(data={'SavedToDb':dbDataSave})


#TO GET PROJECT NAMES DEPENDING UPON ORGANIZATION
class ProjectView(GenericViewSet):

    @extend_schema(
        tags=['Momentum Report'],
        responses={
            200:dict,
            400:dict,
        }
    )
    def getlist(self,request):
    
        projectsList=[]
        #to view worksapce names and details by user category
        data_workspace=utils.ListProjectsByOrganization(request.user.id)
        if data_workspace is not None:
            try:
                #if user is a super admin, user can view all data
                for i in data_workspace:
                    # import pdb;pdb.set_trace()
                    assignee_list = list(ReportShare.objects.filter(report__product_id__id = i.id).distinct('receiver__id').annotate(userid=F('receiver__id'),first_name=F('receiver__first_name'),last_name=F('receiver__last_name')).values('userid','first_name','last_name'))
                    if assignee_list == [] and i.organization_data:
                        org_id = Organization.objects.get(id=i.organization_data.id)
                        assignee_list = list(Role.objects.filter(organization__id = org_id.id).distinct('user__id').annotate(userid=F('user__id'),first_name=F('user__first_name'),last_name=F('user__last_name')).values('userid','first_name','last_name'))
                    comments_count = TaskComments.objects.filter(task__reports__product_id__id = i.id).count()
                    projectsList.append({"id":str(i.id),"title":str(i.name),"created_at":i.created_at.strftime("%d-%m-%Y %I:%M:%S %p"),"updated_at":i.updated_at.strftime("%d-%m-%Y %I:%M:%S %p"),'status':str(i.status),'notification_count':comments_count,"collaborators":assignee_list})
                return Response(data={'results':projectsList}, status=status.HTTP_201_CREATED)

            except:
                #if user is an organization admin, user can only view data of that organization.
                i=data_workspace
                assignee_list = list(ReportShare.objects.filter(report__product_id__id = i.id).distinct('receiver__id').annotate(user_id=F('receiver__id'),first_name=F('receiver__first_name'),last_name=F('receiver__last_name')).values('user_id','first_name','last_name'))
                comments_count = TaskComments.objects.filter(task__reports__product_id__id = i.id).count()
                projectsList=[{"id":str(i.id),"title":str(i.name),"created_at":i.created_at.strftime("%d-%m-%Y %I:%M:%S %p"),"updated_at":i.updated_at.strftime("%d-%m-%Y %I:%M:%S %p"),'status':str(i.status),'notification_count':comments_count,"collaborators":assignee_list}]
                return Response(data={'results':projectsList}, status=status.HTTP_201_CREATED)
        else:
            #if user is not added to any of the category, then user cannot view any of the workspace details.
            return Response(data={'user':'user is not added to any of the organization or super admin category.'})
class ProjectByIdView(GenericViewSet):
    serializer_class= projectIdSerializer
    @extend_schema(
        tags=['Momentum Report'],
        request=projectIdSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def create(self,request):

        #INPUTTING CREDENTIALS AND PROJECT ID
        sv=projectIdSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        project_id=sv.validated_data.get('project_id')
        projectData=utils.projectDbFinder(project_id)

        srv=ProjectByIdSerializer(projectData)
        return Response(data={'data':srv.data})

class ReportIdView(GenericViewSet):

    @extend_schema(
        tags=['Momentum Report'],
        responses={
            200:dict,
            400:dict,
        }
    )
    def getlist(self,request):
        #this will view all report data's under each workspaces.
        reportDatas=utils.ReportNameList()
        srs=ReportListViewSerializer(reportDatas,many=True)
        return Response(data={'Reportid':srs.data})


#to generate a pdf of a selected project
#not a necessery api. but created for backend testing purpose. no front end use.
class GenerateReportCustomized(GenericViewSet):
    serializer_class= ReportGenerateSerializer
    @extend_schema(
        tags=['Momentum Report'],
        request=ReportGenerateSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def create(self,request):

        #INPUTTING CREDENTIALS AND PROJECT ID
        sv=ReportGenerateSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        project_id=sv.validated_data.get('project_id')
        client_id=sv.validated_data.get('client_id')
        client_secret=sv.validated_data.get('client_secret')
        grant_type=sv.validated_data.get('grant_type')
        

        try:
            project_name_db=utils.projectDbFinder(project_id)
            print('\n\n\ntasks found: 1',)
            ReportStatusInDb=utils.CheckReportExist(project_id)
            print('\n\n\ntasks found: 2',)
            if(ReportStatusInDb=='NewProject' or ReportStatusInDb==7):
                print('\n\n\ntasks found: 3',)

                #finding project name
                
                project_name=project_name_db.name

                #to save report name
                saveReport=utils.saveReportName(project_name)
                #FETCHING PROJECT DETAILS
                projectData=workzone_functions.projectIdFromWorkzone(project_name,client_id,client_secret,grant_type)
                for i in projectData:

                    #workzone connection and data collection
                    projectReportData=workzone_functions.projectReportDataFetch(client_id,client_secret,grant_type,i['id'])

                    #to save new tasks to db
                    if(len(projectReportData[0]['new'])>1):

                        saveNew=utils.saveNewTaskDb(projectReportData[0]['new'],saveReport)

                    #to save active task
                    if(len(projectReportData[0]['active'])>1):

                        saveActive=utils.saveActiveTaskDb(projectReportData[0]['active'],saveReport)

                    #to save completed tasks
                    if(len(projectReportData[0]['completed'])>1):

                        saveCompleted=utils.saveCompletedTaskDb(projectReportData[0]['completed'],saveReport)
                    
                report_id=saveReport.id
                taskData=utils.dbTaskData(report_id)
                if(len(taskData[0])==0 and len(taskData[1])==0 and len(taskData[2])==0):
                    return Response(data={'Result':'No datas found'})
                else:
                    project_name=utils.findReportName(report_id)
                    project_folder=project_name.lower().replace(" ","_")
                    img_found=utils.LogoGetImage(project_name_db.id)

                    logo=img_found.logo_image                    

                    colors, pixel_count = extcolors.extract_from_path(logo)
                    selected_colors=[]
                    for color_item in colors:
                        if(utils.isLightOrDark(color_item[0])=='dark'):
                            selected_colors.append(color_item[0])

                    options = {
                            'page-size': 'A4',
                            'margin-top': '0in',
                            'margin-right': '0in',
                            'margin-bottom': '0.4in',
                            'margin-left': '0in',
                            'encoding': "UTF-8", 
                            'custom-header' : [('Accept-Encoding', 'gzip')],
                            'no-outline':None 
                            }

                    report_date=utils.FindReportWeekDate(report_id)
                    
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                        options['--footer-html'] = header.name
                        header.write(
                            render_to_string('footer.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'color':selected_colors[0]}).encode('utf-8')
                        )
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                            options['--header-html'] = header.name
                            header.write(
                                render_to_string('header.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'report_date':report_date,'color':selected_colors[0]}).encode('utf-8')
                            )
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as cover:
                        cover.write(
                            render_to_string('cover.html',{'project_name':project_name,'report_date':report_date,'finish_date':report_date,'rooturl':settings.ROOT_URL,'logo':img_found,'colors':selected_colors}).encode('utf-8')
                        )
                    try:
                        os.mkdir(settings.MEDIA_ROOTPDF+project_folder)
                    except FileExistsError:
                        pass
                    output_file=f"{project_folder}/{report_id}report.pdf"  
                    Pdfurl=settings.MEDIA_URLPDF+output_file
                    pdf = render_to_string('view-report.html',{'project_name':project_name,'report_date':report_date, 'itemsCompleted':taskData[0],'itemsActive':taskData[1],'itemsNew':taskData[2],'rooturl':settings.ROOT_URL,'zip':zip,'colors':selected_colors[0],'options':options})
                    try:
                        pdfop=pdfkit.from_string(pdf,f"{settings.MEDIA_ROOTPDF}{output_file}",configuration=settings.CONFIGPDF,options=options,cover=cover.name, cover_first=True)
                        file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        file_size=utils.convert_bytes(file_size_bytes)
                        file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 
                        pdf_code=pdfSave.report_pdf
                        output_display={'Projectid':project_id,'ProjectName':project_name,'ReportId':report_id,'folderurl':settings.MEDIA_URLPDF+output_file,'created_at':report_date,'Filesize':file_size,'pdfcode':pdf_code}

                        return HttpResponse(str(output_display))
                    except OSError:

                        file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        file_size=utils.convert_bytes(file_size_bytes)
                        file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 
                        pdf_code=pdfSave.report_pdf
                        output_display={'Projectid':project_id,'ProjectName':project_name,'ReportId':report_id,'folderurl':settings.MEDIA_URLPDF+output_file,'created_at':report_date,'Filesize':file_size,'pdfcode':pdf_code}

                        return HttpResponse(str(output_display))

            else:
                #finding project name
                report_id=utils.ReportDbFinderByProjectId(project_id)
                taskData=utils.dbTaskData(report_id)
                if(len(taskData[0])==0 and len(taskData[1])==0 and len(taskData[2])==0):
                    return Response(data={'Result':'No datas found'})
                else:
                    project_name=utils.findReportName(report_id)
                    project_folder=project_name.lower().replace(" ","_")
                    img_found=utils.LogoGetImage(project_name_db.id)
                    logo=img_found.logo_image

                    colors, pixel_count = extcolors.extract_from_path(logo)
                    selected_colors=[]
                    for color_item in colors:
                        if(utils.isLightOrDark(color_item[0])=='dark'):
                            selected_colors.append(color_item[0])

                    options = {
                            'page-size': 'A4',
                            'margin-top': '0in',
                            'margin-right': '0in',
                            'margin-bottom': '0.4in',
                            'margin-left': '0in',
                            'encoding': "UTF-8", 
                            'custom-header' : [('Accept-Encoding', 'gzip')],
                            'no-outline':None 
                            }

                    report_date=utils.FindReportWeekDate(report_id)
                    
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                        options['--footer-html'] = header.name
                        header.write(
                            render_to_string('footer.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'color':selected_colors[0]}).encode('utf-8')
                        )
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header:
                            options['--header-html'] = header.name
                            header.write(
                                render_to_string('header.html',{'project_name':project_name,'rooturl':settings.ROOT_URL,'report_date':report_date,'color':selected_colors[0]}).encode('utf-8')
                            )
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as cover:
                        cover.write(
                            render_to_string('cover.html',{'project_name':project_name,'report_date':report_date,'finish_date':report_date,'rooturl':settings.ROOT_URL,'logo':img_found,'colors':selected_colors}).encode('utf-8')
                        )
                    try:
                        os.mkdir(settings.MEDIA_ROOTPDF+project_folder)
                    except FileExistsError:
                        pass
                    output_file=f"{project_folder}/{report_id}report.pdf"   
                    Pdfurl=settings.MEDIA_URLPDF+output_file
                    pdf = render_to_string('view-report.html',{'project_name':project_name,'report_date':report_date, 'itemsCompleted':taskData[0],'itemsActive':taskData[1],'itemsNew':taskData[2],'rooturl':settings.ROOT_URL,'zip':zip,'colors':selected_colors[0],'options':options})
                    try:
                        fs = FileSystemStorage()
                        pdfop=pdfkit.from_string(pdf,f"{settings.MEDIA_ROOTPDF}{output_file}",configuration=settings.CONFIGPDF,options=options,cover=cover.name, cover_first=True)
                        
                        file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        file_size=utils.convert_bytes(file_size_bytes)
                        file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 
                        pdf_code=pdfSave.report_pdf
                        pdf_code_conv=pdf_code.decode("utf-8") 
                        output_display={'Projectid':project_id,'ProjectName':project_name,'ReportId':report_id,'folderurl':settings.MEDIA_URLPDF+output_file,'created_at':report_date,'Filesize':file_size,'pdfcode':pdf_code_conv}

                        return HttpResponse(str(output_display))
                    except OSError:
                        file_size_bytes=os.path.getsize(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        file_size=utils.convert_bytes(file_size_bytes)
                        file_base64=utils.pdfToBase64view(f"{settings.MEDIA_ROOTPDF}{output_file}")
                        pdfSave=utils.save_pdf_url(report_id,file_base64,file_size) 
                        pdf_code=pdfSave.report_pdf
                        pdf_code_conv=pdf_code.decode("utf-8") 
                        output_display={'Projectid':project_id,'ProjectName':project_name,'ReportId':report_id,'folderurl':settings.MEDIA_URLPDF+output_file,'created_at':report_date,'Filesize':file_size,'pdfcode':pdf_code_conv}

                        return HttpResponse(str(output_display))

        except ProjectLogo.DoesNotExist:
            return HttpResponse('Logo image doeasnot exist. please upload a logo image for this project')
                        
        except ValidationError:
            return HttpResponse('Project id not found')

        

#TO DELETE A REPORT BY ID
class DeleteReportByIdView(GenericViewSet):
    serializer_class= ReportIdSerializer
    @extend_schema(
        tags=['Momentum Report'],
        request=ReportIdSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def create(self,request):
        #INPUTTING REPORT ID
        sv=ReportIdSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        report_id=sv.validated_data.get('report_id')
        #MAIN FUNCTION IN UTILS.PY
        delete_status=utils.DeleteReportById(report_id)
        return Response(data={'Result':delete_status})


class ReportListView(APIView):
    """
    A simple ViewSet for viewing and editing accounts.
    
    """
    permission_classes  = [IsAuthenticated]
    @extend_schema(
        tags=['Momentum Report'],
        request   = ReportListSerializer,
        responses = {
                200: dict,
                404: dict,
        }
    ) 
    def post(self, request):
        sv=ReportListSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        project_id=sv.validated_data.get('product_id')
        search_key=sv.validated_data.get('keyword')
        start_date=sv.validated_data.get('start_date')
        end_date=sv.validated_data.get('end_date')
        # queryset = models.Report.objects.filter(product_id=request.POST['productId'])
        # serializer  = ReportListSerializer(queryset, many=True)
        data = utils.FetchReportData(project_id,search_key,start_date,end_date)
        if data == 'Report Id not found':
            return Response({"status":0,"error":data})
        else:
            res_data = []
            for i in data:
                res_data.append({"report_name":i.report_name,"id":i.id,"created_at":i.created_at,"updated_at":i.updated_at})
            return Response({"status":1,"report_list":res_data,"count":len(data)})


class TaskListView(APIView):
    """
    A simple ViewSet for viewing and editing accounts.
    
    """
    permission_classes  = [IsAuthenticated]
    @extend_schema(
        tags=['Momentum Report'],
        request   = TaskListSerializer,
        responses = {
                200: dict,
                404: dict,
        }
    ) 
    def post(self, request):
        sv=TaskListSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        report_id=sv.validated_data.get('report_id')
        search_key=sv.validated_data.get('keyword')
        # queryset = models.Report.objects.filter(product_id=request.POST['productId'])
        # serializer  = ReportListSerializer(queryset, many=True)
        data = utils.FetchTaskData(report_id,search_key)
        active_data = []
        new_data = []
        completed_data = []
        for i in data:
            tags = []
            if i.status == 'Active' or i.status == 'active':
                comments_count = TaskComments.objects.filter(task__id=i.id).count()
                comments = list(TaskComments.objects.filter(task__id=i.id).values('comments'))
                for data in comments:
                    tags = tags + data['comments']['tags']
                active_data.append({"task_name":i.task_title,"id":i.id,"task_id":i.task_id,"start_date":i.startdate,"end_date":i.enddate,"status":i.status,"workspace_name":i.workspacename,"comments_count":comments_count,"tags":tags})
            elif i.status == 'New' or i.status == 'new':
                comments_count = TaskComments.objects.filter(task__id=i.id).count()
                comments = list(TaskComments.objects.filter(task__id=i.id).values('comments'))
                for data in comments:
                    tags = tags + data['comments']['tags']
                new_data.append({"task_name":i.task_title,"id":i.id,"task_id":i.task_id,"start_date":i.startdate,"end_date":i.enddate,"status":i.status,"workspace_name":i.workspacename,"comments_count":comments_count,"tags":tags})
            elif i.status == 'Completed' or i.status == 'completed':
                comments_count = TaskComments.objects.filter(task__id=i.id).count()
                comments = list(TaskComments.objects.filter(task__id=i.id).values('comments'))
                for data in comments:
                    tags = tags + data['comments']['tags']
                completed_data.append({"task_name":i.task_title,"id":i.id,"task_id":i.task_id,"start_date":i.startdate,"end_date":i.enddate,"status":i.status,"workspace_name":i.workspacename,"comments_count":comments_count,"tags":tags})
        sent_count = ReportShare.objects.filter(report_id=report_id,status="sent").count()
        viewed_count = ReportShare.objects.filter(report_id=report_id,status="seen").count()
        TaskNotification.objects.filter(task__reports__id=report_id,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
        return Response({"new_tasks":new_data,"active_tasks":active_data,"completed_tasks":completed_data,"sent_count":sent_count+viewed_count,"viewed_count":viewed_count})


class TasksCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete tasks comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    # serializer_class    = taskCreateSerializer
    request   = TaskCommentSerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,task):
        comments = TaskComments.objects.filter(task_id= task)
        
        if comments:
             
            return comments
        else:
            return "NA"
    
    @extend_schema(
    tags=['Momentum Report'],
    request   = TaskCommentSerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    def create(self, request, *args, **kwargs):
        """
        Create task comments
        """
        try:
            serializer = TaskCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)

            
            #For task notificationorganization
            if request.user.is_superuser:
                org_id = ProjectFromWorkzone.objects.filter(id=instance.task.reports.product_id.id).values_list('organization_data__id',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)
                task_notif = list(map(lambda user: TaskNotification(task=instance.task,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                TaskNotification.objects.bulk_create(task_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                task_notif = list(map(lambda user: TaskNotification(task=instance.task,action_user=request.user,action_type="comment",org_user_id=user,comment=instance), final_user))
                TaskNotification.objects.bulk_create(task_notif)         
            ProjectFromWorkzone.objects.filter(id=instance.task.reports.product_id.id).update(updated_at=datetime.now())
            Report.objects.filter(id=instance.task.reports.id).update(updated_at=datetime.now())
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)   

    @extend_schema(
    tags=['Momentum Report'],
    request   = None,
    parameters=[

      OpenApiParameter(name='task_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: TaskCommentListSerializer})
    
    def list(self, request):
        """
        Lists all ScheduleGroups
        
        @TODO: Add pagination
        """
        task = request.query_params.get('task_id')
        querset     = self.get_queryset(task)
        if querset != "NA":
            
            serializer  = TaskCommentListSerializer(querset,many=True)
            comments_count = TaskComments.objects.filter(task_id= task).values_list("id",flat=True)
            
            task = TaskNotification.objects.filter(comment__in=list(comments_count),org_user=request.user,action_type="comment",higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            # return Response(serializer.data) 
            return Response(data={"detail": "Comments fetched","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)

    
    @extend_schema(
    tags=['Momentum Report'],
    request   = TaskCommentUpdateSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: TaskCommentUpdateSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = TaskComments.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = TaskCommentUpdateSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Momentum Report'],
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
        obj     = TaskComments.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)


class ReportDocmentShare(viewsets.ViewSet):
    @extend_schema(
        tags=['Momentum Report'],
    request   = MomentumReportShareSerializer,
    responses = {200: dict})
    def create(self,request):
        try:
            user= request.user
            serializer = MomentumReportShareSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(sender=user)
            report_id = serializer.validated_data["report_id"]
            message = serializer.validated_data["message"]
            if obj:
                receiver_user = obj.receiver
                email_args = {
                'full_name': f"{receiver_user.first_name} {receiver_user.last_name}".strip(),
                'email': receiver_user.username,
                'origin'  : f"{configurations.MOMENTUM_SHARE_URL}{report_id}",
                'app'    : "Momentum Report",
                'message':message
                }
                # Send Email as non blocking thread. Reduces request waiting time.
                t = threading.Thread(target=user_fn.EmailService(email_args,[receiver_user.username]).send_momentum_report_email)
                t.start() 
            return Response(data={"detail": "Successfully Shared "}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)


#tasks under a report id
class ViewReportDatasByIdView(GenericViewSet):
    serializer_class= ReportIdSerializer
    @extend_schema(
        tags=['Momentum Report'],
        request=ReportIdSerializer,
        responses={
            200:dict,
            400:dict,
        }
    )

    def create(self,request):
        #INPUTTING REPORT ID
        sv=ReportIdSerializer(data=request.data)
        sv.is_valid(raise_exception=True)
        report_id=sv.validated_data.get('report_id')

        tasks=utils.dbTaskData(report_id)
        taskurl=utils.get_url_pdf(report_id)
        
        project_id=str(taskurl.report_id.product_id)
        project_name=str(taskurl.report_id.product_id.name)

        created_at=str(taskurl.report_id.created_at)

        report_name=str(taskurl.report_id.report_name)
        #taking base64 code of saved pdf. and removing first two characters as it was not needed
        #it is because we are saving is in string format. so b comes as first character
        base64pdf=str(taskurl.report_pdf[2:])
        file_size=taskurl.report_size
        #removing last character of base 64 , not necessery.
        base64pdf=base64pdf.rstrip(base64pdf[-1])
        report_data = Report.objects.get(id=report_id)
        org_id = None
        if report_data.product_id.organization_data:
            org_id = report_data.product_id.organization_data.id
        final_output={'Completed':tasks[0],'Active':tasks[1],'New':tasks[2],'Projectid':project_id,'ProjectName':project_name,'org_id':org_id,'ReportName':report_name,'created_at':created_at,'updated_at':report_data.updated_at,'filesize':file_size,'Base64Pdf':base64pdf}        
        #to change read status to seen
        status_pdf_read=utils.saveReadStatus(request.user.id,report_id)
        return Response(data={'data':final_output})

class NotificationView(viewsets.ViewSet):
    @extend_schema(
        tags=['Momentum Report'])
    def list(self,request):
        try:
            arguments= utils.task_notifications(request)
            return Response(data={"detail": "Notification fetched","data":arguments}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Momentum Report'],
    request   = TaskNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = TaskNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = TaskNotification.objects.filter(id__in=notif_list,action_status="unseen").update(action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)
        
class TaskReplyCommentsCRUDView(viewsets.ViewSet):
    """
    APIs to create,retrieve,update and delete task comments
    """
    permission_classes  = [permissions.IsSuperUser|permissions.IsOrganizationAdmin|permissions.IsOrganizationUser ,]
    serializer_class    = TaskReplySerializer
    request   = TaskReplySerializer,
    responses = {
            201: dict,
            404: dict,
            409: dict
        }


    def get_queryset(self,task):
        comments = TaskComments.objects.filter(task_id= task)
        
        if comments:
             
            return comments
        else:
            return "NA"
  
    @extend_schema(
    tags=['Momentum Report'],
    request   = TaskReplySerializer,
    responses = {201: dict,
            404: dict,
            409: dict})
    

    def reply_comments(self, request, *args, **kwargs):
        """
        Create task comments
        """
        try:
            serializer = TaskReplySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            
            #For task notificationorganization
            if request.user.is_superuser:
                org_id = ProjectFromWorkzone.objects.filter(id=instance.task_comment.task.reports.product_id.id).values_list('organization_data__id',flat = True).get()
                org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(org_user_list) + list(super_admin_list)

                task_notif = list(map(lambda user: TaskNotification(task=instance.task_comment.task,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                TaskNotification.objects.bulk_create(task_notif)
            else:
                
                organization = user_model.Role.objects.filter(user=request.user).first()
                user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).values_list('user',flat=True)

                super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

                final_user = list(user_list) + list(super_admin_list)
            
                task_notif = list(map(lambda user: TaskNotification(task=instance.task_comment.task,action_user=request.user,action_type="reply",org_user_id=user,reply=instance), final_user))
                TaskNotification.objects.bulk_create(task_notif)
            ProjectFromWorkzone.objects.filter(id=instance.task_comment.task.reports.product_id.id).update(updated_at=datetime.now())
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_409_CONFLICT)
        return Response({"message":"Comments added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
    tags=['Momentum Report'],
    request   = TaskReplyUpdationSerializer,
    parameters=[

      OpenApiParameter(name='comment_id', required=False, type=UUID,location=OpenApiParameter.QUERY),

           ],
    responses = {201: TaskReplyUpdationSerializer})
    
    def update(self, request):
        """
        Update comments
        
        @TODO: Add pagination
        """
        comment_id = request.query_params.get('comment_id')
        querset     = TaskCommentsReply.objects.filter(id=comment_id).first()
        if querset:
            
            serializer  = TaskReplyUpdationSerializer(querset,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"detail": "Comments updated ","data":serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
    tags=['Momentum Report'],
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
        obj     = TaskCommentsReply.objects.filter(id=comment_id)
        if obj:
            obj.delete()
           
            return Response(data={"detail": "Comments Deleted "}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Comment id not found'}, status=status.HTTP_404_NOT_FOUND)


class NotifiMarkAsRead(viewsets.ViewSet):
    
    @extend_schema(
        tags=['Momentum Report'],
    request   = TaskNotifcationStatusSerializer,
    responses = {200: dict})
    def status_change(self,request):
        try:
            user = request.user
            serializer = TaskNotifcationStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            notif_list : list = serializer.validated_data.get('notification_list', None)
            notif = TaskNotification.objects.filter(id__in=notif_list,higlight_status="unseen").update(higlight_status="seen",action_status="seen")
            
            return Response(data={"detail": "Notification status changed"}, status=status.HTTP_200_OK)
        except exceptions.ExistsError as e:
            return Response(data={"detail": e.message}, status=status.HTTP_404_NOT_FOUND)