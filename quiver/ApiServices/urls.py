from django.urls import path,include
from . import views

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'', views.projectApiListView, basename='apiservices')
urlpatterns=[
    path('',include(router.urls)),
    path('chartByUrl/<url_id>',views.APiByUrlView.as_view({"get":"viewurl"}),name='chartByUrl'),
    path('ApiLists',views.UrlIdView.as_view({"get":"viewurl"}),name='ApiLists'),
    # path('ApiProjectList',views.projectApiListView.as_view(),name='ApiProjectList'),
    path('ApiCallListWithDetails',views.ApiUrlDetails.as_view({"get":"viewdata"}),name='ApiCallListWithDetails'),   
    path('ApiProjectListById',views.projectApiListByIdView.as_view({"post":"viewdatabyid"}),name='ApiProjectListById'),
    path('ApiListByUserId',views.ApiUrlDetailsByUser.as_view({"post":"viewdatabyuser"}),name='ApiListByUserId'),
    path('UrlIdBasedApiList',views.ApiUrlDetailsByUrl.as_view({"post":"viewdatabyUrl"}),name='UrlIdBasedApiList'),   
    path('ApiDataViewBasedOnUrlId',views.ApiUrlDetailsByDate.as_view({"post":"viewdatabyUrlDate"}),name='ApiDataViewBasedOnUrlId'),
    path('AllApiListDetailsWithDate',views.AllDetailsByDate.as_view({"post":"viewdatabyUrlDate"}),name='AllApiListDetailsWithDate'),
    path('AllApiListDetailsWithHour',views.DetailsByHour.as_view({"post":"viewdatabyUrlHour"}),name='AllApiListDetailsWithHour'),
    path('UrlIdDetailsWithHour',views.ApiUrlDetailsByHour.as_view({"post":"viewdatabyUrlHour"}),name='UrlIdDetailsWithHour'),
    path('AllApiListDetailsWithHDaysCount',views.DetailsByDays.as_view({"post":"viewdatabyUrlHour"}),name='AllApiListDetailsWithHDaysCount'),
    path('UrlIdDetailsWithHDaysCount',views.ApiUrlDetailsByDays.as_view({"post":"viewdatabyUrlHour"}),name='UrlIdDetailsWithHDaysCount'),
    path('HourChart',views.HourChartView.as_view({"post":"viewdatabyUrlHour"}),name='HourChart'),
    path('DayChart',views.DayChartView.as_view({"post":"viewdatabyUrlHour"}),name='DayChart'),
    path('DateChart',views.DateChartView.as_view({"post":"viewdatabyUrlDate"}),name='DateChart'),
    path('Apinotification', views.ApiNotificationView.as_view({'post':'status_change','get':'viewdata'}),name='Apinotification'),
    path('api-notification-mark-as-read', views.ApiNotificationStatusChange.as_view({'post':'status_change'}),name='api-notification-mark-as-read'),
    path('ApiSave', views.ApiSave.as_view(),name='apisave'),

]