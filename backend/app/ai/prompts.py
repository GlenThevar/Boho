"""Prompt templates for Amazon Bedrock AI features (Stage 3)."""


def build_explain_finding_prompt(finding_type: str, finding_summary: str,
                                  rule_details: dict | None,
                                  responsible_rules: list | None,
                                  severity: str | None) -> str:
    rule_block = ""
    if rule_details:
        rule_block = f"\n\nAffected rule:\n{_format_rule(rule_details)}"

    responsible_block = ""
    if responsible_rules:
        lines = "\n".join(_format_rule(r) for r in responsible_rules[:5])
        responsible_block = f"\n\nRules causing this finding:\n{lines}"

    severity_block = f"\nSeverity: {severity}" if severity else ""

    return f"""You are a senior network security engineer reviewing a firewall policy analysis finding.

Finding type: {finding_type}{severity_block}
Finding summary: {finding_summary}{rule_block}{responsible_block}

Provide a concise, structured explanation with the following sections:
1. **Issue** — what this finding means in plain language
2. **Evidence** — concrete reasons why this finding was flagged
3. **Risk** — potential security impact if left unresolved
4. **Remediation** — specific, actionable steps to fix the issue
5. **Side Effects** — what changing this rule might affect
6. **Verification** — how to confirm the fix worked

Keep each section to 2-4 sentences. Be specific. Do not invent IP addresses or traffic patterns not mentioned in the evidence. Do not recommend changes that could break legitimate traffic without noting the risk."""


def build_suggest_improvements_prompt(rules: list, findings_summary: str | None) -> str:
    rules_text = "\n".join(_format_rule(r) for r in rules[:20])
    findings_block = f"\n\nKnown issues:\n{findings_summary}" if findings_summary else ""

    return f"""You are a senior network security engineer auditing a firewall policy.

Current firewall rules (in priority order):
{rules_text}{findings_block}

Suggest up to 5 concrete improvements to make this policy safer. For each suggestion:
- Give it a short title
- Describe exactly what to change
- Explain the security rationale
- Note the potential impact on traffic

Format each suggestion as:
SUGGESTION: <title>
CHANGE: <description>
RATIONALE: <security reasoning>
IMPACT: <potential effect on traffic>

Do not invent IP ranges or services not visible in the existing rules. Do not suggest changes that contradict the user's evident intent. Mark assumptions clearly."""


def build_explain_comparison_prompt(before_label: str, after_label: str,
                                     total_records: int, changed_records: int,
                                     newly_allowed: int, newly_denied: int,
                                     summary_stats: dict) -> str:
    stats_text = "\n".join(f"  {k}: {v}" for k, v in summary_stats.items())

    return f"""You are a senior network security engineer reviewing a firewall policy comparison report.

Policy comparison:
  Before: {before_label}
  After: {after_label}
  Total traffic records evaluated: {total_records}
  Records with changed decisions: {changed_records}
  Newly allowed by new policy: {newly_allowed}
  Newly denied by new policy: {newly_denied}

Additional statistics:
{stats_text}

Provide a structured summary with these sections:
1. **Overview** — high-level summary of what changed
2. **Security Impact** — whether the new policy is more or less restrictive and what that means
3. **Newly Allowed Traffic** — what was blocked before and is now allowed; flag any concerns
4. **Newly Denied Traffic** — what was allowed before and is now blocked; note disruption risk
5. **Records Requiring Review** — categories of traffic that should be manually verified
6. **Recommendation** — whether to adopt the new policy, with conditions if any

Base your analysis only on the statistics provided. Do not invent traffic patterns or IP ranges."""


def build_assistant_prompt(question: str, context_rules: list | None,
                            context_findings: list | None,
                            context_comparison: dict | None) -> str:
    context_parts = []

    if context_rules:
        rules_text = "\n".join(_format_rule(r) for r in context_rules[:15])
        context_parts.append(f"Current firewall rules:\n{rules_text}")

    if context_findings:
        findings_text = "\n".join(
            f"- [{f.get('severity','?')}] {f.get('finding_type','?')}: {f.get('summary','?')}"
            for f in context_findings[:10]
        )
        context_parts.append(f"Recent policy findings:\n{findings_text}")

    if context_comparison:
        comp_text = "\n".join(f"  {k}: {v}" for k, v in context_comparison.items())
        context_parts.append(f"Latest policy comparison:\n{comp_text}")

    context_block = "\n\n".join(context_parts)
    context_section = f"\n\nContext from the current Boho application state:\n{context_block}" if context_block else ""

    return f"""You are a cybersecurity assistant embedded in Boho, a firewall policy simulation and auditing platform.{context_section}

User question: {question}

Answer concisely and accurately based only on the provided context. If the question cannot be answered from the context, say so clearly. Do not invent firewall rules, IP addresses, or statistics. Do not suggest modifying the host operating system's real firewall."""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_rule(rule: dict) -> str:
    """Format a rule dict as a single readable line."""
    parts = []
    if "priority" in rule:
        parts.append(f"[P{rule['priority']}]")
    if "name" in rule:
        parts.append(f"name={rule['name']}")
    for field in ("source_ip", "destination_ip", "destination_port", "protocol", "action", "enabled"):
        if field in rule:
            parts.append(f"{field}={rule[field]}")
    return "  " + " | ".join(parts)
