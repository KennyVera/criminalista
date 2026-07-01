from django.urls import path

from core.views import FactCrimesListView, HealthView
from core.views_api import (
    AnalyticsCrimesByDistrictView,
    CollectionMetaDetailView,
    CollectionRecordDetailView,
    CollectionRecordsView,
    CollectionsMetaView,
    DashboardStatsView,
    EtlStatusAliasView,
    EtlTaskStatusView,
    PocketBaseSyncStatsView,
    RelationOptionsView,
    RunEtlToMinioView,
    SyncPocketBaseView,
    UnifiedJobStatusView,
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
    path("sync/pocketbase/", SyncPocketBaseView.as_view(), name="sync-pocketbase"),
    path(
        "sync/pocketbase/stats/",
        PocketBaseSyncStatsView.as_view(),
        name="sync-pocketbase-stats",
    ),
    path("etl/pb-to-minio/", RunEtlToMinioView.as_view(), name="etl-pb-to-minio"),
    path("etl/status/<str:task_id>/", EtlTaskStatusView.as_view(), name="etl-task-status"),
    path("etl-status/<str:task_id>/", EtlStatusAliasView.as_view(), name="etl-status-alias"),
    path("jobs/status/<str:task_id>/", UnifiedJobStatusView.as_view(), name="job-status"),
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
