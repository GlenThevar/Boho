import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sample_csv_download():
    res = client.get("/api/datasets/sample-csv")
    assert res.status_code == 200
    assert "source_ip,destination_ip,destination_port,protocol" in res.text
    assert "traffic-001" in res.text


def test_valid_csv_upload_preview():
    csv_data = (
        "record_id,source_ip,destination_ip,destination_port,protocol\n"
        "t1,192.168.1.1,10.0.0.1,80,TCP\n"
        "t2,192.168.1.2,10.0.0.2,53,UDP\n"
        "t3,192.168.1.3,10.0.0.3,,ICMP\n"
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))
    res = client.post(
        "/api/datasets/upload-and-validate",
        files={"file": ("test.csv", file_bytes, "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 3
    assert data["valid_count"] == 3
    assert data["invalid_count"] == 0
    assert len(data["validation_issues"]) == 0


def test_csv_upload_with_malformed_individual_rows():
    csv_data = (
        "record_id,source_ip,destination_ip,destination_port,protocol\n"
        "t1,192.168.1.1,10.0.0.1,80,TCP\n"
        "bad-row,999.999.999.999,10.0.0.2,53,UDP\n"  # Invalid IP
        "bad-port,192.168.1.3,10.0.0.3,99999,TCP\n"    # Out of range port
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))
    res = client.post(
        "/api/datasets/upload-and-validate",
        files={"file": ("test_malformed.csv", file_bytes, "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 3
    assert data["valid_count"] == 1
    assert data["invalid_count"] == 2
    assert len(data["validation_issues"]) == 2
    assert data["validation_issues"][0]["row_number"] == 3
    assert any("Invalid source IP" in err for err in data["validation_issues"][0]["errors"])
    assert data["validation_issues"][1]["row_number"] == 4
    assert any("outside valid range" in err for err in data["validation_issues"][1]["errors"])


def test_csv_fatal_error_on_missing_required_columns():
    csv_data = (
        "record_id,source_ip,protocol\n"  # Missing destination_ip and destination_port
        "t1,192.168.1.1,TCP\n"
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))
    res = client.post(
        "/api/datasets/upload-and-validate",
        files={"file": ("bad_headers.csv", file_bytes, "text/csv")}
    )
    assert res.status_code == 400
    assert "Missing required column(s)" in res.json()["detail"]


def test_csv_fatal_error_on_non_csv_extension():
    file_bytes = io.BytesIO(b"binary data")
    res = client.post(
        "/api/datasets/upload-and-validate",
        files={"file": ("data.pcap", file_bytes, "application/octet-stream")}
    )
    assert res.status_code == 400
    assert "Only CSV files" in res.json()["detail"]


def test_csv_fatal_error_on_empty_file():
    file_bytes = io.BytesIO(b"")
    res = client.post(
        "/api/datasets/upload-and-validate",
        files={"file": ("empty.csv", file_bytes, "text/csv")}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"]
