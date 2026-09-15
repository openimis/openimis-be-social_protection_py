from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_protection', '0028_alter_beneficiary_date_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='benefitplan',
            name='code',
            field=models.CharField(max_length=9),
        ),
        migrations.AlterField(
            model_name='historicalbenefitplan',
            name='code',
            field=models.CharField(max_length=9),
        ),
    ]