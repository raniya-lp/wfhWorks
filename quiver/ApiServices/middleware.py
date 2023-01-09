from django.shortcuts import render,redirect
import time
from django.conf import settings
from . import utils
from django.http import JsonResponse
import traceback
from . functions import *


def apidata_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        if request.get_full_path() != '/api/v1/apiservices/ApiSave':
            t1 = time.time()

            if response.streaming:
                error_get=request.get_full_path()
                msg=error_get
            else:
                error_get=response.content
                error_msg=error_get.decode('UTF-8')
                msg=error_msg.split('\n')
                msg=str(msg[:4])
            
            ip_address=FindIpAddress()
            print('\n\nipaddresss: ',ip_address)
            t2 = time.time()

            totaltime=(t2 - t1)
            status_code=response.status_code
            path_found=request.get_full_path()
            
            try:
                result=utils.saveApiListDb(path_found,'LogicPlum','Alignment Chain',request,totaltime,status_code,msg,ip_address[1],ip_address[0])
            except Exception as e:
                print("Middleware exception:",e)
                pass
        return response
    return middleware
