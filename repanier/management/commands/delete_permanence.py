# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

from repanier.models.permanence import Permanence
from repanier.task.task_purchase import admin_delete


class Command(BaseCommand):
    args = '<none>'
    help = 'Recalculate order amount'

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)
        for permanence in Permanence.objects.filter(
            id__in=[1, 2, 3],
            # status__lte=PERMANENCE_SEND
            # id__gte=11,
            # id__lte=16
        ).order_by('permanence_date'):
            print("{}".format(permanence))
            admin_delete(permanence_id=permanence.id)
            Permanence.objects.filter(id=permanence.id).delete()

