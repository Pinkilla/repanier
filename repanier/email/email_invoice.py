from django.template import Template, Context as TemplateContext
from repanier.email.email import RepanierEmail
from repanier.models.customer import Customer
from repanier.models.invoice import CustomerInvoice
from repanier.models.permanence import Permanence
from repanier.models.producer import Producer
from repanier.models.purchase import Purchase
from repanier.models.staff import Staff
from repanier.tools import *


def send_invoice(permanence_id):
    from repanier.apps import (
        REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_PRODUCER,
        REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_CUSTOMER,
        REPANIER_SETTINGS_CONFIG,
    )

    permanence = Permanence.objects.get(id=permanence_id)
    config = REPANIER_SETTINGS_CONFIG

    invoice_responsible = Staff.get_or_create_invoice_responsible()

    if REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_PRODUCER:
        # To the producer we speak of "payment".
        # This is the detail of the payment to the producer, i.e. received products
        for producer in Producer.objects.filter(permanence_id=permanence.id):
            to_email = []
            if producer.email:
                to_email.append(producer.email)
            if producer.email2:
                to_email.append(producer.email2)
            if producer.email3:
                to_email.append(producer.email3)
            if to_email:
                # to_email = list(set(to_email + invoice_responsible["to_email"]))
                long_profile_name = (
                    producer.long_profile_name
                    if producer.long_profile_name is not None
                    else producer.short_profile_name
                )
                if Purchase.objects.filter(
                    permanence_id=permanence.id, producer_id=producer.id
                ).exists():
                    invoice_producer_mail = config.invoice_producer_mail_v2
                    invoice_producer_mail_subject = "{} - {}".format(
                        settings.REPANIER_SETTINGS_GROUP_NAME, permanence
                    )

                    template = Template(invoice_producer_mail)
                    context = TemplateContext(
                        {
                            "name": long_profile_name,
                            "long_profile_name": long_profile_name,
                            "permanence_link": mark_safe(
                                '<a href="https://{}{}">{}</a>'.format(
                                    settings.ALLOWED_HOSTS[0],
                                    reverse(
                                        "repanier:producer_invoice_uuid_view",
                                        args=(0, producer.uuid),
                                    ),
                                    permanence,
                                )
                            ),
                            "signature": invoice_responsible["html_signature"],
                        }
                    )
                    html_body = template.render(context)
                    email = RepanierEmail(
                        subject=invoice_producer_mail_subject,
                        html_body=html_body,
                        to=to_email,
                    )
                    email.send_email()

    if REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_CUSTOMER:
        # To the customer we speak of "invoice".
        # This is the detail of the invoice, i.e. sold products
        invoice_description = permanence.invoice_description_v2
        for customer in Customer.objects.filter(
            customerinvoice__permanence_id=permanence.id,
            customerinvoice__customer_charged_id=F("id"),
            represent_this_buyinggroup=False,
        ):
            long_basket_name = (
                customer.long_basket_name
                if customer.long_basket_name is not None
                else customer.short_basket_name
            )
            if Purchase.objects.filter(
                permanence_id=permanence.id,
                customer_invoice__customer_charged_id=customer.id,
            ).exists():
                to_email = [customer.user.email]
                if customer.email2:
                    to_email.append(customer.email2)
                # to_email = list(set(to_email + invoice_responsible["to_email"]))

                invoice_customer_mail = config.invoice_customer_mail_v2
                invoice_customer_mail_subject = "{} - {}".format(
                    settings.REPANIER_SETTINGS_GROUP_NAME, permanence
                )
                customer_invoice = CustomerInvoice.objects.filter(
                    permanence_id=permanence.id, customer_id=customer.id
                ).first()
                (
                    customer_last_balance,
                    _,
                    customer_payment_needed,
                    customer_order_amount,
                ) = payment_message(customer, permanence, customer_invoice)
                template = Template(invoice_customer_mail)
                context = TemplateContext(
                    {
                        "name": long_basket_name,
                        "long_basket_name": long_basket_name,
                        "basket_name": customer.short_basket_name,
                        "short_basket_name": customer.short_basket_name,
                        "permanence_link": mark_safe(
                            '<a href="https://{}{}">{}</a>'.format(
                                settings.ALLOWED_HOSTS[0],
                                reverse("repanier:order_view", args=(permanence.id,)),
                                permanence,
                            )
                        ),
                        "last_balance_link": mark_safe(
                            '<a href="https://{}{}">{}</a>'.format(
                                settings.ALLOWED_HOSTS[0],
                                reverse("repanier:customer_invoice_view", args=(0,)),
                                customer_last_balance,
                            )
                        ),
                        "last_balance": mark_safe(customer_last_balance),
                        "order_amount": mark_safe(customer_order_amount),
                        "payment_needed": mark_safe(customer_payment_needed),
                        "invoice_description": mark_safe(invoice_description),
                        "signature": invoice_responsible["html_signature"],
                    }
                )
                html_body = template.render(context)
                email = RepanierEmail(
                    subject=invoice_customer_mail_subject,
                    html_body=html_body,
                    to=to_email,
                    show_customer_may_unsubscribe=True,
                )
                email.send_email()
