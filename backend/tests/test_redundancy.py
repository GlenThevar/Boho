import pytest
from app.engine.firewall_engine import FirewallRuleData
from app.engine.policy_analyzer import detect_redundancy


def test_genuinely_redundant_rule_earlier_same_action():
    # Rule 1: Allow TCP 443 to 10.0.0.0/24
    # Rule 2: Allow TCP 443 to 10.0.0.50 (same action, completely covered by Rule 1)
    rule1 = FirewallRuleData(
        id=1,
        name="Allow Subnet HTTPS",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.0/24",
        destination_port="443",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )
    rule2 = FirewallRuleData(
        id=2,
        name="Allow Host HTTPS",
        priority=20,
        source_ip="ANY",
        destination_ip="10.0.0.50",
        destination_port="443",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, _ = detect_redundancy([rule1, rule2])
    assert len(findings) == 1
    assert findings[0].rule_id == 2
    assert findings[0].redundancy_type == "EARLIER_SAME_ACTION"
    assert findings[0].equivalent_rule_ids == [1]


def test_rule_with_different_action_is_not_redundant():
    # Rule 1: Deny all to 10.0.0.0/24
    # Rule 2: Allow to 10.0.0.50 (different action: this is a conflict shadow, NOT redundant in behavior)
    rule1 = FirewallRuleData(
        id=1,
        name="Block Subnet",
        priority=10,
        source_ip="ANY",
        destination_ip="10.0.0.0/24",
        destination_port="ANY",
        protocol="ANY",
        action="DENY",
        enabled=True,
    )
    rule2 = FirewallRuleData(
        id=2,
        name="Allow Host",
        priority=20,
        source_ip="ANY",
        destination_ip="10.0.0.50",
        destination_port="80",
        protocol="TCP",
        action="ALLOW",
        enabled=True,
    )

    findings, _ = detect_redundancy([rule1, rule2])
    # Rule 2 is NOT redundant because its intended action is ALLOW, which differs from Rule 1's action DENY.
    # (It is shadowed, but not redundant).
    redundant_ids = [f.rule_id for f in findings]
    assert 2 not in redundant_ids


def test_rule_that_affects_traffic_cannot_be_removed():
    # Rule 1: Allow TCP 80
    # Rule 2: Allow TCP 443
    rule1 = FirewallRuleData(id=1, name="HTTP", priority=1, source_ip="ANY", destination_ip="10.0.0.1", destination_port="80", protocol="TCP", action="ALLOW", enabled=True)
    rule2 = FirewallRuleData(id=2, name="HTTPS", priority=2, source_ip="ANY", destination_ip="10.0.0.1", destination_port="443", protocol="TCP", action="ALLOW", enabled=True)

    findings, _ = detect_redundancy([rule1, rule2])
    # Neither rule is redundant; both affect different ports!
    assert len(findings) == 0


def test_default_policy_deny_redundancy():
    # If the firewall has an explicit DENY rule and NO subsequent rules exist with ALLOW,
    # the rule is functionally equivalent to the default DENY policy.
    rule_deny = FirewallRuleData(
        id=5,
        name="Explicit Deny Telnet",
        priority=50,
        source_ip="ANY",
        destination_ip="ANY",
        destination_port="23",
        protocol="TCP",
        action="DENY",
        enabled=True,
    )

    findings, _ = detect_redundancy([rule_deny])
    assert len(findings) == 1
    assert findings[0].rule_id == 5
    assert findings[0].redundancy_type == "DEFAULT_POLICY_DENY"
