import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create an in-memory SQLite database for test isolation
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


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_rule_crud_operations():
    # 1. Create rule
    payload = {
        "name": "Allow Web HTTPS",
        "priority": 10,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.1",
        "destination_port": "443",
        "protocol": "TCP",
        "action": "ALLOW",
        "enabled": True,
        "description": "HTTPS Rule"
    }
    res = client.post("/api/rules", json=payload)
    assert res.status_code == 201
    data = res.json()
    rule_id = data["id"]
    assert data["name"] == "Allow Web HTTPS"
    assert data["priority"] == 10

    # 2. List rules
    list_res = client.get("/api/rules")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. Toggle rule
    toggle_res = client.patch(f"/api/rules/{rule_id}/toggle", json={"enabled": False})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["enabled"] is False

    # 4. Update rule
    payload["name"] = "Allow Web HTTPS Updated"
    payload["enabled"] = True
    put_res = client.put(f"/api/rules/{rule_id}", json=payload)
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "Allow Web HTTPS Updated"

    # 5. Delete rule
    del_res = client.delete(f"/api/rules/{rule_id}")
    assert del_res.status_code == 204
    assert len(client.get("/api/rules").json()) == 0


def test_rule_validation_rejects_blank_and_invalid():
    # Blank source IP should fail
    bad_payload = {
        "name": "Bad Rule",
        "priority": 1,
        "source_ip": "   ",
        "destination_ip": "ANY",
        "destination_port": "80",
        "protocol": "TCP",
        "action": "ALLOW",
    }
    res = client.post("/api/rules", json=bad_payload)
    assert res.status_code == 422

    # Port start > end should fail
    bad_port = {
        "name": "Bad Port Range",
        "priority": 1,
        "source_ip": "ANY",
        "destination_ip": "ANY",
        "destination_port": "8080-8000",
        "protocol": "TCP",
        "action": "ALLOW",
    }
    res2 = client.post("/api/rules", json=bad_port)
    assert res2.status_code == 422


def test_simulation_workflow_and_snapshot_preservation():
    """
    Critical test:
    1. Create rule allowing TCP 80.
    2. Run simulation with 2 records (1 allowed, 1 default deny).
    3. Modify or delete the rule.
    4. Verify that historical simulation rule snapshot and record decisions remain unchanged!
    """
    # 1. Create rule
    rule_res = client.post("/api/rules", json={
        "name": "Original Allow Web",
        "priority": 5,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.50",
        "destination_port": "80",
        "protocol": "TCP",
        "action": "ALLOW",
        "enabled": True,
    })
    rule_id = rule_res.json()["id"]

    # 2. Run simulation
    sim_payload = {
        "simulation_name": "Test Sim 1",
        "records": [
            {
                "record_id": "r1",
                "source_ip": "192.168.1.5",
                "destination_ip": "10.0.0.50",
                "destination_port": "80",
                "protocol": "TCP"
            },
            {
                "record_id": "r2",
                "source_ip": "192.168.1.6",
                "destination_ip": "10.0.0.50",
                "destination_port": "22",
                "protocol": "TCP"
            }
        ]
    }
    sim_res = client.post("/api/simulations", json=sim_payload)
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    sim_id = sim_data["id"]
    assert sim_data["allowed_records"] == 1
    assert sim_data["denied_records"] == 1

    # Inspect simulation detail
    detail_res = client.get(f"/api/simulations/{sim_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["rules_snapshot"]) == 1
    assert detail["rules_snapshot"][0]["name"] == "Original Allow Web"
    assert detail["rules_snapshot"][0]["destination_port"] == "80"

    # 3. Edit current rule completely (change port to 443 and action to DENY)
    client.put(f"/api/rules/{rule_id}", json={
        "name": "Modified Rule Deny 443",
        "priority": 99,
        "source_ip": "ANY",
        "destination_ip": "10.0.0.50",
        "destination_port": "443",
        "protocol": "TCP",
        "action": "DENY",
        "enabled": False,
    })

    # 4. Verify historical simulation results remain 100% unchanged!
    hist_res = client.get(f"/api/simulations/{sim_id}")
    assert hist_res.status_code == 200
    hist_detail = hist_res.json()
    # Still 1 allowed, 1 denied
    assert hist_detail["simulation"]["allowed_records"] == 1
    assert hist_detail["simulation"]["denied_records"] == 1
    # Snapshot still has the original rule values
    assert hist_detail["rules_snapshot"][0]["name"] == "Original Allow Web"
    assert hist_detail["rules_snapshot"][0]["destination_port"] == "80"
    assert hist_detail["rules_snapshot"][0]["action"] == "ALLOW"
    assert hist_detail["rules_snapshot"][0]["enabled"] is True


def test_simulation_filtering_and_csv_export():
    # Run a simulation
    sim_res = client.post("/api/simulations", json={
        "simulation_name": "Export Sim",
        "records": [
            {"record_id": "r1", "source_ip": "1.1.1.1", "destination_ip": "2.2.2.2", "destination_port": "80", "protocol": "TCP"},
            {"record_id": "r2", "source_ip": "3.3.3.3", "destination_ip": "4.4.4.4", "destination_port": "53", "protocol": "UDP"},
        ]
    })
    sim_id = sim_res.json()["id"]

    # Test filtering by protocol
    filter_res = client.get(f"/api/simulations/{sim_id}?protocol=UDP")
    assert filter_res.status_code == 200
    assert len(filter_res.json()["records"]["items"]) == 1
    assert filter_res.json()["records"]["items"][0]["protocol"] == "UDP"

    # Test export CSV
    csv_res = client.get(f"/api/simulations/{sim_id}/export")
    assert csv_res.status_code == 200
    assert "Record ID,Source IP,Destination IP" in csv_res.text
    assert "r1,1.1.1.1,2.2.2.2" in csv_res.text
