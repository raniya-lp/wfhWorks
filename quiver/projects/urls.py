
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'', views.ProjectCRUDView, basename='projects')

urlpatterns = [
    path('',include(router.urls)),
    path('roadmap/<uuid:pk>/', views.RoadMapView.as_view(), name='roadmap'),
    path('roadmap_feature/<pk>/', views.RoadMapFeatureView.as_view(), name='roadmap_feature'),
    path('feature/order/', views.FeatureOrderUpdateView.as_view(), name='feature_order'),
    path('feature/bulk_update/', views.FeatureBulkUpdateView.as_view(), name='feature_bulk_update'),
    path('projects/product_delete/<pk>/', views.ProductDeleteView.as_view(),name='product_delete'),
    path('roadmap',  views.RoadMapList.as_view({'get': 'list'}),name='roadmap_list'),

    #Notification
    path('notification', views.NotificationView.as_view({'post':'status_change','get':'list'}),name='notification'),
    path('notification-mark-as-read', views.NotifiMarkAsRead.as_view({'post':'status_change'}),name='notification-mark-as-read'),
    #Comments

    path('roadmap-comments', views.RoadMapCommentsCRUDView.as_view({'post':'create','get':'list','put':'update','delete':'destroy'}),name='roadmap-comments'),
    path('reply-comments', views.RoadMapReplyCommentsCRUDView.as_view({'post':'reply_comments','put':'update','delete':'destroy'}),name='reply-comments'),
    path('roadmap-comment/<pk>', views.SingleComment.as_view(),name='roadmap-comment'),
    path('roadmap-comment-reply/<pk>', views.SingleCommentReply.as_view(),name='roadmap-comment-reply'),

    #For pattern document share
    path('roadmap-document-share', views.DocumentShare.as_view({'post':'create'}),name='roadmap-document-share'),
    path('roadmap/roadmap-filter', views.RoadmapFilterApi.as_view({'post':'filter'}),name='roadmap-filter'),

    path('roadmap/roadmap-single-get/<pk>/',views.RoadmapSingleGet.as_view(),name='roadmap-single-get')

]