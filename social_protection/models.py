from django.db import models
from core import models as core_models
from policyholder.models import PolicyHolder


class BenefitPlan(core_models.HistoryBusinessModel):
    code = models.CharField(db_column='Code', max_length=50, null=False)
    name = models.CharField(db_column='NameBF', max_length=255, null=False)
    date_from = models.DateTimeField(db_column="DateFrom")
    date_to = models.DateTimeField(db_column="DateTo")
    max_beneficiaries = models.SmallIntegerField(db_column="MaxNoBeneficiaries")
    ceiling_per_beneficiary = models.DecimalField(db_column="BeneficiaryCeiling",
                                                  max_digits=18,
                                                  decimal_places=2,
                                                  blank=True,
                                                  null=True,
                                                  )
    organization = models.ForeignKey(PolicyHolder, models.DO_NOTHING, db_column='Organization', blank=True, null=True)
    schema = models.TextField(db_column="Schema", null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'tblBenefitPlan'
