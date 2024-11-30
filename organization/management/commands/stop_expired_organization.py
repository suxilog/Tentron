import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from organization.models import Organization

logger = logging.getLogger("tentron")


class Command(BaseCommand):
    help = "Stop expired organization, set active_status to False"

    def stop_expired_organization(self):
        stopped_count = 0
        for organization in Organization.objects.filter(active_status=True):
            if organization.expiry_date and organization.expiry_date < timezone.now():
                organization.active_status = False
                organization.save()
                stopped_count += 1
                print("Organization ID: {} is EXPIRED".format(organization.id))
                logger.info("Organization ID: {} is EXPIRED".format(organization.id))
        print(
            "Stop expired organization done. All organization checked. {} organization stopped.".format(
                stopped_count
            )
        )
        logger.info(
            "Stop expired organization done. All organization checked. {} organization stopped.".format(
                stopped_count
            )
        )

    def handle(self, *args, **options):
        self.stop_expired_organization()
