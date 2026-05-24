from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TaskViewSet, productivity_report, tasks_page

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")

urlpatterns = router.urls + [
    path("tasks/productivity/", productivity_report, name="productivity_report"),
    path("tasks-ui/", tasks_page, name="tasks_page"),
]