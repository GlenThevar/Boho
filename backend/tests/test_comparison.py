import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_policy_comparison_workflow():
    # 1. Setup base firewall rules:
    # Rule 1: Allow TCP 80
    # Rule 2: Allow TCP 443
    client.post("/api/rules", json={
        "name": "Allow HTTP",
        "priority": 10,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.1",
        "destination_port": "80",
        "protocol": "TCP",
        "action": "ALLOW",
        "enabled": True
    })
    client.post("/api/rules", json={
        "name": "Allow HTTPS",
        "priority": 20,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.1",
        "destination_port": "443",
        "protocol": "TCP",
        "action": "ALLOW",
        "enabled": True
    })

    # 2. Run simulation with 3 traffic records:
    # rec-1: TCP 80  -> Originally ALLOWED (Rule 1)
    # rec-2: TCP 443 -> Originally ALLOWED (Rule 2)
    # rec-3: TCP 22  -> Originally DENIED (Default policy)
    sim_res = client.post("/api/simulations", json={
        "simulation_name": "Base Sim",
        "records": [
            {"record_id": "rec-1", "source_ip": "192.168.1.10", "destination_ip": "10.0.0.1", "destination_port": "80", "protocol": "TCP"},
            {"record_id": "rec-2", "source_ip": "192.168.1.10", "destination_ip": "10.0.0.1", "destination_port": "443", "protocol": "TCP"},
            {"record_id": "rec-3", "source_ip": "192.168.1.10", "destination_ip": "10.0.0.1", "destination_port": "22", "protocol": "TCP"},
        ]
    })
    assert sim_res.status_code == 201
    sim_id = sim_res.json()["id"]

    # 3. Test proposed policy comparison:
    # Proposed Changes:
    # - Disable HTTP (rec-1 becomes ALLOW -> DENY)
    # - Add SSH Allow (rec-3 becomes DENY -> ALLOW)
    # - Keep HTTPS Allow (rec-2 remains ALLOW -> ALLOW)
    comp_payload = {
        "simulation_id": sim_id,
        "name": "Audit Proposed Policy",
        "proposed_rules": [
            {
                "name": "Allow HTTPS",
                "priority": 10,
                "source_ip": "ANY",
                "destination_ip": "10.0.0.1",
                "destination_port": "443",
                "protocol": "TCP",
                "action": "ALLOW",
                "enabled": True
            },
            {
                "name": "Allow SSH Management",
                "priority": 20,
                "source_ip": "ANY",
                "destination_ip": "10.0.0.1",
                "destination_port": "22",
                "protocol": "TCP",
                "action": "ALLOW",
                "enabled": True
            }
        ]
    }
    comp_res = client.post("/api/comparisons", json=comp_payload)
    assert comp_res.status_code == 201
    comp_data = comp_res.json()
    comp_id = comp_data["id"]

    # Verify summary counts
    assert comp_data["total_records"] == 3
    assert comp_data["original_allowed"] == 2
    assert comp_data["original_denied"] == 1
    assert comp_data["proposed_allowed"] == 2  # HTTPS + SSH
    assert comp_data["proposed_denied"] == 1   # HTTP (dropped)
    assert comp_data["changed_decisions"] == 2
    assert comp_data["allow_to_deny"] == 1     # rec-1
    assert comp_data["deny_to_allow"] == 1     # rec-3

    # 4. Check detailed comparison endpoint
    detail_res = client.get(f"/api/comparisons/{comp_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["original_rules"]) == 2
    assert len(detail["proposed_rules"]) == 2
    assert len(detail["records"]["items"]) == 3

    # Check individual record classifications
    rec_map = {r["record_id"]: r for r in detail["records"]["items"]}
    assert rec_map["rec-1"]["change_type"] == "ALLOW_TO_DENY"
    assert rec_map["rec-3"]["change_type"] == "DENY_TO_ALLOW"
    assert rec_map["rec-2"]["change_type"] == "SAME_DECISION_DIFFERENT_RULE" or rec_map["rec-2"]["change_type"] == "UNCHANGED"

    # 5. Verify original simulation remains 100% UNCHANGED
    sim_check = client.get(f"/api/simulations/{sim_id}")
    assert sim_check.status_code == 200
    assert sim_check.json()["simulation"]["allowed_records"] == 2
    assert sim_check.json()["simulation"]["denied_records"] == 1


def test_security_findings_dismiss_and_restore():
    # 1. Create a risky rule (Public SSH)
    client.post("/api/rules", json={
        "name": "Public SSH",
        "priority": 10,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.1",
        "destination_port": "22",
        "protocol": "TCP",
        "action": "ALLOW",
        "enabled": True,
        "description": "Rule without business justification"
    })

    # 2. Run analysis
    analysis_res = client.post("/api/analysis/run")
    assert analysis_res.status_code == 201
    analysis_id = analysis_res.json()["id"]

    detail_res = client.get(f"/api/analysis/{analysis_id}")
    assert detail_res.status_code == 200
    findings = detail_res.json()["findings"]
    assert len(findings) > 0

    target_finding = next((f for f in findings if "SEC-MGMT-EXPOSED-22" in f["finding_code"]), None)
    assert target_finding is not None
    assert target_finding["is_dismissed"] is False

    # 3. Dismiss finding
    dismiss_res = client.patch(
        f"/api/analysis/findings/{target_finding['id']}/dismiss",
        json={"reason": "Business exception approved for jumpbox"}
    )
    assert dismiss_res.status_code == 200
    assert dismiss_res.json()["is_dismissed"] is True
    assert dismiss_res.json()["dismissed_reason"] == "Business exception approved for jumpbox"

    # 4. Restore finding
    restore_res = client.patch(f"/api/analysis/findings/{target_finding['id']}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["is_dismissed"] is False
    assert restore_res.json()["dismissed_reason"] is None
