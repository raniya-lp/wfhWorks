from django.urls import path
from . import views

urlpatterns=[
    
    path('dbPojectNameSave',views.saveProjectToDbView.as_view({"post":"getlist"}),name='dbPojectNameSave'),   
    path('workzone_projectListFromDb/',views.ProjectView.as_view({"get":"getlist"}),name='workzone_projectListFromDb'),
    path('GetReportIds/',views.ReportIdView.as_view({"get":"getlist"}),name='GetReportIds'),
    path('CreateReportCustomized/',views.GenerateReportCustomized.as_view({"post":"create"}),name='CreateReportCustomized'),
    path('DeleteReportById/',views.DeleteReportByIdView.as_view({"post":"create"}),name='DeleteReportById'), 
    path('report-list/', views.ReportListView.as_view(), name='report'),
    path('task-list/', views.TaskListView.as_view(), name='task'),
    path('DeleteReportById/',views.DeleteReportByIdView.as_view({"post":"create"}),name='DeleteReportById'),
    path('task-comments', views.TasksCommentsCRUDView.as_view({'post':'create','get':'list','put':'update','delete':'destroy'}),name='task-comments'),
    path('ScheduleTaskApi/',views.SchedulingApiTesting.as_view({"post":"getlist"}), name='ScheduleTaskApi'),
    path('WorkspaceLogoUpload/',views.ProjectLogoUploadView.as_view({"post":"create"}),name='WorkspaceLogoUpload'),
    path('momentum-report-share', views.ReportDocmentShare.as_view({'post':'create'}),name='momentum-report-share'),
    path('projectById/',views.ProjectByIdView.as_view({'post':'create'}),name='projectById'),
    path('ReportData/',views.ViewReportDatasByIdView.as_view({'post':'create'}),name='ReportData'),
    path('notification', views.NotificationView.as_view({'post':'status_change','get':'list'}),name='notification'),
    path('reply-comments', views.TaskReplyCommentsCRUDView.as_view({'post':'reply_comments','put':'update','delete':'destroy'}),name='reply-comments'),
    path('notification-mark-as-read', views.NotifiMarkAsRead.as_view({'post':'status_change'}),name='notification-mark-as-read'),
]