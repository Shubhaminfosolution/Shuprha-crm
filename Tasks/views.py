from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from django.shortcuts import render

from Users.permissions import IsAdmin
from .models import Task
from .serializers import TaskSerializer
from Users.models import User
from django.utils import timezone


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Client users never see tasks
        if user.role == "client":
            return Task.objects.none()

        qs = Task.objects.select_related("assigned_to", "created_by")

        # Auto-mark overdue tasks on every fetch
        now = timezone.now()
        qs.filter(
            status="pending",
            due_date__lt=now
        ).update(status="overdue")

        # Admin can see all or filter by assigned_to
        if user.role == "admin":
            assigned_to = self.request.query_params.get("assigned_to")
            if assigned_to:
                qs = qs.filter(assigned_to_id=assigned_to)
            return qs

        # Manager/Sales — only own tasks
        return qs.filter(assigned_to=user)

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == "client":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Client users cannot create tasks.")

        task = serializer.save(created_by=user)


        reminder_time = task.due_date - timezone.timedelta(hours=1)
        if reminder_time > timezone.now():
            # Schedule via Celery if worker available, else skip
            try:
                from .tasks import send_task_reminder
                send_task_reminder.apply_async(
                    args=[task.id],
                    eta=reminder_time
                )
            except Exception:
                pass  # silently skip if no worker

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        # If marking complete — record completed_at
        new_status = serializer.validated_data.get("status")
        if new_status == "completed" and instance.status != "completed":
            serializer.save(completed_at=timezone.now())
        else:
            serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        # Only admin or creator can delete
        if user.role != "admin" and instance.created_by != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the creator or admin can delete this task.")
        instance.delete()

    @action(detail=False, methods=["get"])
    def my_tasks(self, request):
        """Quick endpoint — current user's pending + overdue tasks sorted by due date."""
        user = request.user
        tasks = Task.objects.filter(
            assigned_to=user,
            status__in=["pending", "overdue"]
        ).order_by("due_date")
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def productivity_report(request):
    """
    Productivity report endpoint.
    Admin sees full team. Others see only themselves.
    Measures:
      - Completion rate: completed / total assigned
      - On-time rate: completed on time / total completed
    """
    user = request.user

    if user.role == "client":
        return Response({"detail": "Not available for client users."}, status=403)

    if user.role == "admin":
        # Full team report
        team_members = User.objects.filter(
            role__in=["admin", "manager", "sales"],
            is_active=True,
            is_deleted=False
        )
    else:
        team_members = User.objects.filter(id=user.id)

    report = []

    for member in team_members:
        tasks = Task.objects.filter(assigned_to=member)
        total = tasks.count()
        completed = tasks.filter(status="completed").count()
        on_time = sum(1 for t in tasks.filter(status="completed") if t.completed_on_time)
        overdue = tasks.filter(status="overdue").count()
        pending = tasks.filter(status="pending").count()

        completion_rate = round((completed / total * 100), 1) if total else 0
        on_time_rate = round((on_time / completed * 100), 1) if completed else 0

        # Productivity score — weighted average of both rates
        productivity_score = round((completion_rate * 0.5) + (on_time_rate * 0.5), 1)

        report.append({
            "user_id": member.id,
            "name": member.full_name,
            "email": member.email,
            "total_tasks": total,
            "completed": completed,
            "on_time": on_time,
            "overdue": overdue,
            "pending": pending,
            "completion_rate": completion_rate,
            "on_time_rate": on_time_rate,
            "productivity_score": productivity_score,
        })

    # Sort by productivity score descending — leaderboard order
    report.sort(key=lambda x: x["productivity_score"], reverse=True)

    return Response({
        "report": report,
        "generated_at": timezone.now().isoformat(),
    })


# UI page view
def tasks_page(request):
    return render(request, "tasks.html")