from django.urls import path

from core.views import FactCrimesListView, HealthView
from core.views_api import (
    AnalyticsCrimesByDistrictView,
    CollectionMetaDetailView,
    CollectionRecordDetailView,
    CollectionRecordsView,
    CollectionsMetaView,
    DashboardStatsView,
    GenerateFakeDataAsyncView,
    GenerateFakeDataBatchView,
    GenerateFakeDataRealisticBatchView,
    GenerateFakeDataTaskStatusView,
    GenerateFakeDataView,
    RelationOptionsView,
    EtlTaskStatusView,
    RunEtlToMinioView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("crimes/", FactCrimesListView.as_view(), name="fact-crimes-list"),
    path("meta/collections/", CollectionsMetaView.as_view(), name="collections-meta"),
    path(
        "meta/collections/<str:collection>/",
        CollectionMetaDetailView.as_view(),
        name="collection-meta-detail",
    ),
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path(
        "analytics/crimes-by-district/",
        AnalyticsCrimesByDistrictView.as_view(),
        name="analytics-crimes-by-district",
    ),
    path("generate-fake-data/", GenerateFakeDataView.as_view(), name="generate-fake-data"),
    path(
        "generate-fake-data/batch/",
        GenerateFakeDataBatchView.as_view(),
        name="generate-fake-data-batch",
    ),
    path(
        "generate-fake-data/realistic/batch/",
        GenerateFakeDataRealisticBatchView.as_view(),
        name="generate-fake-data-realistic-batch",
    ),
    path(
        "generate-fake-data/async/",
        GenerateFakeDataAsyncView.as_view(),
        name="generate-fake-data-async",
    ),
    path(
        "generate-fake-data/status/<str:task_id>/",
        GenerateFakeDataTaskStatusView.as_view(),
        name="generate-fake-data-status",
    ),
    path("etl/pb-to-minio/", RunEtlToMinioView.as_view(), name="etl-pb-to-minio"),
    path("etl/status/<str:task_id>/", EtlTaskStatusView.as_view(), name="etl-task-status"),
    path(
        "collections/<str:collection>/records/",
        CollectionRecordsView.as_view(),
        name="collection-records",
    ),
    path(
        "collections/<str:collection>/records/<str:record_id>/",
        CollectionRecordDetailView.as_view(),
        name="collection-record-detail",
    ),
    path(
        "collections/<str:collection>/options/",
        RelationOptionsView.as_view(),
        name="relation-options",
    ),
]
