from django.db import models
from core import models as core_models
from policyholder.models import PolicyHolder


class BenefitPlan(core_models.HistoryBusinessModel):
    code = models.CharField(db_column='Code', max_length=8, null=False)
    name = models.CharField(db_column='NameBF', max_length=255, null=False)
    max_beneficiaries = models.SmallIntegerField(db_column="MaxNoBeneficiaries")
    ceiling_per_beneficiary = models.DecimalField(db_column="BeneficiaryCeiling",
                                                  max_digits=18,
                                                  decimal_places=2,
                                                  blank=True,
                                                  null=True,
                                                  )
    holder = models.ForeignKey(PolicyHolder, models.DO_NOTHING, db_column='Holder', blank=True, null=True)
    schema = models.TextField(db_column="Schema", null=True, blank=True)
