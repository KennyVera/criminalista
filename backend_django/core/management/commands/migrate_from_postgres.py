"""

Migración única PostgreSQL → PocketBase (solo dataset crudo crimes_220k).



Las dimensiones y hechos se generan vía ETL hacia MinIO:

  python manage.py etl_pb_to_minio



Uso:

  python manage.py migrate_from_postgres --dry-run

  python manage.py migrate_from_postgres --steps raw

"""



from django.conf import settings

from django.core.management.base import BaseCommand, CommandError



from core.migration.runner import PostgresMigrator

from core.services.pocketbase import PocketBaseClient





class Command(BaseCommand):

    help = "Migración única: Postgres → crimes_220k en PocketBase (dims/fact van a MinIO vía ETL)."



    def add_arguments(self, parser):

        parser.add_argument(

            "--steps",

            choices=["raw", "dims", "facts", "all"],

            default="raw",

            help="Solo 'raw' está soportado (crimes_220k). dims/facts están obsoletos en PocketBase.",

        )

        parser.add_argument(

            "--batch-size",

            type=int,

            default=200,

            help="Filas por lote leídas de Postgres (default: 200)",

        )

        parser.add_argument(

            "--dry-run",

            action="store_true",

            help="Simula sin escribir en PocketBase",

        )

        parser.add_argument(

            "--no-skip-existing",

            action="store_true",

            help="No omitir registros ya migrados (legacy_id / id)",

        )



    def handle(self, *args, **options):

        steps = options["steps"]

        if steps in ("dims", "facts"):

            raise CommandError(

                "Las dimensiones y fact_crimes ya NO se cargan en PocketBase.\n"

                "1) python manage.py migrate_from_postgres --steps raw\n"

                "2) python manage.py etl_pb_to_minio"

            )



        self._validate_config()



        self.stdout.write(

            self.style.WARNING(

                "\n=== Migración PostgreSQL → PocketBase (solo crimes_220k) ===\n"

                "Modelo estrella: python manage.py etl_pb_to_minio\n"

            )

        )



        if options["dry_run"]:

            self.stdout.write(self.style.NOTICE("Modo DRY-RUN: no se escribe en PocketBase.\n"))



        with PocketBaseClient() as pb:

            pb.auth_admin()

            if not pb.health():

                raise CommandError("PocketBase no responde. Levanta Docker: infra/docker compose up -d")



            migrator = PostgresMigrator(

                pb,

                batch_size=options["batch_size"],

                skip_existing=not options["no_skip_existing"],

                dry_run=options["dry_run"],

                log=lambda msg: self.stdout.write(msg) or self.stdout.flush(),

            )



            self.stdout.write(

                self.style.MIGRATE_HEADING(

                    "\n[1] Dataset crudo crimes_220k (~220k filas, puede tardar)"

                )

            )

            c, s, e = migrator.migrate_crimes_220k()

            self.stdout.write(f"  Resumen: creados={c} omitidos={s} errores={e}")



        self.stdout.write(

            self.style.SUCCESS(

                "\nMigración raw finalizada.\n"

                "Siguiente paso ETL: python manage.py etl_pb_to_minio\n"

            )

        )



    def _validate_config(self):

        missing = []

        for key in (

            "POSTGRES_HOST",

            "POSTGRES_DB",

            "POSTGRES_USER",

            "POSTGRES_PASSWORD",

            "POCKETBASE_ADMIN_PASSWORD",

        ):

            if not getattr(settings, key, None):

                missing.append(key)

        if missing:

            raise CommandError(

                f"Faltan variables en backend_django/.env: {', '.join(missing)}\n"

                "Copia .env.example y completa la sección POSTGRES_* (solo migración)."

            )


