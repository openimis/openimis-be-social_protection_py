from django.db import migrations

from core.models import Role, RoleRight

benefit_plan_rights = [160001, 160002, 160003, 160004]
imis_administrator_system = 64


def add_rights(apps, schema_editor):
    role = Role.objects.get(is_system=imis_administrator_system)
    for right_id in benefit_plan_rights:
        if not RoleRight.objects.filter(validity_to__isnull=True, role=role, right_id=right_id).exists():
            _add_right_for_role(role, right_id)


def _add_right_for_role(role, right_id):
    RoleRight.objects.create(role=role, right_id=right_id, audit_user_id=1)


class Migration(migrations.Migration):
    dependencies = [
        ('social_protection', '0001_initial')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
