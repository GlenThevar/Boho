import pytest
from app.engine.firewall_engine import FirewallRuleData
from app.engine.policy_analyzer import audit_security_policies


def test_ssh_open_to_any_source_detected():
    rule = FirewallRuleData(
        id=1,
        name="Allow Public SSH",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.5",
        destination_port="22",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    findings = audit_security_policies([rule])
    ssh_findings = [f for f in findings if "SEC-MGMT-EXPOSED-22" in f.finding_code]
    assert len(ssh_findings) == 1
    assert ssh_findings[0].severity == "Critical"
    assert "SSH" in ssh_findings[0].title
    assert ssh_findings[0].rule_id == 1


def test_restricted_ssh_access_not_flagged():
    rule = FirewallRuleData(
        id=2,
        name="Allow Bastion SSH",
        priority=10,
        source_ip="192.168.10.25/32",  # Specific IP, not ANY!
        destination_ip="10.0.0.5",
        destination_port="22",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    findings = audit_security_policies([rule])
    ssh_findings = [f for f in findings if "SEC-MGMT-EXPOSED-22" in f.finding_code]
    assert len(ssh_findings) == 0


def test_broad_allow_rules_detected():
    rule_any_any = FirewallRuleData(
        id=3,
        name="Open Permissive Door",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    findings = audit_security_policies([rule_any_any])
    broad_findings = [f for f in findings if "SEC-BROAD-ALLOW-ALL" in f.finding_code]
    assert len(broad_findings) == 1
    assert broad_findings[0].severity == "Critical"


def test_disabled_risky_rules_ignored():
    rule_disabled = FirewallRuleData(
        id=4,
        name="Disabled Risky SSH",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="22",
        protocol="TCP",
        action="ALLOW",
        enabled=False,  # Disabled
    )
    findings = audit_security_policies([rule_disabled])
    # Disabled rules do not present active risks
    assert len(findings) == 0


def test_protocol_wildcard_with_specific_port_detected():
    rule = FirewallRuleData(
        id=5,
        name="Allow Web on Any Protocol",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.1",
        destination_port="443",
        protocol="ANY",  # Should be TCP
        action="ALLOW",
        enabled=True,
    )
    findings = audit_security_policies([rule])
    proto_findings = [f for f in findings if "SEC-PROTO-WILDCARD-PORT" in f.finding_code]
    assert len(proto_findings) == 1
    assert proto_findings[0].severity == "Medium"
