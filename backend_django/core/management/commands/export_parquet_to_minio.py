"""

Pipeline académico 1–3 (recomendado):



  python manage.py etl_pb_to_minio



Este comando delega al ETL o exporta solo crimes_220k desde PocketBase.

"""



from django.core.management.base import BaseCommand, CommandError



from core.etl.star_schema import run_etl_pb_to_minio





class Command(BaseCommand):

    help = "ETL PocketBase (crimes_220k) → Parquet → MinIO. Usa etl_pb_to_minio internamente."



    def add_arguments(self, parser):

        parser.add_argument(

            "--no-raw-copy",

            action="store_true",

            help="No guardar copia crimes_220k.parquet en MinIO.",

        )



    def handle(self, *args, **options):

        self.stdout.write(

            self.style.WARNING(

                "\n[1] Extraer crimes_220k desde PocketBase\n"

                "[2] Transformar a modelo estrella + Parquet\n"

                "[3] Cargar en MinIO\n"

            )

        )

        try:

            result = run_etl_pb_to_minio(export_raw_copy=not options["no_raw_copy"])

        except Exception as exc:

            raise CommandError(str(exc)) from exc



        self.stdout.write(self.style.SUCCESS(result["message"]))

        for name, count in result.get("collections", {}).items():

            self.stdout.write(f"  · {name}: {count:,} filas")


