from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comptes", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="utilisateur",
            name="departement",
            field=models.CharField(
                choices=[
                    ("VENTE", "Vente"),
                    ("COMPTABILITE", "Comptabilité"),
                    ("CONFORMITE", "Conformité"),
                ],
                max_length=100,
                verbose_name="Département",
            ),
        ),
    ]
