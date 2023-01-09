
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views


urlpatterns = [
    path('canvas-type-list/', views.CanvasType.as_view(), name='context'),
    path('canvas-creation/',  views.Canvas.as_view({'post': "create",'get':"list"}),name='CanvasTask'),
    path('canvas-creation/<pk>/', views.Canvas.as_view({'put':"update",'delete':"destroy"}),name='CanvasTask'),
    path('canvas-task-creation/',  views.CanvasTask.as_view({'post': "create"}),name='Task'),
    path('canvas-task-creation/<pk>',  views.CanvasTask.as_view({'put':"update",'get':'singletask','delete':"destroy"}),name='Task'),
    path('canvas-priority/<pk>',  views.PriorityList.as_view({"get":"get_list"}),name='PriorityList'),
    path('canvas-notes/', views.CanvasNotes.as_view({"post":"create"}),name='Answer'),
    path('canvas-notes/<pk>/', views.CanvasNotes.as_view({'put':"update",'delete':"destroy"}),name='Answer'),
    # path('canvas-notes-update/<pk>', views.CanvasNotes.as_view({'put':"update"}),name='Answer'),
    # path('member-creation/',  views.CanvasMembersview.as_view({'post': "create"}),name=' CanvasMembers'),
    path('canvas-deletion/', views.DeleteCanvas.as_view(), name='delete'),
    path('canvas-final-status/<pk>', views.CanvasStatus.as_view(), name='canvasstatus'),
    path('canvas-details/<pk>', views.CanvasDetails.as_view({'get': "list"}), name='details'),
    path('canvas-details-user/<pk>', views.Canvasview.as_view({'get': "list"}), name='details'),
    path('canvas-info/<pk>', views.CanvasInfo.as_view({'get': "list"}), name='details'),
    path('canvas-list/',  views.canvaslist.as_view({'get':"list"}),name='Canvas'),
    path('canvas-notification', views.NotificationView.as_view({'post':'status_change','get':'list'}),name='notification'),
    path('canvas-user-response', views.CanvasUserResponse.as_view({'get': "list"}), name='details'),
    path('canvas-task-creation-complete/<pk>', views.TaskCreationComplete.as_view(),name='task-creation-complete'),
    path('notification-mark-as-read', views.NotifiMarkAsRead.as_view({'post':'status_change'}),name='notification-mark-as-read'),

    #comments
    path('canvas-comments', views.CanvasCommentsCRUDView.as_view({'post':'create','get':'list','put':'update','delete':'destroy'}),name='canvas-comments'),
    path('reply-comments', views.CanvasReplyCommentsCRUDView.as_view({'post':'reply_comments','put':'update','delete':'destroy'}),name='reply-comments'),
    path('canvas-comment/<pk>', views.SingleComment.as_view(),name='canvas-comment'),
    path('canvas-comment-reply/<pk>', views.SingleCommentReply.as_view(),name='canvas-comment-reply'),

    #For canvas document share
    path('canvas-document-share', views.DocumentShare.as_view({'post':'create'}),name='canvas-document-share'),
    
    #Canvas Filter
    path('canvas-filter', views.CanvasFilterApi.as_view({'post':'filter'}),name='canvas-filter')
]