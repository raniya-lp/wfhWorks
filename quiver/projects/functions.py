from . import models
from users import models as user_models
from generics import exceptions
from users import models as user_model
from projects import models as prg_model
from . import serializers
from patterns import models as pattern_model
from context import models as context_model
from blueprint import models as blueprint_model
from momentum_report import models as momentum_model

def is_project_exists(name: str):
    return models.Projects.objects.filter(name=name).first()

def is_roadmap_exists(name: str):
    return models.RoadMaps.objects.filter(name=name).first()
def is_roadmap_feature_exists(name: str,roadmap):
    return models.RoadMapFeatures.objects.filter(name=name,roadmap=roadmap).first()


def create_project(creator,request, name: str, status: str, org_id=None) -> bool:

    # site = is_project_exists(name=name)
    # if site is not None:
    #     raise exceptions.ExistsError("The Project is already being used with the same name.")
    if org_id is None:
        project = models.Projects.objects.create(created_by=creator, name=name)
    else:
        organization = user_models.Organization.objects.get(id=org_id)
        project = models.Projects.objects.create(created_by=creator, name=name)
        project_org_mapping = models.ProjectsOrganizationMapping.objects.create(created_by=creator, project=project,organization=organization)


        #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).exclude(role="user").values_list('user',flat=True)
        print(org_user_list)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)

        #roadmap
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)

        #Patterns
        
        pattern_notif = list(map(lambda user: pattern_model.PatternNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        pattern_model.PatternNotification.objects.bulk_create(pattern_notif)

        #Canvas
        
        canvas_notif = list(map(lambda user: context_model.CanvasNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        context_model.CanvasNotification.objects.bulk_create(canvas_notif)


        #blueprint
        
        bluprint_notif = list(map(lambda user: blueprint_model.BluePrintNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        blueprint_model.BluePrintNotification.objects.bulk_create(bluprint_notif)

        #momentum-report
        
        momentum_notif = list(map(lambda user: momentum_model.TaskNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        momentum_model.TaskNotification.objects.bulk_create(momentum_notif)

       
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).exclude(role="user").values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
        
        #roadmap
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)

        #Patterns
        
        pattern_notif = list(map(lambda user: pattern_model.PatternNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        pattern_model.PatternNotification.objects.bulk_create(pattern_notif)

        #Canvas
        
        canvas_notif = list(map(lambda user: context_model.CanvasNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        context_model.CanvasNotification.objects.bulk_create(canvas_notif)


        #blueprint
        
        bluprint_notif = list(map(lambda user: blueprint_model.BluePrintNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        blueprint_model.BluePrintNotification.objects.bulk_create(bluprint_notif)

        #momentum-report
        
        momentum_notif = list(map(lambda user: momentum_model.TaskNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        momentum_model.TaskNotification.objects.bulk_create(momentum_notif)

        
    return project
def create_roadmap(creator, name: str, description: str, project, collaborators: str,request) -> bool:
    
    #  roadmap = is_roadmap_exists(name=name)
    # if roadmap is not None:
    #     raise exceptions.ExistsError("The RoadMap is already being used with the same name.")
  

    roadmap = models.RoadMaps.objects.create(created_by=creator, name=name, description=description, project=project)

    # users = user_models.User.objects.filter(id__in=[k['user'] for k in collaborators])
    # Bulk Create Collaborators
    usr_lst = [] 
    if collaborators:
        bulk_collaborator = [
            models.Collaborator(roadmap=roadmap, user=user_models.User.objects.get(id=i['user']),write=i['write'])
            for i in collaborators
        ]
        colb_data = models.Collaborator.objects.bulk_create(bulk_collaborator)

               
        list(map(lambda user: usr_lst.append(user.user.id), colb_data))

    #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

        # print("org_user_list",org_user_list)
        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(usr_lst) + list(org_user_list) + list(super_admin_list)

        final_user = [*set(final_user)]
        # print("final",final_user)
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="create",org_user_id=user),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(usr_lst) + list(user_list) + list(super_admin_list)

        final_user = [*set(final_user)]

        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="create",org_user_id=user), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)

    return roadmap
def create_roadmap_features(creator, name: str, roadmap, reach: float, impact: float, confidence: float, effort: float,request,description,image) -> bool:
    
    roadmap_feature = is_roadmap_feature_exists(name=name,roadmap=roadmap)
    if roadmap_feature is not None:
        raise exceptions.ExistsError("The RoadMapFeature is already being used with the same name.")

    feature = models.RoadMapFeatures.objects.create(created_by=creator, name=name, roadmap=roadmap, reach=reach, impact=impact, confidence=confidence, effort=effort,description=description,image=image)

    rice_calculation(feature)
    colb_data = models.Collaborator.objects.filter(roadmap=roadmap)
    usr_lst = []        
    list(map(lambda user: usr_lst.append(user.user.id), colb_data))
    #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(usr_lst) + list(org_user_list) + list(super_admin_list)

        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="feature_create",org_user_id=user,feature=feature),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(usr_lst) + list(user_list) + list(super_admin_list)

        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="feature_create",org_user_id=user,feature=feature), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)

    return feature
def update_feature_order(order,feature):
    feature.order = order
    feature.save()

def bulk_update_feature(data, feature):
    feature.name=data['name']
    feature.confidence=data['confidence']
    feature.effort=data['effort']
    feature.impact=data['impact']
    feature.order=data['order']
    feature.save()
    


def roadmap_update_notification(roadmap,request):

    colb_data = models.Collaborator.objects.filter(roadmap=roadmap)
    usr_lst = []        
    list(map(lambda user: usr_lst.append(user.user.id), colb_data))
    #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(usr_lst) + list(org_user_list) + list(super_admin_list)
        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="update",org_user_id=user),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(usr_lst) + list(user_list) + list(super_admin_list)
        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="update",org_user_id=user), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)


def feature_update_notification(roadmap,request,feature):
    colb_data = models.Collaborator.objects.filter(roadmap=roadmap)
    usr_lst = []        
    list(map(lambda user: usr_lst.append(user.user.id), colb_data))
    #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=roadmap.project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id,role="admin").exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user =list(usr_lst) + list(org_user_list) + list(super_admin_list)
        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="feature_update",org_user_id=user,feature=feature),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin]).exclude(user=request.user.id).values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(usr_lst) + list(user_list) + list(super_admin_list)
        final_user = [*set(final_user)]
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(roadmap=roadmap,action_user=request.user,action_type="feature_update",org_user_id=user,feature=feature), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)


def product_update_notif(project,request):
     #For roadmap notificationorganization
    if request.user.is_superuser:
        org_id = prg_model.ProjectsOrganizationMapping.objects.filter(project=project).values_list('organization',flat = True).get()
        org_user_list = user_model.Role.objects.filter(organization_id=org_id).exclude(user=request.user.id).exclude(role="user").values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).exclude(id=request.user.id).values_list('id',flat=True)

        final_user = list(org_user_list) + list(super_admin_list)
        #roadmap
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user),final_user ))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)
        #pattern
        pattern_notif = list(map(lambda user: pattern_model.PatternNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user),final_user ))
        pattern_model.PatternNotification.objects.bulk_create(pattern_notif)

        #Canvas
        
        canvas_notif = list(map(lambda user: context_model.CanvasNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        context_model.CanvasNotification.objects.bulk_create(canvas_notif)


        #blueprint
        
        bluprint_notif = list(map(lambda user: blueprint_model.BluePrintNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        blueprint_model.BluePrintNotification.objects.bulk_create(bluprint_notif)

        #momentum-report
        
        momentum_notif = list(map(lambda user: momentum_model.TaskNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user),final_user ))

        
        momentum_model.TaskNotification.objects.bulk_create(momentum_notif)
    else:
        
        organization = user_model.Role.objects.filter(user=request.user).first()
        user_list = user_model.Role.objects.filter(organization=organization.organization,role__in=[user_model.Role.RoleName.admin,user_model.Role.RoleName.user]).exclude(user=request.user.id).exclude(role="user").values_list('user',flat=True)

        super_admin_list = user_model.User.objects.filter(is_superuser=True).values_list('id',flat=True)
        
        final_user = list(user_list) + list(super_admin_list)
       
        roadmap_notif = list(map(lambda user: models.RoadMapNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user), final_user))
        models.RoadMapNotification.objects.bulk_create(roadmap_notif)


        #pattern
        pattern_notif = list(map(lambda user: pattern_model.PatternNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user),final_user ))
        pattern_model.PatternNotification.objects.bulk_create(pattern_notif)

        #Canvas
        
        canvas_notif = list(map(lambda user: context_model.CanvasNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        context_model.CanvasNotification.objects.bulk_create(canvas_notif)


        #blueprint
        
        bluprint_notif = list(map(lambda user: blueprint_model.BluePrintNotification(product=project,action_user=request.user,action_type="product_create",org_user_id=user),final_user ))

        
        blueprint_model.BluePrintNotification.objects.bulk_create(bluprint_notif)

        #momentum-report
        
        momentum_notif = list(map(lambda user: momentum_model.TaskNotification(product=project,action_user=request.user,action_type="product_update",org_user_id=user),final_user ))

        
        momentum_model.TaskNotification.objects.bulk_create(momentum_notif)

def rice_calculation(feature):
    features_detailes = models.RoadMapFeatures.objects.filter(roadmap=feature.roadmap)
    feature_count = features_detailes.count()
    

    if feature_count <= 3:
        r = feature.reach
        i = feature.impact
        c = feature.confidence
        e = feature.effort
        
        a = (r*i*c)
        rs = (a)/min(e,(a))
        feature.score=rs
        
        # print("rs_",rs)
        # rs_val = features_detailes.values_list('score',flat=True)
        
        rescale_data = round(min(rs,1000)/10) 
        feature.rice_score=rescale_data
        feature.save()
    else:
          r = feature.reach
          i = feature.impact
          c = feature.confidence
          e = feature.effort
        
          a = (r*i*c)
          rs = (a)/min(e,(a))
          feature.score=rs
          feature.save()
          score = features_detailes.values_list('score',flat=True)
          min_score =min(score)
          max_score =max(score)
          f=models.RoadMapFeatures.objects.filter(roadmap=feature.roadmap)

        #   l2 = list(map(lambda v: (v.rise_score = (v.score - min_score)), f))
          for v in f:
            v.rice_score =round( ((v.score - min_score)*100)/(max_score-min_score))
            v.save()




