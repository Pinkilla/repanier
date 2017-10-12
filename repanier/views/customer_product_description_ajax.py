# -*- coding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET

from repanier.const import EMPTY_STRING, PERMANENCE_OPENED, PERMANENCE_SEND
from repanier.models.offeritem import OfferItem
from repanier.tools import permanence_ok_or_404, sint, html_box_content


@require_GET
def customer_product_description_ajax(request):
    if request.is_ajax():
        offer_item_id = sint(request.GET.get('offer_item', 0))
        offer_item = get_object_or_404(OfferItem, id=offer_item_id)
        permanence = offer_item.permanence
        permanence_ok_or_404(permanence)
        if PERMANENCE_OPENED <= permanence.status <= PERMANENCE_SEND:
            offer_item.long_name = offer_item.product.long_name
            result = render_to_string(
                'repanier/cache_part_e.html',
                 {'offer': offer_item, 'MEDIA_URL': settings.MEDIA_URL}
            )
        else:
            result = format_html(
                "{}",
                _("There is no more product's information")
            )
        return HttpResponse(result)
    raise Http404
