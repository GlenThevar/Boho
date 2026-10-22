import io
import csv
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import PlainTextResponse
from app.engine.firewall_engine import validate_record, TrafficRecordData
from app.schemas.firewall import TrafficPreviewResponse, ValidationIssue

router = APIRouter(prefix="/api/datasets", tags=["Dataset Testing"])

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_ROW_COUNT = 10000

SAMPLE_CSV_CONTENT = """record_id,source_ip,destination_ip,destination_port,protocol
traffic-001,192.168.1.45,10.0.0.10,443,TCP
traffic-002,192.168.1.50,1.1.1.1,53,UDP
traffic-003,192.168.1.102,8.8.8.8,,ICMP
traffic-004,10.0.0.25,10.0.0.10,23,TCP
traffic-005,203.0.113.88,10.0.0.10,80,TCP
traffic-006,172.16.5.20,10.0.0.10,8080,TCP
traffic-007,192.168.1.99,10.0.0.10,80,TCP
traffic-008,192.168.2.10,192.168.1.10,22,TCP
traffic-009,999.999.1.1,10.0.0.10,80,TCP
traffic-010,192.168.1.20,10.0.0.10,99999,TCP
"""


@router.get("/sample-csv", response_class=PlainTextResponse)
def get_sample_csv():
    """
    Returns sample CSV for user testing.
    """
    return PlainTextResponse(
        content=SAMPLE_CSV_CONTENT,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=boho_traffic_sample.csv"}
    )


@router.post("/upload-and-validate", response_model=TrafficPreviewResponse)
async def upload_and_validate_dataset(file: UploadFile = File(...)):
    """
    Upload and safely parse CSV dataset.
    Validates structure, enforces file size/row limits, and analyzes each record for errors.
    """
    # 1. Check file extension
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Fatal file error: Unsupported file type. Only CSV files (.csv) are accepted in Stage 1."
        )

    # 2. Read bytes and check size limit
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Fatal file error: File size ({len(content_bytes) / 1024:.1f} KB) exceeds maximum limit of {MAX_FILE_SIZE_BYTES / (1024*1024):.0f} MB."
        )
    
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fatal file error: The uploaded CSV file is empty.")

    # 3. Decode text safely
    try:
        text_content = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text_content = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Fatal file error: Unable to decode file. Ensure file is encoded in valid UTF-8 text."
            )

    # 4. Parse CSV
    f = io.StringIO(text_content.strip())
    try:
        reader = csv.DictReader(f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fatal file error: Malformed CSV formatting ({str(e)}).")

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="Fatal file error: CSV file does not contain a valid header row."
        )

    # Normalize headers
    fieldnames_clean = [h.strip().lower() for h in reader.fieldnames if h]
    required_cols = {"source_ip", "destination_ip", "destination_port", "protocol"}
    missing_cols = required_cols - set(fieldnames_clean)

    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Fatal file error: Missing required column(s): {', '.join(sorted(missing_cols))}. "
                   f"CSV must contain: source_ip, destination_ip, destination_port, protocol."
        )

    records: List[Dict[str, Any]] = []
    validation_issues: List[ValidationIssue] = []
    valid_count = 0
    invalid_count = 0

    # Helper mapping case-insensitive
    header_map = {h.strip().lower(): h for h in reader.fieldnames if h}

    row_index = 1  # 1 is header
    for raw_row in reader:
        row_index += 1
        if row_index > MAX_ROW_COUNT + 1:
            raise HTTPException(
                status_code=400,
                detail=f"Fatal file error: Dataset exceeds maximum limit of {MAX_ROW_COUNT} rows."
            )

        # Extract values
        src_ip = raw_row.get(header_map.get("source_ip", ""), "").strip()
        dst_ip = raw_row.get(header_map.get("destination_ip", ""), "").strip()
        dst_port = raw_row.get(header_map.get("destination_port", ""), "").strip()
        proto = raw_row.get(header_map.get("protocol", ""), "").strip()
        
        # Optional record_id
        rec_id = ""
        if "record_id" in header_map:
            rec_id = raw_row.get(header_map["record_id"], "").strip()
        if not rec_id:
            rec_id = f"row-{row_index - 1}"

        parsed_record = TrafficRecordData(
            record_id=rec_id,
            source_ip=src_ip,
            destination_ip=dst_ip,
            destination_port=dst_port if dst_port else None,
            protocol=proto,
        )

        record_errors = validate_record(parsed_record)
        
        record_dict = {
            "row_number": row_index,
            "record_id": rec_id,
            "source_ip": src_ip,
            "destination_ip": dst_ip,
            "destination_port": dst_port or ("N/A" if proto.upper() == "ICMP" else ""),
            "protocol": proto.upper() if proto else "",
            "is_valid": len(record_errors) == 0,
            "errors": record_errors,
        }

        records.append(record_dict)

        if record_errors:
            invalid_count += 1
            validation_issues.append(
                ValidationIssue(
                    row_number=row_index,
                    record_id=rec_id,
                    errors=record_errors
                )
            )
        else:
            valid_count += 1

    if len(records) == 0:
        raise HTTPException(
            status_code=400,
            detail="Fatal file error: The uploaded CSV file has headers but contains no traffic data rows."
        )

    return TrafficPreviewResponse(
        total_records=len(records),
        valid_count=valid_count,
        invalid_count=invalid_count,
        preview_records=records[:100],  # Return up to first 100 for preview
        validation_issues=validation_issues[:50],  # First 50 issues
        file_warning=f"Displaying first {min(100, len(records))} rows in preview. All {len(records)} records will be evaluated during simulation." if len(records) > 100 else None
    )
