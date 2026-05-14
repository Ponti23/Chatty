from unittest.mock import MagicMock, patch
from app.storage import StorageClient

TENANT_ID = "tenant-00000000-0000-0000-0000-000000000001"
SOURCE_ID = "source-00000000-0000-0000-0000-000000000002"


def make_client():
    with patch("app.storage.Minio"):
        client = StorageClient("localhost:9000", "user", "pass", "raw-sources")
    return client


def test_save_uploads_to_correct_path():
    client = make_client()
    client.save(TENANT_ID, SOURCE_ID, "doc.pdf", b"content")

    call_args = client._minio.put_object.call_args
    assert call_args[0][0] == "raw-sources"
    assert call_args[0][1] == f"{TENANT_ID}/{SOURCE_ID}/doc.pdf"


def test_delete_removes_correct_path():
    client = make_client()
    client.delete(TENANT_ID, SOURCE_ID, "doc.pdf")

    call_args = client._minio.remove_object.call_args
    assert call_args[0][0] == "raw-sources"
    assert call_args[0][1] == f"{TENANT_ID}/{SOURCE_ID}/doc.pdf"
