# -*- coding: utf-8
import logging

from cms.toolbar_pool import toolbar_pool
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from djangocms_text_ckeditor.fields import HTMLField
from menus.menu_pool import menu_pool
from parler.models import TranslatableModel, TranslatedFields, TranslationDoesNotExist

from repanier.const import *
from repanier.fields.RepanierMoneyField import ModelMoneyField

logger = logging.getLogger(__name__)


class Configuration(TranslatableModel):
    group_name = models.CharField(
        _("Name of the group"),
        max_length=50, default=settings.REPANIER_SETTINGS_GROUP_NAME)
    login_attempt_counter = models.DecimalField(
        _("Login attempt counter"),
        default=DECIMAL_ZERO, max_digits=2, decimal_places=0)
    password_reset_on = models.DateTimeField(
        _("Password reset on"), null=True, blank=True, default=None)
    name = models.CharField(
        max_length=3,
        choices=LUT_PERMANENCE_NAME,
        default=PERMANENCE_NAME_PERMANENCE,
        verbose_name=_("Offers name"))
    # email = models.EmailField(
    #     _("Email"), blank=False, default=settings.DJANGO_SETTINGS_EMAIL_HOST_USER)

    currency = models.CharField(
        max_length=3,
        choices=LUT_CURRENCY,
        default=CURRENCY_EUR,
        verbose_name=_("Currency"))
    max_week_wo_participation = models.DecimalField(
        _("Alert the customer after this number of weeks without participation"),
        help_text=_("0 mean : never display a pop up."),
        default=DECIMAL_ZERO, max_digits=2, decimal_places=0,
        validators=[MinValueValidator(0)])
    send_abstract_order_mail_to_customer = models.BooleanField(_("Send abstract order mail to customers"),
                                                               default=False)
    send_order_mail_to_board = models.BooleanField(
        _("Send an order distribution email to members registered for a task"), default=True)
    send_invoice_mail_to_customer = models.BooleanField(_("Send invoice mail to customers"), default=True)
    send_invoice_mail_to_producer = models.BooleanField(_("Send invoice mail to producers"), default=False)
    invoice = models.BooleanField(_("Enable accounting module"), default=True)
    display_anonymous_order_form = models.BooleanField(
        _("Allow the anonymous visitor to see the customer order screen"), default=True)
    display_who_is_who = models.BooleanField(_("Display the \"who's who\""), default=True)
    xlsx_portrait = models.BooleanField(_("Always generate XLSX files in portrait mode"), default=False)
    bank_account = models.CharField(_("Bank account"), max_length=100, blank=True, default=EMPTY_STRING)
    vat_id = models.CharField(
        _("VAT id"), max_length=20, blank=True, default=EMPTY_STRING)
    page_break_on_customer_check = models.BooleanField(_("Page break on customer check"), default=False)
    membership_fee = ModelMoneyField(
        _("Membership fee"),
        default=DECIMAL_ZERO, max_digits=8, decimal_places=2)
    membership_fee_duration = models.DecimalField(
        _("Membership fee duration"),
        help_text=_("Number of month(s). 0 mean : no membership fee."),
        default=DECIMAL_ZERO, max_digits=3, decimal_places=0,
        validators=[MinValueValidator(0)])
    home_site = models.URLField(_("Home site"), blank=True, default="/")
    permanence_of_last_cancelled_invoice = models.ForeignKey(
        'Permanence',
        on_delete=models.PROTECT, blank=True, null=True)
    db_version = models.PositiveSmallIntegerField(default=0)
    translations = TranslatedFields(
        group_label=models.CharField(_("Label to mention on the invoices of the group"),
                                     max_length=100,
                                     default=EMPTY_STRING,
                                     blank=True),
        how_to_register=HTMLField(_("How to register"),
                                  help_text=EMPTY_STRING,
                                  configuration='CKEDITOR_SETTINGS_MODEL2',
                                  default=EMPTY_STRING,
                                  blank=True),
        offer_customer_mail=HTMLField(_("Contents of the order opening email sent to consumers authorized to order"),
                                      help_text=EMPTY_STRING,
                                      configuration='CKEDITOR_SETTINGS_MODEL2',
                                      default=EMPTY_STRING,
                                      blank=True),
        offer_producer_mail=HTMLField(_("Email content"),
                                      help_text=EMPTY_STRING,
                                      configuration='CKEDITOR_SETTINGS_MODEL2',
                                      default=EMPTY_STRING,
                                      blank=True),
        order_customer_mail=HTMLField(_("Content of the order confirmation email sent to the consumers concerned"),
                                      help_text=EMPTY_STRING,
                                      configuration='CKEDITOR_SETTINGS_MODEL2',
                                      default=EMPTY_STRING,
                                      blank=True),
        cancel_order_customer_mail=HTMLField(
            _("Content of the email in case of cancellation of the order sent to the consumers concerned"),
            help_text=EMPTY_STRING,
            configuration='CKEDITOR_SETTINGS_MODEL2',
            default=EMPTY_STRING,
            blank=True),
        order_staff_mail=HTMLField(_("Content of the order distribution email sent to the members enrolled to a task"),
                                   help_text=EMPTY_STRING,
                                   configuration='CKEDITOR_SETTINGS_MODEL2',
                                   default=EMPTY_STRING,
                                   blank=True),
        order_producer_mail=HTMLField(_("Content of the order confirmation email sent to the producers concerned"),
                                      help_text=EMPTY_STRING,
                                      configuration='CKEDITOR_SETTINGS_MODEL2',
                                      default=EMPTY_STRING,
                                      blank=True),
        invoice_customer_mail=HTMLField(_("Content of the invoice confirmation email sent to the customers concerned"),
                                        help_text=EMPTY_STRING,
                                        configuration='CKEDITOR_SETTINGS_MODEL2',
                                        default=EMPTY_STRING,
                                        blank=True),
        invoice_producer_mail=HTMLField(_("Content of the payment confirmation email sent to the producers concerned"),
                                        help_text=EMPTY_STRING,
                                        configuration='CKEDITOR_SETTINGS_MODEL2',
                                        default=EMPTY_STRING,
                                        blank=True),
    )

    def clean(self):
        try:
            template = Template(self.offer_customer_mail)
        except Exception as error_str:
            raise ValidationError(mark_safe("{} : {}".format(self.offer_customer_mail, error_str)))
        try:
            template = Template(self.offer_producer_mail)
        except Exception as error_str:
            raise ValidationError(mark_safe("{} : {}".format(self.offer_producer_mail, error_str)))
        try:
            template = Template(self.order_customer_mail)
        except Exception as error_str:
            raise ValidationError(mark_safe("{} : {}".format(self.order_customer_mail, error_str)))
        try:
            template = Template(self.order_staff_mail)
        except Exception as error_str:
            raise ValidationError(mark_safe("{} : {}".format(self.order_staff_mail, error_str)))
        try:
            template = Template(self.order_producer_mail)
        except Exception as error_str:
            raise ValidationError(mark_safe("{} : {}".format(self.order_producer_mail, error_str)))
        if settings.REPANIER_SETTINGS_MANAGE_ACCOUNTING:
            try:
                template = Template(self.invoice_customer_mail)
            except Exception as error_str:
                raise ValidationError(mark_safe("{} : {}".format(self.invoice_customer_mail, error_str)))
            try:
                template = Template(self.invoice_producer_mail)
            except Exception as error_str:
                raise ValidationError(mark_safe("{} : {}".format(self.invoice_producer_mail, error_str)))

    @classmethod
    def init_repanier(cls):
        from repanier.const import DECIMAL_ONE, PERMANENCE_NAME_PERMANENCE, CURRENCY_EUR
        from repanier.models.producer import Producer
        from repanier.models.bankaccount import BankAccount
        from repanier.models.staff import Staff
        from repanier.models.customer import Customer

        # Create the configuration record managed via the admin UI
        config = Configuration.objects.filter(id=DECIMAL_ONE).first()
        if config is not None:
            return config
        site = Site.objects.get_current()
        if site is not None:
            site.name = settings.REPANIER_SETTINGS_GROUP_NAME
            site.domain = settings.ALLOWED_HOSTS[0]
            site.save()
        config = Configuration.objects.create(
            group_name=settings.REPANIER_SETTINGS_GROUP_NAME,
            name=PERMANENCE_NAME_PERMANENCE,
            bank_account="BE99 9999 9999 9999",
            currency=CURRENCY_EUR
        )
        config.init_email()
        config.save()

        # Create firsts users
        Producer.get_or_create_group()
        customer_buyinggroup = Customer.get_or_create_group()
        very_first_customer = Customer.get_or_create_the_very_first_customer()

        BankAccount.open_account(
            customer_buyinggroup=customer_buyinggroup,
            very_first_customer=very_first_customer
        )

        coordinator = Staff.get_or_create_any_coordinator()
        Staff.get_or_create_order_responsible()
        Staff.get_or_create_invoice_responsible()
        # Create and publish first web page
        if not coordinator.is_webmaster:
            # This should not be the case...
            return

        from cms.models import StaticPlaceholder
        from cms.constants import X_FRAME_OPTIONS_DENY
        from cms import api
        page = api.create_page(
            title=_("Home"),
            soft_root=False,
            template=settings.CMS_TEMPLATE_HOME,
            language=settings.LANGUAGE_CODE,
            published=True,
            parent=None,
            xframe_options=X_FRAME_OPTIONS_DENY,
            in_navigation=True
        )
        try:
            # New in CMS 3.5
            page.set_as_homepage()
        except:
            pass

        placeholder = page.placeholders.get(slot="home-hero")
        api.add_plugin(
            placeholder=placeholder,
            plugin_type='TextPlugin',
            language=settings.LANGUAGE_CODE,
            body=settings.CMS_TEMPLATE_HOME_HERO)
        placeholder = page.placeholders.get(slot="home-col-1")
        api.add_plugin(
            placeholder=placeholder,
            plugin_type='TextPlugin',
            language=settings.LANGUAGE_CODE,
            body=settings.CMS_TEMPLATE_HOME_COL_1)
        placeholder = page.placeholders.get(slot="home-col-2")
        api.add_plugin(
            placeholder=placeholder,
            plugin_type='TextPlugin',
            language=settings.LANGUAGE_CODE,
            body=settings.CMS_TEMPLATE_HOME_COL_2)
        placeholder = page.placeholders.get(slot="home-col-3")
        api.add_plugin(
            placeholder=placeholder,
            plugin_type='TextPlugin',
            language=settings.LANGUAGE_CODE,
            body=settings.CMS_TEMPLATE_HOME_COL_3)
        static_placeholder = StaticPlaceholder(
            code="footer",
            # site_id=1
        )
        static_placeholder.save()
        api.add_plugin(
            placeholder=static_placeholder.draft,
            plugin_type='TextPlugin',
            language=settings.LANGUAGE_CODE,
            body='hello world footer'
        )
        static_placeholder.publish(
            request=None,
            language=settings.LANGUAGE_CODE,
            force=True
        )
        api.publish_page(
            page=page,
            user=coordinator.user,
            language=settings.LANGUAGE_CODE)

        return config

    def init_email(self):
        for language in settings.PARLER_LANGUAGES[settings.SITE_ID]:
            language_code = language["code"]
            self.set_current_language(language_code)
            try:
                self.offer_customer_mail = """
                    Bonjour,<br />
                    <br />
                    Les commandes de la {{ permanence_link }} sont maintenant ouvertes auprès de : {{ offer_producer }}.<br />
                    {% if offer_description %}<br />{{ offer_description }}<br />
                    {% endif %} {% if offer_recent_detail %}<br />
                    Nouveauté(s) :<br />
                    {{ offer_recent_detail }}{% endif %}<br />
                    <br />
                    {{ signature }}
                    """
                self.offer_producer_mail = """
                    Cher/Chère {{ long_profile_name }},<br>
                    <br>
                    {% if offer_description != "" %}Voici l'annonce consommateur :<br>
                    {{ offer_description }}<br>
                    <br>
                    {% endif %} Veuillez vérifier votre <strong>{{ offer_link }}</strong>.<br>
                    <br>
                    {{ signature }}
                    """
                self.order_customer_mail = """
                    Bonjour {{ long_basket_name }},<br>
                    <br>
                    En pièce jointe vous trouverez le montant de votre panier {{ short_basket_name }} de la {{ permanence_link }}.<br>
                    <br>
                    {{ last_balance }}<br>
                    {{ order_amount }}<br>
                    {% if on_hold_movement %}{{ on_hold_movement }}<br>
                    {% endif %} {% if payment_needed %}{{ payment_needed }}<br>
                    {% endif %}<br>
                    <br>
                    {{ signature }}
                    """
                self.cancel_order_customer_mail = """
                    Bonjour {{ long_basket_name }},<br>
                    <br>
                    La commande ci-jointe de votre panier {{ short_basket_name }} de la {{ permanence_link }} <b>a été annulée</b> car vous ne l'avez pas confirmée.<br>
                    <br>
                    {{ signature }}
                    """
                self.order_staff_mail = """
                    Cher/Chère membre de l'équipe de préparation,<br>
                    <br>
                    En pièce jointe vous trouverez la liste de préparation pour la {{ permanence_link }}.<br>
                    <br>
                    L'équipe de préparation est composée de :<br>
                    {{ board_composition_and_description }}<br>
                    <br>
                    {{ signature }}
                    """
                self.order_producer_mail = """
                    Cher/Chère {{ name }},<br>
                    <br>
                    {% if order_empty %}Le groupe ne vous a rien acheté pour la {{ permanence_link }}.{% else %}En pièce jointe, vous trouverez la commande du groupe pour la {{ permanence }}.{% if duplicate %}<br>
                    <strong>ATTENTION </strong>: La commande est présente en deux exemplaires. Le premier exemplaire est classé par produit et le duplicata est classé par panier.{% else %}{% endif %}{% endif %}<br>
                    <br>
                    {{ signature }}
                    """
                self.invoice_customer_mail = """
                    Bonjour {{ name }},<br>
                    <br>
                    En cliquant sur ce lien vous trouverez votre facture pour la {{ permanence_link }}.{% if invoice_description %}<br>
                    <br>
                    {{ invoice_description }}{% endif %}
                    <br>
                    {{ order_amount }}<br>
                    {{ last_balance_link }}<br>
                    {% if payment_needed %}{{ payment_needed }}<br>
                    {% endif %}<br>
                    <br>
                    {{ signature }}
                    """
                self.invoice_producer_mail = """
                    Cher/Chère {{ profile_name }},<br>
                    <br>
                    En cliquant sur ce lien vous trouverez le détail de notre paiement pour la {{ permanence_link }}.<br>
                    <br>
                    {{ signature }}
                    """
                self.save_translations()
            except TranslationDoesNotExist:
                pass

    def upgrade_db(self):
        logger.debug("######## upgrade_db")
        if self.db_version == 0:
            from repanier.models import Product, OfferItemWoReceiver, BankAccount, Permanence, Staff
            # Staff.objects.rebuild()
            Product.objects.filter(
                is_box=True
            ).order_by('?').update(
                limit_order_quantity_to_stock=True
            )
            OfferItemWoReceiver.objects.filter(
                permanence__status__gte=PERMANENCE_SEND,
                order_unit=PRODUCT_ORDER_UNIT_PC_KG
            ).order_by('?').update(
                use_order_unit_converted=True
            )
            for bank_account in BankAccount.objects.filter(
                    permanence__isnull=False,
                    producer__isnull=True,
                    customer__isnull=True
            ).order_by('?').only("id", "permanence_id"):
                Permanence.objects.filter(
                    id=bank_account.permanence_id,
                    invoice_sort_order__isnull=True
                ).order_by('?').update(invoice_sort_order=bank_account.id)
            for permanence in Permanence.objects.filter(
                    status__in=[PERMANENCE_CANCELLED, PERMANENCE_ARCHIVED],
                    invoice_sort_order__isnull=True
            ).order_by('?'):
                bank_account = BankAccount.get_closest_to(permanence.permanence_date)
                if bank_account is not None:
                    permanence.invoice_sort_order = bank_account.id
                    permanence.save(update_fields=['invoice_sort_order'])
            Staff.objects.order_by('?').update(
                is_order_manager=F('is_reply_to_order_email'),
                is_invoice_manager=F('is_reply_to_invoice_email'),
                is_order_referent=F('is_contributor')
            )
            self.db_version = 1
        if self.db_version == 1:
            for user in User.objects.filter(is_staff=False).order_by('?'):
                user.first_name = EMPTY_STRING
                user.last_name = user.username[:30]
                user.save()
            for user in User.objects.filter(is_staff=True, is_superuser=False).order_by('?'):
                user.first_name = EMPTY_STRING
                user.last_name = user.email[:30]
                user.save()
            self.db_version = 2
        if self.db_version == 2:
            from repanier.models import Staff
            Staff.objects.order_by('?').update(
                is_repanier_admin=F('is_coordinator'),
            )
            Staff.objects.filter(
                is_repanier_admin=True
            ).order_by('?').update(
                can_be_contacted=True,
            )
            Staff.objects.filter(
                is_order_manager=True
            ).order_by('?').update(
                can_be_contacted=True,
            )
            Staff.objects.filter(
                is_invoice_manager=True
            ).order_by('?').update(
                can_be_contacted=True,
            )
            Staff.objects.filter(
                is_invoice_referent=True
            ).order_by('?').update(
                is_invoice_manager=True,
            )
            Staff.objects.filter(
                is_order_referent=True
            ).order_by('?').update(
                is_order_manager=True,
            )
            self.db_version = 3
        if self.db_version == 3:
            from repanier.models import BankAccount, Configuration, Customer, OfferItemWoReceiver, Producer, \
                ProducerInvoice, Product, PurchaseWoReceiver
            BankAccount.objects.filter(
                operation_comment__isnull=True
            ).order_by('?').update(
                operation_comment=EMPTY_STRING
            )
            Configuration.objects.filter(
                bank_account__isnull=True
            ).order_by('?').update(
                bank_account=EMPTY_STRING
            )
            Configuration.objects.filter(
                home_site__isnull=True
            ).order_by('?').update(
                home_site="/"
            )
            Configuration.objects.filter(
                vat_id__isnull=True
            ).order_by('?').update(
                vat_id=EMPTY_STRING
            )
            Customer.objects.filter(
                about_me__isnull=True
            ).order_by('?').update(
                about_me=EMPTY_STRING
            )
            Customer.objects.filter(
                address__isnull=True
            ).order_by('?').update(
                address=EMPTY_STRING
            )
            Customer.objects.filter(
                bank_account1__isnull=True
            ).order_by('?').update(
                bank_account1=EMPTY_STRING
            )
            Customer.objects.filter(
                bank_account2__isnull=True
            ).order_by('?').update(
                bank_account2=EMPTY_STRING
            )
            Customer.objects.filter(
                city__isnull=True
            ).order_by('?').update(
                city=EMPTY_STRING
            )
            Customer.objects.filter(
                long_basket_name__isnull=True
            ).order_by('?').update(
                long_basket_name=EMPTY_STRING
            )
            Customer.objects.filter(
                memo__isnull=True
            ).order_by('?').update(
                memo=EMPTY_STRING
            )
            Customer.objects.filter(
                phone1__isnull=True
            ).order_by('?').update(
                phone1=EMPTY_STRING
            )
            Customer.objects.filter(
                phone2__isnull=True
            ).order_by('?').update(
                phone2=EMPTY_STRING
            )
            Customer.objects.filter(
                vat_id__isnull=True
            ).order_by('?').update(
                vat_id=EMPTY_STRING
            )
            OfferItemWoReceiver.objects.filter(
                not_permanences_dates__isnull=True
            ).order_by('?').update(
                not_permanences_dates=EMPTY_STRING
            )
            OfferItemWoReceiver.objects.filter(
                permanences_dates__isnull=True
            ).order_by('?').update(
                permanences_dates=EMPTY_STRING
            )
            OfferItemWoReceiver.objects.filter(
                permanences_dates_counter__isnull=True
            ).order_by('?').update(
                permanences_dates_counter=1
            )
            OfferItemWoReceiver.objects.filter(
                reference__isnull=True
            ).order_by('?').update(
                reference=EMPTY_STRING
            )
            Producer.objects.filter(
                address__isnull=True
            ).order_by('?').update(
                address=EMPTY_STRING
            )
            Producer.objects.filter(
                bank_account__isnull=True
            ).order_by('?').update(
                bank_account=EMPTY_STRING
            )
            Producer.objects.filter(
                city__isnull=True
            ).order_by('?').update(
                city=EMPTY_STRING
            )
            Producer.objects.filter(
                fax__isnull=True
            ).order_by('?').update(
                fax=EMPTY_STRING
            )
            Producer.objects.filter(
                long_profile_name__isnull=True
            ).order_by('?').update(
                long_profile_name=EMPTY_STRING
            )
            Producer.objects.filter(
                memo__isnull=True
            ).order_by('?').update(
                memo=EMPTY_STRING
            )
            Producer.objects.filter(
                offer_uuid__isnull=True
            ).order_by('?').update(
                offer_uuid=EMPTY_STRING
            )
            Producer.objects.filter(
                phone1__isnull=True
            ).order_by('?').update(
                phone1=EMPTY_STRING
            )
            Producer.objects.filter(
                phone2__isnull=True
            ).order_by('?').update(
                phone2=EMPTY_STRING
            )
            Producer.objects.filter(
                uuid__isnull=True
            ).order_by('?').update(
                uuid=EMPTY_STRING
            )
            Producer.objects.filter(
                vat_id__isnull=True
            ).order_by('?').update(
                vat_id=EMPTY_STRING
            )
            ProducerInvoice.objects.filter(
                invoice_reference__isnull=True
            ).order_by('?').update(
                invoice_reference=EMPTY_STRING
            )
            Product.objects.filter(
                reference__isnull=True
            ).order_by('?').update(
                reference=EMPTY_STRING
            )
            PurchaseWoReceiver.objects.filter(
                comment__isnull=True
            ).order_by('?').update(
                comment=EMPTY_STRING
            )
            self.db_version = 4

    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = _("Configuration")
        verbose_name_plural = _("Configurations")


