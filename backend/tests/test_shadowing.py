import pytest
from app.engine.firewall_engine import FirewallRuleData
from app.engine.policy_analyzer import detect_shadowing, does_rule_cover


def test_rule_fully_shadowed_by_earlier_any_rule():
    rule1 = FirewallRuleData(
        id=1,
        name="Block All",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="DENY",
        enabled=True,
    )
    rule2 = FirewallRuleData(
        id=2,
        name="Allow HTTPS",
        priority=10,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="443",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, inconclusive = detect_shadowing([rule1, rule2])
    assert len(findings) == 1
    assert findings[0].rule_id == 2
    assert findings[0].shadowing_rule_ids == [1]
    assert findings[0].is_conflict is True
    assert findings[0].severity == "Critical"
    assert "Rule #10" in findings[0].explanation or "Rule #1" in findings[0].explanation


def test_partially_overlapping_rule_not_shadowed():
    # Rule 1: Covers port 80
    # Rule 2: Covers port 80-443 (wider than rule 1)
    rule1 = FirewallRuleData(
        id=1,
        name="Allow HTTP",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.1",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    rule2 = FirewallRuleData(
        id=2,
        name="Allow Web Range",
        priority=20,
        source_ip="ANY",
        destination_ip="10.0.0.1",
        destination_port="80-443",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, _ = detect_shadowing([rule1, rule2])
    # Rule 2 is NOT fully shadowed because ports 81-443 can still match Rule 2!
    assert len(findings) == 0


def test_disabled_rules_ignored_in_shadowing():
    rule_disabled = FirewallRuleData(
        id=1,
        name="Disabled Catch All",
        priority=1,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="ANY",
        protocol="ANY",
        action="DENY",
        enabled=False,  # Disabled!
    )
    rule_active = FirewallRuleData(
        id=2,
        name="Active Web",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.1",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, _ = detect_shadowing([rule_disabled, rule_active])
    assert len(findings) == 0


def test_priority_changes_alter_shadowing_result():
    # When rule_specific is priority 5 and rule_broad is priority 15,
    # neither is fully shadowed because rule_specific matches first,
    # and rule_broad covers other addresses.
    rule_specific = FirewallRuleData(
        id=1,
        name="Specific Host",
        priority=5,
        source_ip="ANY",
        destination_ip="10.0.0.5",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    rule_broad = FirewallRuleData(
        id=2,
        name="Broad Subnet",
        priority=15,
        source_ip="ANY",
        destination_ip="10.0.0.0/24",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, _ = detect_shadowing([rule_specific, rule_broad])
    assert len(findings) == 0

    # Invert priority: rule_broad is Priority 5, rule_specific is Priority 15
    rule_broad.priority = 5
    rule_specific.priority = 15

    findings_inverted, _ = detect_shadowing([rule_broad, rule_specific])
    # Now rule_specific is fully shadowed by rule_broad!
    assert len(findings_inverted) == 1
    assert findings_inverted[0].rule_id == 1
    assert findings_inverted[0].shadowing_rule_ids == [2]


def test_protocol_and_port_range_boundaries():
    # Rule 1: TCP 8000-9000
    # Rule 2: TCP 8050-8090 (within boundaries) -> Shadowed
    # Rule 3: TCP 8900-9100 (crosses upper boundary) -> Not shadowed
    # Rule 4: UDP 8000-9000 (different protocol) -> Not shadowed
    rule1 = FirewallRuleData(id=1, name="R1", priority=1, source_ip="ANY", destination_ip="ANY", destination_port="8000-9000", protocol="TCP", action="ALLOW", enabled=True)
    rule2 = FirewallRuleData(id=2, name="R2", priority=2, source_ip="ANY", destination_ip="ANY", destination_port="8050-8090", protocol="TCP", action="ALLOW", enabled=True)
    rule3 = FirewallRuleData(id=3, name="R3", priority=3, source_ip="ANY", destination_ip="ANY", destination_port="8900-9100", protocol="TCP", action="ALLOW", enabled=True)
    rule4 = FirewallRuleData(id=4, name="R4", priority=4, source_ip="ANY", destination_ip="ANY", destination_port="8000-9000", protocol="UDP", action="ALLOW", enabled=True)

    findings, _ = detect_shadowing([rule1, rule2, rule3, rule4])
    shadowed_ids = [f.rule_id for f in findings]
    assert 2 in shadowed_ids
    assert 3 not in shadowed_ids
    assert 4 not in shadowed_ids
