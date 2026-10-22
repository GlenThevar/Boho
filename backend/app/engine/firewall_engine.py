"""
Boho Firewall Evaluation Engine
Stage 1: Offline Deterministic Firewall Simulation Engine

Provides deterministic, first-match-wins rule evaluation for network traffic records.
"""

from dataclasses import dataclass, field
import ipaddress
from typing import List, Optional, Tuple, Any, Dict


@dataclass
class FirewallRuleData:
    id: Optional[int]
    name: str
    priority: int
    source_ip: str
    destination_ip: str
    destination_port: str
    protocol: str
    action: str
    enabled: bool = True
    description: Optional[str] = None


@dataclass
class TrafficRecordData:
    record_id: str
    source_ip: str
    destination_ip: str
    destination_port: Optional[Any] = None
    protocol: str = "TCP"
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class EvaluationResult:
    record_id: str
    decision: str  # ALLOW or DENY
    matched_rule_id: Optional[int]
    matched_rule_name: Optional[str]
    explanation: str
    is_default_policy: bool
    validation_errors: List[str] = field(default_factory=list)
    source_ip: str = ""
    destination_ip: str = ""
    destination_port: Optional[str] = None
    protocol: str = ""


def validate_ip_or_cidr(val: str, field_name: str) -> Tuple[bool, Optional[str], Optional[ipaddress.IPv4Network | ipaddress.IPv6Network]]:
    """
    Validates if string is 'ANY' or a valid IPv4/IPv6 address or CIDR range.
    Returns (is_valid, error_message, network_object_if_applicable).
    """
    if not val or not isinstance(val, str) or not val.strip():
        return False, f"{field_name} cannot be blank. Use 'ANY' for wildcard matching.", None
    
    val_clean = val.strip().upper()
    if val_clean == "ANY":
        return True, None, None
    
    try:
        # strict=False allows host bits to be set in CIDR like 192.168.1.5/24
        net = ipaddress.ip_network(val.strip(), strict=False)
        return True, None, net
    except ValueError as e:
        return False, f"Invalid {field_name} '{val}': must be valid IP address, CIDR range, or 'ANY'. ({str(e)})", None


def validate_port_spec(val: Any, protocol: str = "ANY") -> Tuple[bool, Optional[str]]:
    """
    Validates port specification: 'ANY', single port (1-65535), or range (e.g. '80-443').
    ICMP permits 'ANY', blank/None, or optional port.
    """
    proto_upper = str(protocol).strip().upper()
    
    if val is None or str(val).strip() == "" or str(val).strip().upper() == "N/A":
        if proto_upper == "ICMP":
            return True, None
        return False, "Port cannot be blank for TCP/UDP/ANY. Use 'ANY' for wildcard matching."
    
    val_str = str(val).strip().upper()
    if val_str == "ANY":
        return True, None
    
    # Check port range min-max
    if "-" in val_str:
        parts = val_str.split("-")
        if len(parts) != 2:
            return False, f"Invalid port range '{val_str}'. Expected format: 'start-end' (e.g. '80-443')."
        try:
            start_p = int(parts[0].strip())
            end_p = int(parts[1].strip())
        except ValueError:
            return False, f"Port range '{val_str}' must contain valid integer port numbers."
        
        if not (1 <= start_p <= 65535 and 1 <= end_p <= 65535):
            return False, f"Port numbers must be between 1 and 65535. Received '{val_str}'."
        if start_p > end_p:
            return False, f"Port range start ({start_p}) must not exceed range end ({end_p})."
        return True, None

    # Single port
    try:
        p = int(val_str)
    except ValueError:
        return False, f"Invalid port '{val_str}'. Must be an integer between 1 and 65535, a range 'start-end', or 'ANY'."
    
    if not (1 <= p <= 65535):
        return False, f"Port must be between 1 and 65535. Received '{val_str}'."
    
    return True, None


def validate_protocol_spec(proto: str) -> Tuple[bool, Optional[str]]:
    """
    Validates protocol specification: TCP, UDP, ICMP, or ANY.
    """
    if not proto or not str(proto).strip():
        return False, "Protocol cannot be blank. Must be TCP, UDP, ICMP, or ANY."
    
    proto_upper = str(proto).strip().upper()
    if proto_upper not in {"TCP", "UDP", "ICMP", "ANY"}:
        return False, f"Invalid protocol '{proto}'. Must be TCP, UDP, ICMP, or ANY."
    return True, None


