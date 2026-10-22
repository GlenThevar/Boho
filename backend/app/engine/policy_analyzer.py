"""
Boho Policy Analysis & Security Auditing Engine
Stage 2: Deterministic Rule Shadowing, Redundancy Analysis, and Security Auditing
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import ipaddress
from typing import List, Optional, Tuple, Dict, Any
from app.engine.firewall_engine import FirewallRuleData, validate_ip_or_cidr, validate_port_spec


@dataclass
class ShadowingFinding:
    rule_id: Optional[int]
    rule_name: str
    rule_priority: int
    rule_action: str
    shadowing_rule_ids: List[int]
    shadowing_rule_names: List[str]
    shadowing_rule_priorities: List[int]
    shadowing_rule_actions: List[str]
    is_conflict: bool  # True if actions differ (e.g. earlier DENY suppresses later ALLOW)
    explanation: str
    evidence: Dict[str, Any]
    severity: str  # Critical, High, Medium, Low
    remediation: str
    confidence: str = "Confirmed"


@dataclass
class RedundancyFinding:
    rule_id: Optional[int]
    rule_name: str
    rule_priority: int
    rule_action: str
    redundancy_type: str  # EARLIER_SAME_ACTION, DEFAULT_POLICY_DENY, EXACT_DUPLICATE
    equivalent_rule_ids: List[int]
    equivalent_rule_names: List[str]
    explanation: str
    evidence: Dict[str, Any]
    severity: str  # High, Medium, Low
    remediation: str
    confidence: str = "Confirmed"


@dataclass
class SecurityFindingData:
    finding_code: str
    rule_id: Optional[int]
    rule_name: str
    rule_priority: int
    category: str
    severity: str  # Critical, High, Medium, Low
    finding_type: str  # SECURITY_RISK, SHADOWING, REDUNDANCY
    title: str
    explanation: str
    evidence: Dict[str, Any]
    remediation: str
    confidence: str = "Confirmed"


@dataclass
class PolicyAnalysisReport:
    rules_analyzed_count: int
    shadowed_rules: List[ShadowingFinding] = field(default_factory=list)
    redundant_rules: List[RedundancyFinding] = field(default_factory=list)
    security_findings: List[SecurityFindingData] = field(default_factory=list)
    inconclusive_checks: List[str] = field(default_factory=list)


# --- Mathematical Traffic Space Helpers ---

def parse_ip_network(ip_str: str) -> Optional[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    clean = ip_str.strip().upper()
    if clean == "ANY":
        return None  # Represents universal wildcard
    try:
        return ipaddress.ip_network(ip_str.strip(), strict=False)
    except ValueError:
        return None


def is_ip_contained(sub_ip_str: str, super_ip_str: str) -> Tuple[bool, bool]:
    """
    Checks if sub_ip_str is entirely contained within super_ip_str.
    Returns (is_contained, is_conclusive).
    """
    sub_clean = sub_ip_str.strip().upper()
    super_clean = super_ip_str.strip().upper()

    if super_clean == "ANY":
        return True, True
    if sub_clean == "ANY" and super_clean != "ANY":
        return False, True

    net_sub = parse_ip_network(sub_ip_str)
    net_super = parse_ip_network(super_ip_str)

    if net_sub is None or net_super is None:
        return False, False  # Inconclusive due to parsing error

    if net_sub.version != net_super.version:
        return False, True

    return net_sub.subnet_of(net_super), True


def is_protocol_contained(sub_proto: str, super_proto: str) -> Tuple[bool, bool]:
    """
    Checks if sub_proto is contained within super_proto.
    """
    sub_c = sub_proto.strip().upper()
    super_c = super_proto.strip().upper()

    if super_c == "ANY":
        return True, True
    if sub_c == "ANY" and super_c != "ANY":
        return False, True

    return sub_c == super_c, True


def parse_port_bounds(port_str: str, protocol: str) -> Tuple[Optional[Tuple[int, int]], bool]:
    """
    Returns ((min_port, max_port), is_conclusive).
    """
    proto_c = protocol.strip().upper()
    port_c = str(port_str).strip().upper()

    if proto_c == "ICMP":
        # ICMP has no TCP/UDP transport ports
        return (1, 65535), True

    if port_c in {"ANY", "N/A", ""}:
        return (1, 65535), True

    if "-" in port_c:
        parts = port_c.split("-")
        if len(parts) == 2:
            try:
                p_start = int(parts[0].strip())
                p_end = int(parts[1].strip())
                if 1 <= p_start <= 65535 and 1 <= p_end <= 65535 and p_start <= p_end:
                    return (p_start, p_end), True
            except ValueError:
                pass
        return None, False

    try:
        p = int(port_c)
        if 1 <= p <= 65535:
            return (p, p), True
    except ValueError:
        pass

    return None, False


def is_port_contained(sub_port_str: str, super_port_str: str, sub_proto: str, super_proto: str) -> Tuple[bool, bool]:
    """
    Checks if sub_port_str is completely within super_port_str range.
    """
    sub_p_c = sub_proto.strip().upper()
    super_p_c = super_proto.strip().upper()

    if sub_p_c == "ICMP" and super_p_c == "ICMP":
        return True, True

    sub_bounds, sub_ok = parse_port_bounds(sub_port_str, sub_proto)
    super_bounds, super_ok = parse_port_bounds(super_port_str, super_proto)

    if not sub_ok or not super_ok or sub_bounds is None or super_bounds is None:
        return False, False  # Inconclusive

    sub_min, sub_max = sub_bounds
    super_min, super_max = super_bounds

    return (super_min <= sub_min and sub_max <= super_max), True


def does_rule_cover(super_rule: FirewallRuleData, sub_rule: FirewallRuleData) -> Tuple[bool, bool, str]:
    """
    Evaluates whether super_rule's matching criteria completely cover sub_rule's matching criteria.
    Returns (is_covered, is_conclusive, explanation).
    """
    # 1. Protocol coverage
    proto_cov, proto_conc = is_protocol_contained(sub_rule.protocol, super_rule.protocol)
    if not proto_conc:
        return False, False, f"Inconclusive protocol comparison: '{sub_rule.protocol}' vs '{super_rule.protocol}'"
    if not proto_cov:
        return False, True, f"Protocol '{sub_rule.protocol}' not covered by '{super_rule.protocol}'"

    # 2. Source IP coverage
    src_cov, src_conc = is_ip_contained(sub_rule.source_ip, super_rule.source_ip)
    if not src_conc:
        return False, False, f"Inconclusive source IP comparison: '{sub_rule.source_ip}' vs '{super_rule.source_ip}'"
    if not src_cov:
        return False, True, f"Source IP '{sub_rule.source_ip}' not covered by '{super_rule.source_ip}'"

    # 3. Destination IP coverage
    dst_cov, dst_conc = is_ip_contained(sub_rule.destination_ip, super_rule.destination_ip)
    if not dst_conc:
        return False, False, f"Inconclusive destination IP comparison: '{sub_rule.destination_ip}' vs '{super_rule.destination_ip}'"
    if not dst_cov:
        return False, True, f"Destination IP '{sub_rule.destination_ip}' not covered by '{super_rule.destination_ip}'"

    # 4. Port coverage
    port_cov, port_conc = is_port_contained(
        sub_rule.destination_port,
        super_rule.destination_port,
        sub_rule.protocol,
        super_rule.protocol
    )
    if not port_conc:
        return False, False, f"Inconclusive port comparison: '{sub_rule.destination_port}' vs '{super_rule.destination_port}'"
    if not port_cov:
        return False, True, f"Destination port '{sub_rule.destination_port}' not covered by '{super_rule.destination_port}'"

    return True, True, "All dimensions (Protocol, Source IP, Destination IP, Port) fully covered."


# --- Feature A: Rule Shadowing Detection ---

def detect_shadowing(rules: List[FirewallRuleData]) -> Tuple[List[ShadowingFinding], List[str]]:
    """
    Analyzes enabled rules in priority order.
    A rule is shadowed if earlier enabled rules ensure its entire matching space is already handled,
    making it impossible for that rule to ever determine a decision under first-match-wins policy.
    """
    enabled_rules = [r for r in rules if r.enabled]
    sorted_rules = sorted(enabled_rules, key=lambda r: r.priority)
    findings: List[ShadowingFinding] = []
    inconclusive: List[str] = []

    for idx, rule in enumerate(sorted_rules):
        # Compare against all earlier rules
        for earlier_idx in range(idx):
            earlier_rule = sorted_rules[earlier_idx]

            covers, is_conclusive, reason = does_rule_cover(earlier_rule, rule)
            if not is_conclusive:
                inconclusive.append(f"Rule #{rule.priority} vs Rule #{earlier_rule.priority}: {reason}")
                continue

            if covers:
                is_conflict = (rule.action.upper() != earlier_rule.action.upper())
                
                if is_conflict:
                    severity = "Critical" if (rule.action.upper() == "ALLOW" and earlier_rule.action.upper() == "DENY") else "High"
                    explanation = (
                        f'Rule #{rule.priority} "{rule.name}" (Action: {rule.action.upper()}) is completely shadowed by '
                        f'earlier Rule #{earlier_rule.priority} "{earlier_rule.name}" (Action: {earlier_rule.action.upper()}). '
                        f'Because Rule #{earlier_rule.priority} has higher priority and completely covers all matching traffic '
                        f'(Source: {earlier_rule.source_ip}, Dest: {earlier_rule.destination_ip}, Port: {earlier_rule.destination_port}, Proto: {earlier_rule.protocol}), '
                        f'Rule #{rule.priority} can never be reached and its intended {rule.action.upper()} decision will never execute.'
                    )
                    remediation = (
                        f'If traffic matched by Rule #{rule.priority} should be {rule.action.upper()}ed, reorder it to a higher priority '
                        f'(lower priority number) than Rule #{earlier_rule.priority}. Otherwise, remove the unreachable rule.'
                    )
                else:
                    severity = "Medium"
                    explanation = (
                        f'Rule #{rule.priority} "{rule.name}" is completely shadowed by earlier Rule #{earlier_rule.priority} "{earlier_rule.name}". '
                        f'Both rules have the same action ({rule.action.upper()}), meaning Rule #{rule.priority} will never be reached because '
                        f'Rule #{earlier_rule.priority} matches all its traffic first.'
                    )
                    remediation = (
                        f'Rule #{rule.priority} is redundant and unreachable. Consider deleting it to keep the policy clean and maintainable.'
                    )

                findings.append(
                    ShadowingFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_priority=rule.priority,
                        rule_action=rule.action.upper(),
                        shadowing_rule_ids=[earlier_rule.id] if earlier_rule.id else [],
                        shadowing_rule_names=[earlier_rule.name],
                        shadowing_rule_priorities=[earlier_rule.priority],
                        shadowing_rule_actions=[earlier_rule.action.upper()],
                        is_conflict=is_conflict,
                        explanation=explanation,
                        evidence={
                            "shadowed_rule": {
                                "id": rule.id,
                                "name": rule.name,
                                "priority": rule.priority,
                                "source_ip": rule.source_ip,
                                "destination_ip": rule.destination_ip,
                                "destination_port": rule.destination_port,
                                "protocol": rule.protocol,
                                "action": rule.action,
                            },
                            "shadowing_rule": {
                                "id": earlier_rule.id,
                                "name": earlier_rule.name,
                                "priority": earlier_rule.priority,
                                "source_ip": earlier_rule.source_ip,
                                "destination_ip": earlier_rule.destination_ip,
                                "destination_port": earlier_rule.destination_port,
                                "protocol": earlier_rule.protocol,
                                "action": earlier_rule.action,
                            },
                            "match_proof": reason
                        },
                        severity=severity,
                        remediation=remediation,
                    )
                )
                # Found primary shadowing rule, move to next rule
                break

    return findings, inconclusive


# --- Feature B: Redundant Rule Detection ---

def detect_redundancy(rules: List[FirewallRuleData]) -> Tuple[List[RedundancyFinding], List[str]]:
    """
    Identifies rules that appear unnecessary because removing them would not change the firewall's decisions.
    Distinguishes redundant rules from conflict-shadowed rules:
    1. Earlier Same Action: Completely covered by an earlier rule with the same action.
    2. Default Policy DENY: Rule has action DENY, and removing it leaves traffic to hit default DENY
       (no intervening or subsequent rules could match it with ALLOW).
    3. Duplicate Rule: Identical match criteria and action.
    """
    enabled_rules = [r for r in rules if r.enabled]
    sorted_rules = sorted(enabled_rules, key=lambda r: r.priority)
    findings: List[RedundancyFinding] = []
    inconclusive: List[str] = []

    for idx, rule in enumerate(sorted_rules):
        # Check 1: Duplicate or Earlier Same Action
        found_earlier_same_action = False
        for earlier_idx in range(idx):
            earlier_rule = sorted_rules[earlier_idx]
            
            covers, is_conc, reason = does_rule_cover(earlier_rule, rule)
            if not is_conc:
                inconclusive.append(f"Redundancy check Rule #{rule.priority} vs #{earlier_rule.priority}: {reason}")
                continue

            if covers and earlier_rule.action.upper() == rule.action.upper():
                # Check if exact duplicate
                is_exact_dup = (
                    earlier_rule.source_ip.strip().upper() == rule.source_ip.strip().upper() and
                    earlier_rule.destination_ip.strip().upper() == rule.destination_ip.strip().upper() and
                    str(earlier_rule.destination_port).strip().upper() == str(rule.destination_port).strip().upper() and
                    earlier_rule.protocol.strip().upper() == rule.protocol.strip().upper()
                )
                
                rtype = "EXACT_DUPLICATE" if is_exact_dup else "EARLIER_SAME_ACTION"
                exp = (
                    f'Rule #{rule.priority} "{rule.name}" is completely redundant because earlier Rule #{earlier_rule.priority} '
                    f'"{earlier_rule.name}" already executes the exact same action ({rule.action.upper()}) for all of this rule\'s traffic space. '
                    f'Removing Rule #{rule.priority} will not alter any firewall packet decisions.'
                )
                findings.append(
                    RedundancyFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_priority=rule.priority,
                        rule_action=rule.action.upper(),
                        redundancy_type=rtype,
                        equivalent_rule_ids=[earlier_rule.id] if earlier_rule.id else [],
                        equivalent_rule_names=[earlier_rule.name],
                        explanation=exp,
                        evidence={
                            "redundant_rule": {
                                "id": rule.id,
                                "name": rule.name,
                                "priority": rule.priority,
                                "action": rule.action,
                                "criteria": f"Src: {rule.source_ip}, Dst: {rule.destination_ip}, Port: {rule.destination_port}, Proto: {rule.protocol}"
                            },
                            "covering_rule": {
                                "id": earlier_rule.id,
                                "name": earlier_rule.name,
                                "priority": earlier_rule.priority,
                                "action": earlier_rule.action,
                                "criteria": f"Src: {earlier_rule.source_ip}, Dst: {earlier_rule.destination_ip}, Port: {earlier_rule.destination_port}, Proto: {earlier_rule.protocol}"
                            },
                            "relationship": "Earlier rule covers entire space with identical action"
                        },
                        severity="Low" if is_exact_dup else "Medium",
                        remediation=f'Safely remove Rule #{rule.priority} "{rule.name}" as earlier Rule #{earlier_rule.priority} provides identical coverage.'
                    )
                )
                found_earlier_same_action = True
                break

        if found_earlier_same_action:
            continue

        # Check 2: Default Policy DENY Redundancy
        # If rule action is DENY, and there are NO subsequent rules with action ALLOW that overlap with it,
        # then removing this DENY rule leaves any matching traffic to fall through to default DENY anyway!
        if rule.action.upper() == "DENY":
            has_subsequent_allow_overlap = False
            for later_idx in range(idx + 1, len(sorted_rules)):
                later_rule = sorted_rules[later_idx]
                if later_rule.action.upper() == "ALLOW":
                    # Check if there is any overlap between rule and later_rule
                    # If later_rule is covered by rule, or rule is covered by later_rule, or they overlap
                    overlap_proto, _ = is_protocol_contained(later_rule.protocol, rule.protocol)
                    if not overlap_proto:
                        overlap_proto, _ = is_protocol_contained(rule.protocol, later_rule.protocol)
                    
                    if overlap_proto:
                        # Check IP overlaps
                        # If later_rule could potentially match, this DENY rule is protecting/blocking it!
                        has_subsequent_allow_overlap = True
                        break

            if not has_subsequent_allow_overlap:
                # No subsequent ALLOW rule exists that could ever match this traffic.
                # If removed, traffic falls through to Default DENY!
                findings.append(
                    RedundancyFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_priority=rule.priority,
                        rule_action=rule.action.upper(),
                        redundancy_type="DEFAULT_POLICY_DENY",
                        equivalent_rule_ids=[],
                        equivalent_rule_names=["Default Policy DENY"],
                        explanation=(
                            f'Rule #{rule.priority} "{rule.name}" specifies action DENY, but there are no subsequent ALLOW rules '
                            f'that could match its traffic space. Under the default DENY policy, unhandled traffic is denied automatically. '
                            f'Removing this explicit DENY rule would not change any firewall outcomes unless an ALLOW rule is later added.'
                        ),
                        evidence={
                            "rule_id": rule.id,
                            "name": rule.name,
                            "priority": rule.priority,
                            "action": "DENY",
                            "default_fallback": "DENY",
                            "subsequent_allow_rules_overlap": False
                        },
                        severity="Low",
                        remediation=(
                            f'Rule #{rule.priority} reinforces the default DENY policy. While harmless for explicit auditing, '
                            f'it is functionally redundant if no subsequent ALLOW rules exist.'
                        )
                    )
                )

    return findings, inconclusive


# --- Feature C: Overly Permissive Security Policy Auditing ---

def audit_security_policies(rules: List[FirewallRuleData]) -> List[SecurityFindingData]:
    """
    Deterministic rule-based security audit checks identifying potentially risky firewall configurations.
    Transparent severity calculations, evidence, and remediations.
    """
    findings: List[SecurityFindingData] = []
    
    # Sensitive management & administration ports
    MANAGEMENT_PORTS = {
        22: ("SSH (Secure Shell)", "Critical"),
        23: ("Telnet (Unencrypted Remote Shell)", "Critical"),
        3389: ("RDP (Remote Desktop Protocol)", "Critical"),
        5900: ("VNC Remote Desktop", "High"),
        5985: ("WinRM HTTP", "High"),
        5986: ("WinRM HTTPS", "High"),
    }
    
    # Database and internal infrastructure ports
    DATABASE_PORTS = {
        3306: ("MySQL Database Server", "High"),
        5432: ("PostgreSQL Database Server", "High"),
        1433: ("Microsoft SQL Server", "High"),
        27017: ("MongoDB NoSQL Database", "High"),
        6379: ("Redis Cache & Key-Value Store", "High"),
        9200: ("Elasticsearch REST API", "High"),
        9300: ("Elasticsearch Node Communication", "High"),
    }

    INTERNAL_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
    ]

    for rule in rules:
        if not rule.enabled:
            # Audit note: Disabled rules do not enforce policy, so they do not present active risks
            continue

        src_clean = rule.source_ip.strip().upper()
        dst_clean = rule.destination_ip.strip().upper()
        port_clean = str(rule.destination_port).strip().upper()
        proto_clean = rule.protocol.strip().upper()
        action_clean = rule.action.strip().upper()

        is_allow = (action_clean == "ALLOW")
        is_any_source = (src_clean in {"ANY", "0.0.0.0/0", "::/0"})
        is_any_dest = (dst_clean in {"ANY", "0.0.0.0/0", "::/0"})
        is_any_port = (port_clean in {"ANY", "*"} and proto_clean != "ICMP")
        is_any_proto = (proto_clean == "ANY")

        # 1. Broad "ANY-ANY-ANY-ANY" ALLOW Rule (Critical)
        if is_allow and is_any_source and is_any_dest and is_any_port and is_any_proto:
            findings.append(
                SecurityFindingData(
                    finding_code=f"SEC-BROAD-ALLOW-ALL-RULE-{rule.id or rule.priority}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_priority=rule.priority,
                    category="Overly Broad Access",
                    severity="Critical",
                    finding_type="SECURITY_RISK",
                    title="Universal 'ANY-ANY' ALLOW Rule Permits All Traffic",
                    explanation=(
                        f'Rule #{rule.priority} "{rule.name}" permits all network traffic regardless of source IP, destination IP, '
                        f'port, or protocol. This effectively bypasses firewall filtering for any traffic reaching this rule.'
                    ),
                    evidence={
                        "source_ip": rule.source_ip,
                        "destination_ip": rule.destination_ip,
                        "destination_port": rule.destination_port,
                        "protocol": rule.protocol,
                        "action": rule.action,
                    },
                    remediation=(
                        "Remove or restrict this rule immediately. Narrow source and destination addresses to specific subnets, "
                        "and designate explicit required service ports."
                    ),
                    confidence="Confirmed"
                )
            )

        # 2. Remote Administration Ports open to ANY source (SSH, Telnet, RDP, VNC, WinRM)
        if is_allow and is_any_source:
            bounds, ok = parse_port_bounds(rule.destination_port, rule.protocol)
            if ok and bounds:
                p_min, p_max = bounds
                for port_num, (svc_name, default_sev) in MANAGEMENT_PORTS.items():
                    if p_min <= port_num <= p_max and proto_clean in {"TCP", "ANY"}:
                        findings.append(
                            SecurityFindingData(
                                finding_code=f"SEC-MGMT-EXPOSED-{port_num}-RULE-{rule.id or rule.priority}",
                                rule_id=rule.id,
                                rule_name=rule.name,
                                rule_priority=rule.priority,
                                category="Insecure Service Exposure",
                                severity=default_sev,
                                finding_type="SECURITY_RISK",
                                title=f"Remote Administration Port {port_num} ({svc_name}) Exposed to ANY Source",
                                explanation=(
                                    f'Rule #{rule.priority} "{rule.name}" allows inbound traffic on port {port_num} ({svc_name}) '
                                    f'from ANY source ({rule.source_ip}). Exposing remote administration interfaces to public/unrestricted '
                                    f'networks risks brute-force authentication attacks and unauthorized remote access.'
                                ),
                                evidence={
                                    "matched_port": port_num,
                                    "service": svc_name,
                                    "rule_source": rule.source_ip,
                                    "rule_port_spec": rule.destination_port,
                                    "rule_protocol": rule.protocol,
                                },
                                remediation=(
                                    f"Restrict access to port {port_num} to a dedicated VPN gateway, bastion host, or specific admin management CIDR."
                                ),
                                confidence="Confirmed"
                            )
                        )

                # 3. Database Ports open to ANY source
                for port_num, (db_name, default_sev) in DATABASE_PORTS.items():
                    if p_min <= port_num <= p_max and proto_clean in {"TCP", "ANY"}:
                        findings.append(
                            SecurityFindingData(
                                finding_code=f"SEC-DB-EXPOSED-{port_num}-RULE-{rule.id or rule.priority}",
                                rule_id=rule.id,
                                rule_name=rule.name,
                                rule_priority=rule.priority,
                                category="Insecure Service Exposure",
                                severity=default_sev,
                                finding_type="SECURITY_RISK",
                                title=f"Database Service Port {port_num} ({db_name}) Exposed to ANY Source",
                                explanation=(
                                    f'Rule #{rule.priority} "{rule.name}" permits connections to database port {port_num} ({db_name}) '
                                    f'from ANY source ({rule.source_ip}). Database servers should never be directly accessible from untrusted sources.'
                                ),
                                evidence={
                                    "matched_port": port_num,
                                    "database_service": db_name,
                                    "rule_source": rule.source_ip,
                                    "rule_port_spec": rule.destination_port,
                                },
                                remediation=(
                                    f"Restrict port {port_num} strictly to application server subnets or internal VPC endpoints."
                                ),
                                confidence="Confirmed"
                            )
                        )

        # 4. Unrestricted Destination Port Wildcard on ALLOW rule
        if is_allow and is_any_port and not (is_any_source and is_any_dest and is_any_port and is_any_proto):
            findings.append(
                SecurityFindingData(
                    finding_code=f"SEC-PORT-WILDCARD-ALLOW-RULE-{rule.id or rule.priority}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_priority=rule.priority,
                    category="Overly Broad Access",
                    severity="High",
                    finding_type="SECURITY_RISK",
                    title="ALLOW Rule with Destination Port Wildcard (ANY)",
                    explanation=(
                        f'Rule #{rule.priority} "{rule.name}" permits traffic on ANY destination port ({rule.destination_port}). '
                        f'Firewall best practices require the principle of least privilege, allowing only designated service ports.'
                    ),
                    evidence={
                        "destination_port": rule.destination_port,
                        "action": rule.action,
                        "destination_ip": rule.destination_ip,
                        "source_ip": rule.source_ip,
                    },
                    remediation=(
                        "Replace the wildcard port with explicit destination ports required for authorized services."
                    ),
                    confidence="High"
                )
            )

        # 5. Protocol Wildcard ANY with Specific Port
        if is_allow and is_any_proto and not is_any_port:
            findings.append(
                SecurityFindingData(
                    finding_code=f"SEC-PROTO-WILDCARD-PORT-RULE-{rule.id or rule.priority}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_priority=rule.priority,
                    category="Protocol Hygiene",
                    severity="Medium",
                    finding_type="SECURITY_RISK",
                    title="Protocol Wildcard (ANY) Used with Specific Destination Port",
                    explanation=(
                        f'Rule #{rule.priority} "{rule.name}" uses protocol wildcard ANY while specifying destination port "{rule.destination_port}". '
                        f'Most port-based services operate strictly over TCP or UDP. Allowing ANY protocol with specific ports may permit unintended transport protocols.'
                    ),
                    evidence={
                        "protocol": rule.protocol,
                        "destination_port": rule.destination_port,
                    },
                    remediation="Explicitly restrict protocol to TCP or UDP as required by the application.",
                    confidence="Confirmed"
                )
            )

        # 6. Broad Inbound Access to Internal RFC1918 Subnets
        if is_allow and is_any_source and not is_any_dest:
            dst_net = parse_ip_network(rule.destination_ip)
            if dst_net:
                for priv_net in INTERNAL_NETWORKS:
                    if dst_net.subnet_of(priv_net) or dst_net == priv_net:
                        if is_any_port or (rule.destination_port and "-" in str(rule.destination_port)):
                            findings.append(
                                SecurityFindingData(
                                    finding_code=f"SEC-INBOUND-INTERNAL-SUBNET-RULE-{rule.id or rule.priority}",
                                    rule_id=rule.id,
                                    rule_name=rule.name,
                                    rule_priority=rule.priority,
                                    category="Overly Broad Access",
                                    severity="High",
                                    finding_type="SECURITY_RISK",
                                    title=f"Broad Inbound Access to Internal Subnet {rule.destination_ip}",
                                    explanation=(
                                        f'Rule #{rule.priority} "{rule.name}" allows traffic from ANY source to internal private subnet '
                                        f'{rule.destination_ip} across wide or unrestricted ports ({rule.destination_port}). '
                                        f'Inbound perimeter rules should pinpoint specific public servers or load balancers.'
                                    ),
                                    evidence={
                                        "destination_ip": rule.destination_ip,
                                        "private_network_class": str(priv_net),
                                        "destination_port": rule.destination_port,
                                    },
                                    remediation="Restrict destination to specific reverse-proxy or DMZ host IP rather than the entire internal subnet.",
                                    confidence="High"
                                )
                            )
                        break

        # 7. Missing or Ambiguous Security Documentation
        if not rule.description or not rule.description.strip() or len(rule.description.strip()) < 5:
            findings.append(
                SecurityFindingData(
                    finding_code=f"SEC-DOC-MISSING-RULE-{rule.id or rule.priority}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_priority=rule.priority,
                    category="Policy Documentation",
                    severity="Low",
                    finding_type="SECURITY_RISK",
                    title="Missing or Insufficient Rule Security Documentation",
                    explanation=(
                        f'Rule #{rule.priority} "{rule.name}" does not include an informative description explaining its business '
                        f'justification, change ticket, or owning service.'
                    ),
                    evidence={
                        "rule_name": rule.name,
                        "description": rule.description or "(Empty)",
                    },
                    remediation="Add a clear description specifying the service purpose, authorized stakeholders, and security justification.",
                    confidence="Confirmed"
                )
            )

    return findings


# --- Comprehensive Policy Analysis Aggregator ---

def analyze_firewall_policy(rules: List[FirewallRuleData]) -> PolicyAnalysisReport:
    """
    Executes complete policy analysis:
    - Shadowing detection
    - Redundancy detection
    - Security risk auditing
    """
    shadow_findings, shadow_inconc = detect_shadowing(rules)
    redundancy_findings, redund_inconc = detect_redundancy(rules)
    sec_findings = audit_security_policies(rules)

    # Convert shadowing and redundancy findings into unified SecurityFindingData items
    all_findings: List[SecurityFindingData] = []

    for s in shadow_findings:
        all_findings.append(
            SecurityFindingData(
                finding_code=f"SHADOW-RULE-{s.rule_id or s.rule_priority}-BY-{'-'.join(map(str, s.shadowing_rule_priorities))}",
                rule_id=s.rule_id,
                rule_name=s.rule_name,
                rule_priority=s.rule_priority,
                category="Rule Shadowing",
                severity=s.severity,
                finding_type="SHADOWING",
                title=f"Rule #{s.rule_priority} is Fully Shadowed by Rule #{s.shadowing_rule_priorities[0]}",
                explanation=s.explanation,
                evidence=s.evidence,
                remediation=s.remediation,
                confidence=s.confidence
            )
        )

    for r in redundancy_findings:
        all_findings.append(
            SecurityFindingData(
                finding_code=f"REDUND-RULE-{r.rule_id or r.rule_priority}-{r.redundancy_type}",
                rule_id=r.rule_id,
                rule_name=r.rule_name,
                rule_priority=r.rule_priority,
                category="Rule Redundancy",
                severity=r.severity,
                finding_type="REDUNDANCY",
                title=f"Rule #{r.rule_priority} is Redundant ({r.redundancy_type.replace('_', ' ')})",
                explanation=r.explanation,
                evidence=r.evidence,
                remediation=r.remediation,
                confidence=r.confidence
            )
        )

    all_findings.extend(sec_findings)

    return PolicyAnalysisReport(
        rules_analyzed_count=len([r for r in rules if r.enabled]),
        shadowed_rules=shadow_findings,
        redundant_rules=redundancy_findings,
        security_findings=all_findings,
        inconclusive_checks=shadow_inconc + redund_inconc
    )
