import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from courses.models import Course, UserCourseEnrollment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates course badges based on various criteria"

    def handle(self, *args, **options):
        self.stdout.write("Starting to update course badges...")

        # Get the current date
        now = timezone.now()

        # Reset all badges to none first
        Course.objects.all().update(badge="none")

        # Mark courses as 'new' if they were created in the last 30 days
        thirty_days_ago = now - timedelta(days=30)
        new_courses = Course.objects.filter(created_at__gte=thirty_days_ago)
        new_courses_count = new_courses.update(badge="new")
        self.stdout.write(f"Updated {new_courses_count} courses as NEW")

        # Mark top 10 courses with most enrollments as 'popular'
        popular_courses = Course.objects.annotate(
            enrollment_count=Count("enrollments")
        ).order_by("-enrollment_count")[:10]
        popular_count = 0
        for course in popular_courses:
            if course.badge == "none":  # Only update if no other badge
                course.badge = "popular"
                course.save()
                popular_count += 1
        self.stdout.write(f"Updated {popular_count} courses as POPULAR")

        # Mark courses with increased enrollments in the last 7 days as 'trending'
        seven_days_ago = now - timedelta(days=7)
        trending_courses = Course.objects.annotate(
            recent_enrollments=Count(
                "enrollments", filter=Q(enrollments__date_enrolled__gte=seven_days_ago)
            )
        ).filter(
            recent_enrollments__gte=5
        )  # At least 5 enrollments in the last week
        trending_count = 0
        for course in trending_courses:
            if course.badge == "none":  # Only update if no other badge
                course.badge = "trending"
                course.save()
                trending_count += 1
        self.stdout.write(f"Updated {trending_count} courses as TRENDING")

        # Mark top 5 courses with high completion rates as 'bestseller'
        bestsellers = (
            Course.objects.annotate(
                completed_count=Count(
                    "enrollments", filter=Q(enrollments__is_completed=True)
                )
            )
            .filter(completed_count__gte=10)
            .order_by("-completed_count")[:5]
        )  # At least 10 completions
        bestseller_count = 0
        for course in bestsellers:
            if course.badge in [
                "none",
                "popular",
            ]:  # Bestseller takes precedence over popular
                course.badge = "bestseller"
                course.save()
                bestseller_count += 1
        self.stdout.write(f"Updated {bestseller_count} courses as BESTSELLER")

        # The 'featured' badge should be set manually by admins

        self.stdout.write(self.style.SUCCESS("Successfully updated course badges"))
