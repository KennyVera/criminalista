from django.conf import settings

from django.core.management.base import BaseCommand, CommandError



from core.pocketbase.schema import CRIMES_220K_SCHEMA

from core.services.pocketbase import PocketBaseClient





class Command(BaseCommand):

    help = "Crea en PocketBase SOLO la colección crimes_220k (dataset crudo ~220k)."



    def handle(self, *args, **options):

        if not settings.POCKETBASE_ADMIN_PASSWORD:

            raise CommandError("Define POCKETBASE_ADMIN_PASSWORD en backend_django/.env")



        with PocketBaseClient() as client:

            client.auth_admin()

            self.stdout.write(self.style.SUCCESS("Autenticado en PocketBase."))



            existing = {c["name"]: c for c in client.list_collections()}

            raw_name = CRIMES_220K_SCHEMA["name"]



            if raw_name not in existing:

                client.create_collection(CRIMES_220K_SCHEMA)

                self.stdout.write(self.style.SUCCESS(f"  + {raw_name} creada"))

            else:

                self.stdout.write(f"  · {raw_name} ya existe")



        self.stdout.write(

            self.style.SUCCESS(

                "\nPocketBase listo (solo dataset crudo).\n"

                "Dimensiones y hechos van en MinIO: python manage.py etl_pb_to_minio\n"

            )

        )

