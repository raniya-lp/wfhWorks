from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'', views.BlueprintDataView, basename='blueprint')

urlpatterns = [
    path('',include(router.urls)),
    path('sections/<pk>', views.GetSingleSectionView.as_view(),name='section-get'),
    path('notification', views.NotificationView.as_view({"get":"list","post":"status_change"}),name='notification'),
    path('notification-mark-as-read', views.NotifiMarkAsRead.as_view({'post':'status_change'}),name='notification-mark-as-read'),

    #comments

    path('blueprint-comments', views.BluePrintCommentsCRUDView.as_view({'post':'create','get':'list','put':'update','delete':'destroy'}),name='blueprint-comments'),
    path('reply-comments', views.BluePrintReplyCommentsCRUDView.as_view({'post':'reply_comments','put':'update','delete':'destroy'}),name='reply-comments'),
    path('blueprint-comment/<pk>', views.SingleComment.as_view(),name='blueprint-comment'),
    path('blueprint-comment-reply/<pk>', views.SingleCommentReply.as_view(),name='blueprint-comment-reply'),

    #For blueprint document share

    path('blueprint-document-share', views.DocumentShare.as_view({'post':'create'}),name='blueprint-document-share'),

]
