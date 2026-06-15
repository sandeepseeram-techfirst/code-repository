from google.adk.agents.llm_agent import Agent


def get_alert_details(alert_id: str) -> dict:
    """Returns mock alert metadata for an incident."""
    return {
        "alert_id": alert_id,
        "service": "checkout-api",
        "environment": "staging",
        "severity": "high",
        "summary": "Elevated HTTP 5xx rate",
        "affected_deployment": "checkout-api-v42",
    }


def get_recent_deployments(service: str) -> dict:
    """Returns mock deployment history for a service."""
    return {
        "service": service,
        "recent_deployments": [
            {
                "version": "checkout-api-v42",
                "author": "platform-team",
                "change": "Increased checkout timeout",
                "time": "14 minutes ago",
            },
            {
                "version": "checkout-api-v41",
                "author": "payments-team",
                "change": "Dependency upgrade",
                "time": "2 days ago",
            },
        ],
    }


def get_service_metrics(service: str) -> dict:
    """Returns mock service health metrics."""
    return {
        "service": service,
        "error_rate_percent": 18.4,
        "p99_latency_ms": 2400,
        "cpu_utilization_percent": 41,
        "memory_utilization_percent": 63,
        "dependency_errors": {
            "payments-api": 0.2,
            "inventory-api": 17.9,
        },
    }


incident_classifier = Agent(
    name="incident_classifier",
    model="gemini-flash-latest",
    description="Classifies an incident and identifies affected services.",
    instruction=(
        "Classify the incident. Identify the affected service, environment, "
        "severity, and likely failure domain. Be concise."
    ),
    tools=[get_alert_details],
)

diagnostician = Agent(
    name="diagnostician",
    model="gemini-flash-latest",
    description="Diagnoses likely root cause using metrics and deployment data.",
    instruction=(
        "Use metrics and recent deployments to identify the most likely root cause. "
        "Do not recommend destructive actions. Clearly separate observations, "
        "hypotheses, and recommended next steps."
    ),
    tools=[get_service_metrics, get_recent_deployments],
)

root_agent = Agent(
    name="sre_triage_orchestrator",
    model="gemini-flash-latest",
    description="Coordinates SRE incident triage.",
    instruction=(
        "You coordinate incident triage. First delegate to incident_classifier. "
        "Then delegate to diagnostician. Produce a final incident summary with: "
        "impact, likely root cause, evidence, recommended action, and required "
        "human approval."
    ),
    tools=[incident_classifier, diagnostician],
)