# @receiver(post_init, sender=Configuration)
# def configuration_post_init(sender, **kwargs):
#     config = kwargs["instance"]
#     if config.id is not None:
#         config.previous_email_host_password = config.email_host_password
#     else:
#         config.previous_email_host_password = EMPTY_STRING
#     config.email_host_password = EMPTY_STRING


# @receiver(pre_save, sender=Configuration)
# def configuration_pre_save(sender, **kwargs):
#     config = kwargs["instance"]
#     if not config.bank_account:
#         config.bank_account = None


@receiver(post_save, sender=Configuration)
def configuration_post_save(sender, **kwargs):
    import repanier.cms_toolbar
    from repanier import apps

    config = kwargs["instance"]
    if config.id is not None:
        apps.REPANIER_SETTINGS_CONFIG = config
        if config.name == PERMANENCE_NAME_PERMANENCE:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Permanence")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Permanences")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Permanence of ")
        elif config.name == PERMANENCE_NAME_CLOSURE:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Closure")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Closures")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Closure of ")
        elif config.name == PERMANENCE_NAME_DELIVERY:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Delivery")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Deliveries")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Delivery of ")
        elif config.name == PERMANENCE_NAME_ORDER:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Order")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Orders")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Order of ")
        elif config.name == PERMANENCE_NAME_OPENING:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Opening")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Openings")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Opening of ")
        else:
            apps.REPANIER_SETTINGS_PERMANENCE_NAME = _("Distribution")
            apps.REPANIER_SETTINGS_PERMANENCES_NAME = _("Distributions")
            apps.REPANIER_SETTINGS_PERMANENCE_ON_NAME = _("Distribution of ")
        apps.REPANIER_SETTINGS_MAX_WEEK_WO_PARTICIPATION = config.max_week_wo_participation
        apps.REPANIER_SETTINGS_SEND_ABSTRACT_ORDER_MAIL_TO_CUSTOMER = config.send_abstract_order_mail_to_customer
        apps.REPANIER_SETTINGS_SEND_ORDER_MAIL_TO_BOARD = config.send_order_mail_to_board
        apps.REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_CUSTOMER = config.send_invoice_mail_to_customer
        apps.REPANIER_SETTINGS_SEND_INVOICE_MAIL_TO_PRODUCER = config.send_invoice_mail_to_producer
        apps.REPANIER_SETTINGS_DISPLAY_ANONYMOUS_ORDER_FORM = config.display_anonymous_order_form
        apps.REPANIER_SETTINGS_DISPLAY_WHO_IS_WHO = config.display_who_is_who
        apps.REPANIER_SETTINGS_XLSX_PORTRAIT = config.xlsx_portrait
        # if config.bank_account is not None and len(config.bank_account.strip()) == 0:
        #     apps.REPANIER_SETTINGS_BANK_ACCOUNT = None
        # else:
        apps.REPANIER_SETTINGS_BANK_ACCOUNT = config.bank_account
        # if config.vat_id is not None and len(config.vat_id.strip()) == 0:
        #     apps.REPANIER_SETTINGS_VAT_ID = None
        # else:
        apps.REPANIER_SETTINGS_VAT_ID = config.vat_id
        apps.REPANIER_SETTINGS_PAGE_BREAK_ON_CUSTOMER_CHECK = config.page_break_on_customer_check
        apps.REPANIER_SETTINGS_MEMBERSHIP_FEE = config.membership_fee
        apps.REPANIER_SETTINGS_MEMBERSHIP_FEE_DURATION = config.membership_fee_duration
        if config.currency == CURRENCY_LOC:
            apps.REPANIER_SETTINGS_CURRENCY_DISPLAY = "✿"
            apps.REPANIER_SETTINGS_AFTER_AMOUNT = False
            apps.REPANIER_SETTINGS_CURRENCY_XLSX = "_ ✿ * #,##0.00_ ;_ ✿ * -#,##0.00_ ;_ ✿ * \"-\"??_ ;_ @_ "
        elif config.currency == CURRENCY_CHF:
            apps.REPANIER_SETTINGS_CURRENCY_DISPLAY = 'Fr.'
            apps.REPANIER_SETTINGS_AFTER_AMOUNT = False
            apps.REPANIER_SETTINGS_CURRENCY_XLSX = "_ Fr\. * #,##0.00_ ;_ Fr\. * -#,##0.00_ ;_ Fr\. * \"-\"??_ ;_ @_ "
        else:
            apps.REPANIER_SETTINGS_CURRENCY_DISPLAY = "€"
            apps.REPANIER_SETTINGS_AFTER_AMOUNT = True
            apps.REPANIER_SETTINGS_CURRENCY_XLSX = "_ € * #,##0.00_ ;_ € * -#,##0.00_ ;_ € * \"-\"??_ ;_ @_ "
        if config.home_site:
            apps.REPANIER_SETTINGS_HOME_SITE = config.home_site
        else:
            apps.REPANIER_SETTINGS_HOME_SITE = "/"
        # config.email = settings.DJANGO_SETTINGS_EMAIL_HOST_USER
        menu_pool.clear()
        toolbar_pool.unregister(repanier.cms_toolbar.RepanierToolbar)
        toolbar_pool.register(repanier.cms_toolbar.RepanierToolbar)
        cache.clear()
