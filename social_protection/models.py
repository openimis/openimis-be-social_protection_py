from django.db import models
from django.utils.translation import gettext as _
from core import models as core_models
from individual.models import Individual
from policyholder.models import PolicyHolder


class StatusChoices(models.TextChoices):
    POTENTIAL = 'POTENTIAL', _('POTENTIAL')
    ACTIVE = 'ACTIVE', _('ACTIVE')
    GRADUATED = 'GRADUATED', _('GRADUATED')
    SUSPENDED = 'SUSPENDED', _('SUSPENDED')


class BenefitPlan(core_models.HistoryBusinessModel):
    code = models.CharField(max_length=8, null=False)
    name = models.CharField(max_length=255, null=False)
    max_beneficiaries = models.SmallIntegerField()
    ceiling_per_beneficiary = models.DecimalField(max_digits=18,
                                                  decimal_places=2,
                                                  blank=True,
                                                  null=True,
                                                  )
    holder = models.ForeignKey(PolicyHolder, models.DO_NOTHING, blank=True, null=True)
    beneficiary_data_schema = models.JSONField(null=True, blank=True)


class Beneficiary(core_models.HistoryBusinessModel):
    individual = models.ForeignKey(Individual, models.DO_NOTHING, null=False)
    benefit_plan = models.ForeignKey(BenefitPlan, models.DO_NOTHING, null=False)
    status = models.CharField(max_length=100, choices=StatusChoices.choices, null=False)


class Group(core_models.HistoryBusinessModel):
    benefit_plan = models.ForeignKey(BenefitPlan, models.DO_NOTHING, null=False)
    status = models.CharField(max_length=100, choices=StatusChoices.choices, null=False)


class GroupIndividual(core_models.HistoryBusinessModel):
    group = models.ForeignKey(Group, models.DO_NOTHING)
    individual = models.ForeignKey(Individual, models.DO_NOTHING)