def validate_rule(rule: FirewallRuleData) -> List[str]:
    """
    Validates complete firewall rule definitions.
    """
    errors = []
    if not rule.name or not rule.name.strip():
        errors.append("Rule name cannot be blank.")
    
    if rule.priority is None or not isinstance(rule.priority, int) or rule.priority < 1:
        errors.append("Rule priority must be a positive integer.")
    
    # Validate source IP
    ok, err, _ = validate_ip_or_cidr(rule.source_ip, "Source IP")
    if not ok:
        errors.append(err)
        
    # Validate destination IP
    ok, err, _ = validate_ip_or_cidr(rule.destination_ip, "Destination IP")
    if not ok:
        errors.append(err)
        
    # Validate protocol
    ok, err = validate_protocol_spec(rule.protocol)
    if not ok:
        errors.append(err)
        
    # Validate destination port
    ok, err = validate_port_spec(rule.destination_port, rule.protocol)
    if not ok:
        errors.append(err)
        
    # Validate action
    action_upper = (rule.action or "").strip().upper()
    if action_upper not in {"ALLOW", "DENY"}:
        errors.append(f"Invalid action '{rule.action}'. Must be ALLOW or DENY.")
        
    return errors


def validate_record(record: TrafficRecordData) -> List[str]:
    """
    Validates a traffic record for evaluation.
    """
    errors = []
    
    # Source IP validation
    if not record.source_ip or not str(record.source_ip).strip():
        errors.append("Source IP is missing or empty.")
    else:
        try:
            ipaddress.ip_address(str(record.source_ip).strip())
        except ValueError:
            errors.append(f"Invalid source IP address: '{record.source_ip}'.")
            
    # Destination IP validation
    if not record.destination_ip or not str(record.destination_ip).strip():
        errors.append("Destination IP is missing or empty.")
    else:
        try:
            ipaddress.ip_address(str(record.destination_ip).strip())
        except ValueError:
            errors.append(f"Invalid destination IP address: '{record.destination_ip}'.")
            
    # Protocol validation
    if not record.protocol or not str(record.protocol).strip():
        errors.append("Protocol is missing or empty.")
    else:
        proto_upper = str(record.protocol).strip().upper()
        if proto_upper not in {"TCP", "UDP", "ICMP"}:
            errors.append(f"Invalid traffic protocol '{record.protocol}'. Expected TCP, UDP, or ICMP.")
            
    # Destination port validation
    proto_upper = str(record.protocol or "").strip().upper()
    port_val = record.destination_port
    
    if proto_upper == "ICMP":
        # Destination port optional for ICMP
        if port_val is not None and str(port_val).strip() != "" and str(port_val).strip().upper() not in {"N/A", "ANY", "0"}:
            try:
                p = int(str(port_val).strip())
                if not (0 <= p <= 65535):
                    errors.append(f"ICMP port/type code out of range (0-65535): '{port_val}'.")
            except ValueError:
                errors.append(f"Invalid ICMP port value: '{port_val}'. ICMP does not require port numbers.")
    else:
        # TCP / UDP require an integer port between 1 and 65535
        if port_val is None or str(port_val).strip() == "":
            errors.append(f"Destination port is required for {proto_upper or 'TCP/UDP'} traffic.")
        else:
            try:
                p = int(str(port_val).strip())
                if not (1 <= p <= 65535):
                    errors.append(f"Destination port {p} is outside valid range (1-65535).")
            except ValueError:
                errors.append(f"Invalid destination port '{port_val}'. Must be an integer between 1 and 65535.")
                
    return errors


def match_ip(rule_ip_str: str, packet_ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, str]:
    """
    Checks if packet_ip matches rule_ip_str (ANY, single IP, or CIDR).
    """
    rule_ip_clean = rule_ip_str.strip()
    if rule_ip_clean.upper() == "ANY":
        return True, "wildcard ANY matched"
    
    net = ipaddress.ip_network(rule_ip_clean, strict=False)
    if packet_ip_obj.version != net.version:
        return False, f"IP version mismatch ({packet_ip_obj} vs {rule_ip_clean})"
    
    if packet_ip_obj in net:
        if net.num_addresses == 1:
            return True, f"exact IP {packet_ip_obj} matched {rule_ip_clean}"
        return True, f"IP {packet_ip_obj} matched subnet {rule_ip_clean}"
    
    return False, f"IP {packet_ip_obj} does not match {rule_ip_clean}"


def match_protocol(rule_proto_str: str, packet_proto_str: str) -> Tuple[bool, str]:
    """
    Checks protocol match.
    """
    r_proto = rule_proto_str.strip().upper()
    p_proto = packet_proto_str.strip().upper()
    
    if r_proto == "ANY" or r_proto == p_proto:
        return True, f"protocol {p_proto} matched {r_proto}"
    return False, f"protocol {p_proto} does not match rule protocol {r_proto}"


