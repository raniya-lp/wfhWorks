
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
# router.register(r'', views.PatternsCRUDView, basename='projects')
router.register(r'', views.PatternsCRUDApi, basename='projects')

urlpatterns = [
    path('',include(router.urls)),
    path('pattern/<pk>/', views.GetSinglePatternView.as_view(),name='pattern-get'),
    path('font-list', views.GetFontFetchView.as_view(),name='pattern-fontfetch'),
    path('notification', views.NotificationView.as_view({'post':'status_change','get':'list'}),name='notification'),
    path('notification-mark-as-read', views.NotifiMarkAsRead.as_view({'post':'status_change'}),name='notification-mark-as-read'),

    #comments

    path('pattern-comments', views.PatternsCommentsCRUDView.as_view({'post':'create','get':'list','put':'update','delete':'destroy'}),name='pattern-comments'),
    path('reply-comments', views.PatternsReplyCommentsCRUDView.as_view({'post':'reply_comments','put':'update','delete':'destroy'}),name='reply-comments'),
    path('pattern-comment/<pk>', views.SingleComment.as_view(),name='pattern-comment'),
    path('pattern-comment-reply/<pk>', views.SingleCommentReply.as_view(),name='pattern-comment-reply'),
    #Pattern Filter
    path('pattern-filter', views.PatternFilterApi.as_view({'post':'filter'}),name='pattern-filter'),
    #For pattern document share

    path('pattern-document-share', views.DocumentShare.as_view({'post':'create'}),name='pattern-document-share'),

    ]