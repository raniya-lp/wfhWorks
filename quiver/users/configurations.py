ORGANIZATION_ADMIN: str = "admin"
ORGANIZATION_USER: str = "user"

CHANGE_PASSWORD_BROWSER_URL: str = "#/reset-password"
ALLOWED_RANDOM_CHARS: str = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

NOTIFICATION_DICT = {"Pattern Library":"PatternNotification","Service Blueprint":"BluePrintNotification","Context":"CanvasNotification","Roadmap Live":"RoadMapNotification","Momentum Report":"TaskNotification"}
APP_DICT = {"Pattern Library":"patterns","Service Blueprint":"blueprint","Context":"context","Roadmap Live":"projects","Momentum Report":"momentum_report"}

PATTERN_SHARE_URL = 'http://alignmentchain-dev.logicplum.com/?appName=pattern_library&listItemId='
MOMENTUM_SHARE_URL = 'http://alignmentchain-dev.logicplum.com/?appName=momentum_report&listItemId='
BLUEPRINT_SHARE_URL = 'http://alignmentchain-dev.logicplum.com/?appName=service_blueprint&listItemId='
ROADMAP_SHARE_URL = 'http://alignmentchain-dev.logicplum.com/?appName=roadmap&listItemId='

CONTEXT_SHARE_URL = 'http://alignmentchain-dev.logicplum.com/?appName=context&listItemId='

