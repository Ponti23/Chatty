import io
from minio import Minio
from minio.error import S3Error


class StorageClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self._minio = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self._bucket = bucket

    def ensure_bucket(self) -> None:
        if not self._minio.bucket_exists(self._bucket):
            self._minio.make_bucket(self._bucket)

    def save(self, tenant_id: str, source_id: str, filename: str, content: bytes) -> str:
        object_name = f"{tenant_id}/{source_id}/{filename}"
        self._minio.put_object(
            self._bucket,
            object_name,
            io.BytesIO(content),
            length=len(content),
        )
        return object_name

    def delete(self, tenant_id: str, source_id: str, filename: str) -> None:
        object_name = f"{tenant_id}/{source_id}/{filename}"
        try:
            self._minio.remove_object(self._bucket, object_name)
        except S3Error:
            pass