def match_port(rule_port_str: str, packet_port_int: Optional[int], packet_proto: str) -> Tuple[bool, str]:
    """
    Matches packet destination port against rule destination port specification.
    ICMP note: Destination ports are optional for ICMP since ICMP operates without
    TCP/UDP transport layer ports. If the rule port is ANY, ICMP matches.
    """
    r_port_clean = str(rule_port_str).strip().upper()
    p_proto = packet_proto.strip().upper()
    
    if r_port_clean == "ANY":
        return True, "port wildcard ANY matched"
    
    if p_proto == "ICMP":
        if packet_port_int is None:
            # ICMP record without port matches only if rule explicitly set to ANY
            return False, f"rule specifies destination port {r_port_clean}, but ICMP record has no port"
    
    if packet_port_int is None:
        return False, f"traffic has no port, rule requires {r_port_clean}"
    
    if "-" in r_port_clean:
        start_p, end_p = map(int, r_port_clean.split("-"))
        if start_p <= packet_port_int <= end_p:
            return True, f"port {packet_port_int} inside range {start_p}-{end_p}"
        return False, f"port {packet_port_int} outside range {start_p}-{end_p}"
    
    try:
        rule_port_num = int(r_port_clean)
        if packet_port_int == rule_port_num:
            return True, f"exact port {packet_port_int} matched"
        return False, f"port {packet_port_int} does not match {rule_port_num}"
    except ValueError:
        return False, f"invalid rule port format: {rule_port_clean}"


def evaluate_record(record: TrafficRecordData, rules: List[FirewallRuleData]) -> EvaluationResult:
    """
    Evaluates a single traffic record against an ordered list of firewall rules.
    Rules should be pre-sorted by priority (ascending).
    Stops at the first matching enabled rule.
    Defaults to DENY if no enabled rule matches.
    """
    # 1. Validate the record first
    val_errors = validate_record(record)
    
    rec_port_str = str(record.destination_port).strip() if record.destination_port is not None else ""
    rec_proto_str = str(record.protocol).strip().upper() if record.protocol else ""
    
    if val_errors:
        return EvaluationResult(
            record_id=str(record.record_id),
            decision="DENY",
            matched_rule_id=None,
            matched_rule_name=None,
            explanation=f"Record validation failed: {'; '.join(val_errors)}. Default policy DENY applied.",
            is_default_policy=True,
            validation_errors=val_errors,
            source_ip=str(record.source_ip),
            destination_ip=str(record.destination_ip),
            destination_port=rec_port_str,
            protocol=rec_proto_str,
        )
    
    # Parse record values
    p_src_ip = ipaddress.ip_address(str(record.source_ip).strip())
    p_dst_ip = ipaddress.ip_address(str(record.destination_ip).strip())
    
    p_port_int = None
    if rec_port_str and rec_port_str.upper() not in {"N/A", "ANY", ""}:
        try:
            p_port_int = int(rec_port_str)
        except ValueError:
            p_port_int = None
            
    # Sort enabled rules by priority ascending
    enabled_rules = [r for r in rules if r.enabled]
    sorted_rules = sorted(enabled_rules, key=lambda r: r.priority)
    
    for rule in sorted_rules:
        # Check protocol match
        proto_ok, proto_msg = match_protocol(rule.protocol, rec_proto_str)
        if not proto_ok:
            continue
            
        # Check source IP match
        src_ok, src_msg = match_ip(rule.source_ip, p_src_ip)
        if not src_ok:
            continue
            
        # Check destination IP match
        dst_ok, dst_msg = match_ip(rule.destination_ip, p_dst_ip)
        if not dst_ok:
            continue
            
        # Check destination port match
        port_ok, port_msg = match_port(rule.destination_port, p_port_int, rec_proto_str)
        if not port_ok:
            continue
            
        # First matching rule found!
        explanation = (
            f'Matched Rule #{rule.id or "?"} "{rule.name}" (Priority {rule.priority}): '
            f'{proto_msg}; {src_msg}; {dst_msg}; {port_msg}. '
            f'Action: {rule.action.upper()}'
        )
        return EvaluationResult(
            record_id=str(record.record_id),
            decision=rule.action.upper(),
            matched_rule_id=rule.id,
            matched_rule_name=rule.name,
            explanation=explanation,
            is_default_policy=False,
            validation_errors=[],
            source_ip=str(record.source_ip),
            destination_ip=str(record.destination_ip),
            destination_port=rec_port_str,
            protocol=rec_proto_str,
        )
    
    # No rule matched -> Default DENY
    return EvaluationResult(
        record_id=str(record.record_id),
        decision="DENY",
        matched_rule_id=None,
        matched_rule_name=None,
        explanation="No matching enabled firewall rule found. Default policy applied: DENY.",
        is_default_policy=True,
        validation_errors=[],
        source_ip=str(record.source_ip),
        destination_ip=str(record.destination_ip),
        destination_port=rec_port_str,
        protocol=rec_proto_str,
    )


def evaluate_dataset(records: List[TrafficRecordData], rules: List[FirewallRuleData]) -> List[EvaluationResult]:
    """
    Evaluates an entire dataset of traffic records against the provided rules.
    """
    return [evaluate_record(record, rules) for record in records]
