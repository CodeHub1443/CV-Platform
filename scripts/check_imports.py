import sys
sys.path.insert(0, 'E:/dev/CV-Platform/CV-Platform')

from cv_platform.shared.api_core import create_app, Router, get_json_body, configuration_object, json_ok, json_created, json_no_content
from cv_platform.configuration.api import create_configuration_app
from cv_platform.configuration.api._serializers import serialize_project, serialize_deployment
from cv_platform.configuration.api.projects import make_projects_router
from cv_platform.configuration.api.sites import make_sites_router
from cv_platform.configuration.api.camera_configs import make_camera_configs_router
from cv_platform.configuration.api.ai_applications import make_ai_applications_router
from cv_platform.configuration.api.models import make_models_router
from cv_platform.configuration.api.rules import make_rules_router
from cv_platform.configuration.api.scene_configs import make_scene_configs_router
from cv_platform.configuration.api.users import make_users_router
from cv_platform.configuration.api.feature_flags import make_feature_flags_router
from cv_platform.configuration.api.deployments import make_deployments_router

print("All imports OK")
