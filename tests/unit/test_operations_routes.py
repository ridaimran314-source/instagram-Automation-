from fastapi.testclient import TestClient

from app.main import app


class FakeGoogleSheetsClient:
    def __init__(self, settings) -> None:
        self.settings = settings


class FakeScholarshipSheetSyncService:
    def __init__(self, session, client) -> None:
        self.session = session
        self.client = client

    def sync(self):
        class Result:
            fetched_rows = 1
            created_records = 1
            updated_records = 0
            skipped_rows = 0

        return Result()


class FakeScholarshipPipeline:
    def __init__(self, settings, session) -> None:
        self.settings = settings
        self.session = session

    def run_once(self) -> bool:
        return True


def test_sync_scholarships_route_returns_success(monkeypatch) -> None:
    from app.api.routes import operations

    monkeypatch.setattr(operations, "GoogleSheetsClient", FakeGoogleSheetsClient)
    monkeypatch.setattr(operations, "ScholarshipSheetSyncService", FakeScholarshipSheetSyncService)

    client = TestClient(app)
    response = client.post("/operations/sync-scholarships")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_pipeline_once_route_returns_success(monkeypatch) -> None:
    from app.api.routes import operations

    monkeypatch.setattr(operations, "ScholarshipPipeline", FakeScholarshipPipeline)

    client = TestClient(app)
    response = client.post("/operations/run-pipeline-once")

    assert response.status_code == 200
    assert response.json()["detail"] == "Processed one pending scholarship."
