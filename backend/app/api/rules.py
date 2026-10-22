from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.firewall import FirewallRule
from app.schemas.firewall import (
    FirewallRuleCreate,
    FirewallRuleUpdate,
    FirewallRuleResponse,
    FirewallRuleToggle,
    FirewallRuleReorderItem,
)

router = APIRouter(prefix="/api/rules", tags=["Firewall Rules"])


@router.get("", response_model=List[FirewallRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    """
    List all firewall rules sorted in priority order (ascending).
    """
    return db.query(FirewallRule).order_by(FirewallRule.priority.asc(), FirewallRule.id.asc()).all()


@router.post("", response_model=FirewallRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(rule_in: FirewallRuleCreate, db: Session = Depends(get_db)):
    """
    Create a new firewall rule.
    """
    new_rule = FirewallRule(
        name=rule_in.name,
        priority=rule_in.priority,
        source_ip=rule_in.source_ip,
        destination_ip=rule_in.destination_ip,
        destination_port=rule_in.destination_port,
        protocol=rule_in.protocol,
        action=rule_in.action,
        enabled=rule_in.enabled,
        description=rule_in.description,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/{rule_id}", response_model=FirewallRuleResponse)
def update_rule(rule_id: int, rule_in: FirewallRuleUpdate, db: Session = Depends(get_db)):
    """
    Update an existing firewall rule.
    """
    rule = db.query(FirewallRule).filter(FirewallRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Firewall rule with ID {rule_id} not found")

    rule.name = rule_in.name
    rule.priority = rule_in.priority
    rule.source_ip = rule_in.source_ip
    rule.destination_ip = rule_in.destination_ip
    rule.destination_port = rule_in.destination_port
    rule.protocol = rule_in.protocol
    rule.action = rule_in.action
    rule.enabled = rule_in.enabled
    rule.description = rule_in.description

    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}/toggle", response_model=FirewallRuleResponse)
def toggle_rule(rule_id: int, toggle: FirewallRuleToggle, db: Session = Depends(get_db)):
    """
    Toggle a rule's enabled / disabled status.
    """
    rule = db.query(FirewallRule).filter(FirewallRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Firewall rule with ID {rule_id} not found")

    rule.enabled = toggle.enabled
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/reorder", response_model=List[FirewallRuleResponse])
def reorder_rules(reorder_items: List[FirewallRuleReorderItem], db: Session = Depends(get_db)):
    """
    Batch update priorities of firewall rules.
    """
    id_map = {item.id: item.priority for item in reorder_items}
    rules = db.query(FirewallRule).filter(FirewallRule.id.in_(id_map.keys())).all()
    
    for rule in rules:
        rule.priority = id_map[rule.id]
        
    db.commit()
    return db.query(FirewallRule).order_by(FirewallRule.priority.asc(), FirewallRule.id.asc()).all()


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Delete a firewall rule. Existing historical simulations remain intact.
    """
    rule = db.query(FirewallRule).filter(FirewallRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Firewall rule with ID {rule_id} not found")

    db.delete(rule)
    db.commit()
    return None


@router.post("/seed-defaults", response_model=List[FirewallRuleResponse])
def seed_default_rules(db: Session = Depends(get_db)):
    """
    Seeds a curated set of standard firewall rules for quick testing.
    """
    if db.query(FirewallRule).count() > 0:
        return db.query(FirewallRule).order_by(FirewallRule.priority.asc()).all()

    defaults = [
        FirewallRule(
            name="Block Dangerous Telnet",
            priority=1,
            source_ip="ANY",
            destination_ip="ANY",
            destination_port="23",
            protocol="TCP",
            action="DENY",
            enabled=True,
            description="Prevent unencrypted telnet connections everywhere"
        ),
        FirewallRule(
            name="Allow Inbound HTTPS",
            priority=10,
            source_ip="ANY",
            destination_ip="10.0.0.10",
            destination_port="443",
            protocol="TCP",
            action="ALLOW",
            enabled=True,
            description="Allow secure HTTPS web traffic to primary server"
        ),
        FirewallRule(
            name="Allow Inbound HTTP",
            priority=20,
            source_ip="ANY",
            destination_ip="10.0.0.10",
            destination_port="80",
            protocol="TCP",
            action="ALLOW",
            enabled=True,
            description="Allow standard HTTP traffic to primary server"
        ),
        FirewallRule(
            name="Allow Internal Subnet DNS",
            priority=30,
            source_ip="192.168.1.0/24",
            destination_ip="1.1.1.1",
            destination_port="53",
            protocol="UDP",
            action="ALLOW",
            enabled=True,
            description="Permit internal office network to query Cloudflare DNS"
        ),
        FirewallRule(
            name="Allow ICMP Diagnostics",
            priority=40,
            source_ip="192.168.1.0/24",
            destination_ip="ANY",
            destination_port="ANY",
            protocol="ICMP",
            action="ALLOW",
            enabled=True,
            description="Allow ICMP ping requests from internal subnet"
        ),
        FirewallRule(
            name="Block Malicious Subnet",
            priority=50,
            source_ip="203.0.113.0/24",
            destination_ip="ANY",
            destination_port="ANY",
            protocol="ANY",
            action="DENY",
            enabled=True,
            description="Known suspicious network range"
        )
    ]
    db.add_all(defaults)
    db.commit()
    return db.query(FirewallRule).order_by(FirewallRule.priority.asc()).all()
