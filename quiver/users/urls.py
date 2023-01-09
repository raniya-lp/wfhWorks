from rest_framework_simplejwt import views as jwt_views
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
# router.register(r'organization', views.OrganisationCRUDView, basename='organization')
router.register(r'', views.UserView, basename='organization')

urlpatterns = [
    path('',include(router.urls)),
    # path('login', jwt_views.TokenObtainPairView.as_view(), name='login'),
    path('login', views.Login.as_view(), name='login'),
    path('refresh', jwt_views.TokenRefreshView.as_view(), name='refresh'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('user/profile/info',views.ProfileInfoView.as_view(), name='user-profile-info'),
    path('user/reset-password', views.ResetPasswordView.as_view(),name='reset-password'),
    path('user/reset-password/confirm',views.ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('user/change-password', views.ChangePasswordView.as_view(),name='change-password'),
    path('user/activity', views.ActivityView.as_view({'get':'list'}),name='activity'),
    path('user/notification', views.NotificationView.as_view(),name='notifications'),
    path('user/feedback', views.UserFeedbackView.as_view(),name='feedback'),
    path('user/feedback/<pk>/', views.UserFeedbackActionView.as_view(),name='feedback-action'),
    path('user/admin-details-update/<pk>/', views.AdminListUpdate.as_view(),name='admin-details-update'),
    path('users/app-access-list',views.UsersAppAccessList.as_view(), name='user-access-list'),
    path('user/admin-list', views.ListAdminView.as_view(),name='admin-list'),
    path('user/update-user-detail/<pk>/', views.UpdateUserProfile.as_view(),name='update-user-detail'),
    path('user/apps',views.AppList.as_view(),name='app-list'),
    path('user/organizations',views.organizations.as_view(),name='organizations'),
    path('user/organization-logo/<pk>',views.OrganizationLogoView.as_view(),name='organization-logo'),
    path('user/app-request/<pk>/',views.AppRequest.as_view(),name='app-request'),
    path('user/activate',views.Activate.as_view(),name='activate'),
    path('app/users',views.AppWiseUserView.as_view({'get':'list'}),name='app-wise-users'),
    path('user/organization-user',views.OrganizationUser.as_view(),name='organisation-user'),
    path('user/organization-list',views.OrganizationProjectView.as_view(),name='organization-list'),
    path('user/invitation-sent',views.Invitation_Sent.as_view(),name='invitation-sent'),
    path('user/replace-password',views.ReplacePassword.as_view(),name='replace-password'),
    path('app/organization-wise-users',views.AppWiseOrgUserView.as_view({'get':'list'}),name='app-wise-org-users')



]