USER_ACTIONS = {
    'GET': {
        'user-profile-info': {
            'description': "User Profile Information."
        },
        'organization-list': {
            'description': "Organization List."
        },
        'organization-options': {
            'description': "list roles"
        },
        'users-list': {
            'description': "Users List"
        },
        'projects-list': {
            'description': "Projects List."
        },
        'roadmap': {
            'description': "RoadMap List."
        },
        'roadmap_feature': {
            'description': "RoadMapFeature List."
        },
        'feedback': {
            'description': "feedback List."
        },
        'feedback-action': {
            'description': "feedback details List."
        },
        'notifications': {
            'description': "notifications details List."
        },
        'admin-list':{
            'description': "List of organisation admin and super admin."
        },
        'notification': {
            'description': "notification patter."
        },
        'pattern-comments': {
            'description': "pattern-comments created."
        },
        'pattern-comment': {
            'description': "pattern-comment created."
        },
        'pattern-comment-reply': {
            'description': "pattern-comment created."
        },
        'canvas-comments': {
            'description': "canvas-comments created."
        },
        'canvas-comment': {
            'description': "canvas-comment created."
        },
        'canvas-comment-reply': {
            'description': "canvas-comment created."
        },
        'blueprint-comments': {
            'description': "blueprint-comments created."
        },
        'blueprint-comment': {
            'description': "blueprint-comment created."
        },
        'blueprint-comment-reply': {
            'description': "blueprint-comment created."
        },
        'app-wise-users': {
            'description': "app-wise-users"
        },
        'organization-logo': {
            'description': "organization-logo get"
        },'roadmap-comments': {
            'description': "roadmap-comments created."
        },
        'roadmap-comment': {
            'description': "roadmap-comment created."
        },
        'roadmap-comment-reply': {
            'description': "roadmap-comment created."
        },
        'organization-list': {
            'description': "organization-list."
        },
        

    },
    'POST': {
        'login': {
            'description': "User logged in to Roadmap.",
        },
        'refresh': {
            'description': "User logged in to Roadmap."
        },
        'logout': {
            'description': "User logout Successfully."
        },
        'reset-password': {
            'description': "Reset Password."
        },
        'reset-password-confirm': {
            'description': "Confirm Reset Password."
        },
        'change-password': {
            'description': "Change Password Successfully."
        },
        'users-list': {
            'description': "Users Created."
        },
        'organization-list': {
            'description': "Organization Created Successfully."
        },
        'projects-list': {
            'description': "Project Created."
        },
        'roadmap': {
            'description': "RoadMap Created."
        },
        'roadmap_feature': {
            'description': "RoadMapFeature Created."
        },
        'feature_order': {
            'description': "RoadMapFeature Order updated."
        },
        'feedback': {
            'description': "feedback created."
        },
        'pattern-comments': {
            'description': "pattern-comments created."
        },
        'pattern-comment': {
            'description': "pattern-comments single."
        },
        'reply-comments': {
            'description': "reply-comments created."
        },
        'pattern-filter': {
            'description': "pattern-filter."
        },
        'pattern-document-share': {
            'description': "pattern-document-share."
        },
        'canvas-comments': {
            'description': "canvas-comments created."
        },
        'canvas-comment': {
            'description': "canvas-comment created."
        },
        'canvas-comment-reply': {
            'description': "canvas-comment created."
        },
        'canvas-document-share': {
            'description': "canvas-document-share."
        },
        'blueprint-document-share': {
            'description': "blueprint-document-share."
        },
        'roadmap-document-share': {
            'description': "roadmap-document-share."
        },
        'notifications': {
            'description': "notifications details List."
        },
        'blueprint-comments': {
            'description': "blueprint-comments created."
        },
        'blueprint-comment': {
            'description': "blueprint-comment created."
        },
        'blueprint-comment-reply': {
            'description': "blueprint-comment created."
        },
        'notification-mark-as-read': {
            'description': "notification-mark-as-read."
        },
        'roadmap-comments': {
            'description': "roadmap-comments created."
        },
        'roadmap-comment': {
            'description': "roadmap-comment created."
        },
        'roadmap-comment-reply': {
            'description': "roadmap-comment created."
        },
        'organization-list': {
            'description': "organization-list."
        },


    },
    'PUT': {
        'organization-detail': {
            'description': "Updated the Organization detail."
        },
        'users-detail': {
            'description': "Updated the users detail."
        },
        'roadmap': {
            'description': "Updated the Roadmap."
        },
        'roadmap_feature': {
            'description': "Updated the Roadmap Feature."
        },
        'projects-detail': {
            'description': "Updated the project detail."
        },
        'feature_bulk_update': {
            'description': "Updated the RoadmapFeature bulk."
        },
        'pattern-comments': {
            'description': "pattern-comments created."
        },
        'reply-comments': {
            'description': "reply-comments created."
        },
        'canvas-comments': {
            'description': "canvas-comments created."
        },
        'blueprint-comments': {
            'description': "canvas-comments created."
        },
        'reply-comments': {
            'description': "reply-comments created."
        },
        'roadmap-comments': {
            'description': "roadmap-comments created."
        },
        'roadmap-comment': {
            'description': "roadmap-comment created."
        },
        'roadmap-comment-reply': {
            'description': "roadmap-comment created."
        },
    },
    'DELETE': {
        'organization-detail': {
            'description': "Deleted the Organization."
        },
        'users-detail': {
            'description': "Deleted the users."
        },
        'roadmap': {
            'description': "Deleted the Roadmap."
        },
        'roadmap_feature': {
            'description': "Deleted the Roadmap Feature."
        },
        'feedback-action': {
            'description': "Deleted feedback."
        },
        'projects-detail': {
            'description': "Deleted the project."
        },
        'pattern-comments': {
            'description': "pattern-comments created."
        },
        'reply-comments': {
            'description': "reply-comments created."
        },
        'canvas-comments': {
            'description': "canvas-comments created."
        },
        'blueprint-comments': {
            'description': "canvas-comments created."
        },
        'reply-comments': {
            'description': "reply-comments created."
        },
        'roadmap-comments': {
            'description': "roadmap-comments created."
        },
        'roadmap-comment': {
            'description': "roadmap-comment created."
        },
        'roadmap-comment-reply': {
            'description': "roadmap-comment created."
        },
    },
}
