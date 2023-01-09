import requests
import json
import pandas as pd
from projects.models import Projects
from . models import ProjectFromWorkzone
from users.models import *

def saveProjectToDb():
    projectList='https://logicplum.sharedwork.com/api/projects'
    projectListData=requests.get(projectList,headers ={'Authorization':auth_token('XLZGTfYP-rJnBoiG','b7nWz-RLavkv2j_YUHslRFywfNFAJSwF','client_credentials')}).json()
    reslen=len(projectListData)
    workspace_name=[]
    
    for i in range(1,reslen):
        
        project_name=projectListData[i]['workspaceName']
        
        project_state=projectListData[i]['projectState']
        project_name_cap=project_name.lower()
        if(project_name in workspace_name):
            pass
        else:
            
            workspace_name.append(project_name)
            if ProjectFromWorkzone.objects.filter(name=project_name).exists():
                pass
            else:
                if Organization.objects.filter(name=project_name).exists():
                    organization_found=Organization.objects.get(name=project_name)
                    project_name_save=ProjectFromWorkzone()
                    project_name_save.organization_data=organization_found
                    project_name_save.name=project_name
                    project_name_save.status=project_state
                    project_name_save.save()
                elif Organization.objects.filter(name=project_name_cap).exists():
                    organization_found=Organization.objects.get(name=project_name_cap)
                    project_name_save=ProjectFromWorkzone()
                    project_name_save.organization_data=organization_found
                    project_name_save.name=project_name
                    project_name_save.status=project_state
                    project_name_save.save()
                else:
                    project_name_save=ProjectFromWorkzone()
                    project_name_save.name=project_name
                    project_name_save.status=project_state
                    project_name_save.save()
    
    return workspace_name

def auth_token(client_id,client_secret,grant_type):
    workzone_integration=requests.post('https://logicplum.sharedwork.com/api/token',data = {'client_id':client_id, 'client_secret':client_secret,'grant_type':grant_type})
    result_text=workzone_integration.text

    token_json=json.loads(result_text)
    token=token_json['access_token']

    auth_tok = "Bearer "+token
    return auth_tok


def projectIdFromWorkzone(project_name,client_id,client_secret,grant_type):

    projects='https://logicplum.sharedwork.com/api/projects'
    project_id_found=[]
    projectTask=requests.get(projects,headers ={'Authorization':auth_token(client_id,client_secret,grant_type)}).json()
    reslen=len(projectTask)
    for i in range(1,reslen):
        if(projectTask[i]['workspaceName']==project_name):
            project_id_found.append({'name':projectTask[i]['projectName'],'id':projectTask[i]['projectID']})
    return project_id_found

def projectReportDataFetch(client_id,client_secret,grant_type,project_id):
    completedTask=[{'taskid':'','taskname':'','status':'','workspacename':'','startdate':'','enddate':''}]
    newTask=[{'taskid':'','taskname':'','status':'','workspacename':'','startdate':'','enddate':''}]
    activeTask=[{'taskid':'','taskname':'','status':'','workspacename':'','startdate':'','enddate':''}]
    tasks=[]
    qr_testers=['vandhana mohanan','damian mingle','akhila v','udayalakshmi jk','melvin george']
    # qr_testers=['vandhana mohanan','damian mingle','akhila v','udayalakshmi jk','melvin george','akhila v - bugherd','vandhana mohanan - bugherd','damian mingle - bugherd','melvin george - bugherd','akhila v - bugherd','udayalakshmi jk - bugherd','melvin george - bugherd']
    try:
        
        for x in range(1,500):
            task='https://logicplum.sharedwork.com/api/projects/'+str(project_id)+'/tasks?page='+str(x)+'&limit=100'

            projectTask=requests.get(task,headers ={'Authorization':auth_token(client_id,client_secret,grant_type)}).json()
            reslen=len(projectTask)

            for i in range(1,reslen):
                taskname=" ".join(projectTask[i]['name'].split()).lower()
                if((projectTask[i]['numSubtasks']>0) or (taskname in qr_testers) or (taskname.endswith("bugherd"))):
                    pass
                else:

                    if(projectTask[i]['percentComplete']==100):
                        completedTask.append({'taskid':projectTask[i]['taskID'],'taskname':projectTask[i]['name'],'status':'Completed','workspacename':projectTask[i]['workspaceName'],'startdate':projectTask[i]['startDate'],'enddate':projectTask[i]['endDate']})
                        
                    elif(projectTask[i]['percentComplete']==0):
                        newTask.append({'taskid':projectTask[i]['taskID'],'taskname':projectTask[i]['name'],'status':'New','workspacename':projectTask[i]['workspaceName'],'startdate':projectTask[i]['startDate'],'enddate':projectTask[i]['endDate']})
                    
                    else:
                        activeTask.append({'taskid':projectTask[i]['taskID'],'taskname':projectTask[i]['name'],'status':'Active','workspacename':projectTask[i]['workspaceName'],'startdate':projectTask[i]['startDate'],'enddate':projectTask[i]['endDate']})
        
    except:
        pass
    tasks.append({'completed':completedTask,'active':activeTask,'new':newTask})
    print(tasks)
    return tasks