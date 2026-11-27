from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0012_brand_storefront_banner"),
    ]

    operations = [
        migrations.CreateModel(
            name="AmogaDecorEnquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("company_name", models.CharField(blank=True, max_length=160)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("wedding", "Wedding"),
                            ("engagement", "Engagement"),
                            ("corporate", "Corporate / Launch"),
                            ("birthday", "Birthday"),
                            ("reception", "Reception"),
                            ("cultural", "Cultural / Festival"),
                            ("other", "Other"),
                        ],
                        max_length=40,
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=30)),
                (
                    "decor_details",
                    models.TextField(help_text="Decor style, theme, and customization requirements."),
                ),
                ("is_read", models.BooleanField(default=False, verbose_name="Followed up")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Amoga Decor enquiry",
                "verbose_name_plural": "Amoga Decor enquiries",
                "ordering": ["-created_at"],
            },
        ),
    ]
