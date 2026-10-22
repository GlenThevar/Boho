import pytest
from app.engine.firewall_engine import (
    FirewallRuleData,
    TrafficRecordData,
    evaluate_record,
    evaluate_dataset,
    validate_rule,
    validate_record,
    validate_ip_or_cidr,
    validate_port_spec,
    validate_protocol_spec,
)


def test_record_matching_allow_rule():
    rule = FirewallRuleData(
        id=1,
        name="Allow Web Traffic",
        priority=10,
        source_ip="ANY",
        destination_ip="192.168.1.100",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    record = TrafficRecordData(
        record_id="rec-1",
        source_ip="10.0.0.5",
        destination_ip="192.168.1.100",
        destination_port=80,
        protocol="TCP",
    )
    result = evaluate_record(record, [rule])
    assert result.decision == "ALLOW"
    assert result.matched_rule_id == 1
    assert result.is_default_policy is False
    assert "Matched Rule #1" in result.explanation


def test_record_matching_deny_rule():
    rule = FirewallRuleData(
        id=2,
        name="Block Telnet",
        priority=5,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="23",
        protocol="TCP",
        action="DENY",
        enabled=True,
    )
    record = TrafficRecordData(
        record_id="rec-2",
        source_ip="192.168.1.50",
        destination_ip="10.0.0.2",
        destination_port=23,
        protocol="TCP",
    )
    result = evaluate_record(record, [rule])
    assert result.decision == "DENY"
    assert result.matched_rule_id == 2
    assert result.is_default_policy is False
    assert "Action: DENY" in result.explanation


def test_first_match_wins_behavior():
    # Rule 1: Priority 10 -> DENY TCP 443
    # Rule 2: Priority 20 -> ALLOW TCP 443
    rule_deny = FirewallRuleData(
        id=1,
        name="Deny HTTPS First",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="443",
        protocol="TCP",
        action="DENY",
        enabled=True,
    )
    rule_allow = FirewallRuleData(
        id=2,
        name="Allow HTTPS Later",
        priority=20,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="443",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    record = TrafficRecordData(
        record_id="rec-3",
        source_ip="1.1.1.1",
        destination_ip="2.2.2.2",
        destination_port=443,
        protocol="TCP",
    )
    
    # Passing rules in reverse order to ensure priority sorting works
    result = evaluate_record(record, [rule_allow, rule_deny])
    assert result.decision == "DENY"
    assert result.matched_rule_id == 1


def test_record_matching_no_rule_receives_default_deny():
    rule = FirewallRuleData(
        id=1,
        name="Allow DNS",
        priority=1,
        source_ip="ANY",
        destination_ip="8.8.8.8",
        destination_port="53",
        protocol="UDP",
        action="ALLOW",
        enabled=True,
    )
    record = TrafficRecordData(
        record_id="rec-4",
        source_ip="192.168.1.5",
        destination_ip="1.1.1.1",
        destination_port=80,
        protocol="TCP",
    )
    result = evaluate_record(record, [rule])
    assert result.decision == "DENY"
    assert result.matched_rule_id is None
    assert result.is_default_policy is True
    assert "Default policy applied: DENY" in result.explanation


def test_disabled_rules_are_ignored():
    rule_disabled = FirewallRuleData(
        id=1,
        name="Disabled Allow All",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=False,
    )
    rule_enabled = FirewallRuleData(
        id=2,
        name="Enabled Deny All",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="DENY",
        enabled=True,
    )
    record = TrafficRecordData(
        record_id="rec-5",
        source_ip="10.0.0.1",
        destination_ip="10.0.0.2",
        destination_port=80,
        protocol="TCP",
    )
    result = evaluate_record(record, [rule_disabled, rule_enabled])
    assert result.decision == "DENY"
    assert result.matched_rule_id == 2


def test_source_and_destination_ip_matching():
    rule = FirewallRuleData(
        id=5,
        name="Host-to-Host",
        priority=10,
        source_ip="192.168.1.10",
        destination_ip="10.20.30.40",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    # Matching record
    rec_match = TrafficRecordData(
        record_id="r1",
        source_ip="192.168.1.10",
        destination_ip="10.20.30.40",
        destination_port=1234,
        protocol="TCP",
    )
    assert evaluate_record(rec_match, [rule]).decision == "ALLOW"

    # Non-matching source IP
    rec_mismatch_src = TrafficRecordData(
        record_id="r2",
        source_ip="192.168.1.11",
        destination_ip="10.20.30.40",
        destination_port=1234,
        protocol="TCP",
    )
    assert evaluate_record(rec_mismatch_src, [rule]).decision == "DENY"

    # Non-matching destination IP
    rec_mismatch_dst = TrafficRecordData(
        record_id="r3",
        source_ip="192.168.1.10",
        destination_ip="10.20.30.41",
        destination_port=1234,
        protocol="TCP",
    )
    assert evaluate_record(rec_mismatch_dst, [rule]).decision == "DENY"


def test_cidr_range_matching():
    rule = FirewallRuleData(
        id=6,
        name="Subnet Rule",
        priority=5,
        source_ip="172.16.0.0/16",
        destination_ip="10.0.0.0/24",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    
    # In-range record
    rec_in = TrafficRecordData(
        record_id="r-cidr-1",
        source_ip="172.16.100.45",
        destination_ip="10.0.0.254",
        destination_port=80,
        protocol="TCP",
    )
    assert evaluate_record(rec_in, [rule]).decision == "ALLOW"

    # Out-of-range record
    rec_out = TrafficRecordData(
        record_id="r-cidr-2",
        source_ip="172.17.0.1",
        destination_ip="10.0.0.1",
        destination_port=80,
        protocol="TCP",
    )
    assert evaluate_record(rec_out, [rule]).decision == "DENY"


def test_port_and_port_range_matching():
    rule_range = FirewallRuleData(
        id=7,
        name="Web Ports Range",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="8000-8080",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    
    # Inside port range
    rec_in = TrafficRecordData(
        record_id="r-p1",
        source_ip="1.1.1.1",
        destination_ip="2.2.2.2",
        destination_port=8000,
        protocol="TCP",
    )
    assert evaluate_record(rec_in, [rule_range]).decision == "ALLOW"

    rec_in_mid = TrafficRecordData(
        record_id="r-p2",
        source_ip="1.1.1.1",
        destination_ip="2.2.2.2",
        destination_port=8040,
        protocol="TCP",
    )
    assert evaluate_record(rec_in_mid, [rule_range]).decision == "ALLOW"

    rec_in_end = TrafficRecordData(
        record_id="r-p3",
        source_ip="1.1.1.1",
        destination_ip="2.2.2.2",
        destination_port=8080,
        protocol="TCP",
    )
    assert evaluate_record(rec_in_end, [rule_range]).decision == "ALLOW"

    # Outside port range
    rec_out = TrafficRecordData(
        record_id="r-p4",
        source_ip="1.1.1.1",
        destination_ip="2.2.2.2",
        destination_port=8081,
        protocol="TCP",
    )
    assert evaluate_record(rec_out, [rule_range]).decision == "DENY"


def test_protocol_matching_and_any():
    rule_any_proto = FirewallRuleData(
        id=8,
        name="Allow Any Proto",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    rec_tcp = TrafficRecordData("r-tcp", "1.1.1.1", "2.2.2.2", 80, "tcp")
    rec_udp = TrafficRecordData("r-udp", "1.1.1.1", "2.2.2.2", 53, "UDP")
    rec_icmp = TrafficRecordData("r-icmp", "1.1.1.1", "2.2.2.2", None, "ICMP")

    assert evaluate_record(rec_tcp, [rule_any_proto]).decision == "ALLOW"
    assert evaluate_record(rec_udp, [rule_any_proto]).decision == "ALLOW"
    assert evaluate_record(rec_icmp, [rule_any_proto]).decision == "ALLOW"


def test_icmp_records_without_destination_ports():
    rule_icmp = FirewallRuleData(
        id=9,
        name="Allow ICMP Ping",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ICMP",
        action="ALLOW",
        enabled=True,
    )
    rec_icmp_no_port = TrafficRecordData(
        record_id="icmp-1",
        source_ip="192.168.1.1",
        destination_ip="8.8.8.8",
        destination_port="",  # Empty port
        protocol="ICMP",
    )
    res = evaluate_record(rec_icmp_no_port, [rule_icmp])
    assert res.decision == "ALLOW"
    assert res.matched_rule_id == 9


def test_invalid_ip_addresses_and_ports():
    rule = FirewallRuleData(
        id=10,
        name="Catch All",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    # Invalid source IP
    rec_bad_ip = TrafficRecordData(
        record_id="bad-ip",
        source_ip="999.999.999.999",
        destination_ip="10.0.0.1",
        destination_port=80,
        protocol="TCP",
    )
    res_ip = evaluate_record(rec_bad_ip, [rule])
    assert res_ip.decision == "DENY"
    assert len(res_ip.validation_errors) > 0
    assert "Invalid source IP address" in res_ip.explanation

    # Invalid port (out of range)
    rec_bad_port = TrafficRecordData(
        record_id="bad-port",
        source_ip="10.0.0.1",
        destination_ip="10.0.0.2",
        destination_port=70000,
        protocol="TCP",
    )
    res_port = evaluate_record(rec_bad_port, [rule])
    assert res_port.decision == "DENY"
    assert len(res_port.validation_errors) > 0
    assert "outside valid range" in res_port.explanation


def test_overlapping_rules_with_different_priorities():
    # Specific rule (Priority 5) allows 192.168.1.100 to 10.0.0.1
    # Broad rule (Priority 15) blocks 192.168.1.0/24 to 10.0.0.0/24
    rule_specific = FirewallRuleData(
        id=11,
        name="Allow Specific Host",
        priority=5,
        source_ip="192.168.1.100",
        destination_ip="10.0.0.1",
        destination_port="ANY",
        protocol="ANY",
        action="ALLOW",
        enabled=True,
    )
    rule_broad = FirewallRuleData(
        id=12,
        name="Block Entire Subnet",
        priority=15,
        source_ip="192.168.1.0/24",
        destination_ip="10.0.0.0/24",
        destination_port="ANY",
        protocol="ANY",
        action="DENY",
        enabled=True,
    )
    
    # Specific host matches rule 11 first and is allowed
    rec_specific = TrafficRecordData("s1", "192.168.1.100", "10.0.0.1", 443, "TCP")
    res1 = evaluate_record(rec_specific, [rule_broad, rule_specific])
    assert res1.decision == "ALLOW"
    assert res1.matched_rule_id == 11

    # Another host in the subnet matches rule 12 and is denied
    rec_other = TrafficRecordData("s2", "192.168.1.101", "10.0.0.1", 443, "TCP")
    res2 = evaluate_record(rec_other, [rule_broad, rule_specific])
    assert res2.decision == "DENY"
    assert res2.matched_rule_id == 12


def test_rule_validation():
    # Blank fields are not allowed silently as wildcards
    bad_rule = FirewallRuleData(
        id=None,
        name="",
        priority=0,
        source_ip="",
        destination_ip="",
        destination_port="",
        protocol="UNKNOWN",
        action="FORWARD",
    )
    errors = validate_rule(bad_rule)
    assert any("name cannot be blank" in e for e in errors)
    assert any("priority must be a positive integer" in e for e in errors)
    assert any("Source IP cannot be blank" in e for e in errors)
    assert any("Destination IP cannot be blank" in e for e in errors)
    assert any("Port cannot be blank" in e for e in errors)
    assert any("Invalid protocol" in e for e in errors)
    assert any("Invalid action" in e for e in errors)
