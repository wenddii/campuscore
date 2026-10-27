from django.db import migrations, models


def create_settings_table_if_needed(apps, schema_editor):
    registration_settings = apps.get_model(
        "registrations",
        "RegistrationSettings",
    )
    table_name = registration_settings._meta.db_table
    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name not in existing_tables:
        schema_editor.create_model(registration_settings)


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="RegistrationSettings",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("registration_open", models.BooleanField(default=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        "verbose_name": "Registration setting",
                        "verbose_name_plural": "Registration settings",
                    },
                ),
            ],
        ),
        migrations.RunPython(
            create_settings_table_if_needed,
            migrations.RunPython.noop,
        ),
    ]
