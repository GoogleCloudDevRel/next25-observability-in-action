import os
import structlog
from opentelemetry import trace

def add_otel_traceids(logger, log_method, event_dict):
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return event_dict
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    traceid = trace.format_trace_id(ctx.trace_id)
    event_dict["logging.googleapis.com/trace"] = f"projects/{project}/traces/{traceid}"
    return event_dict

def use_gcp_fieldnames(logger, log_method, event_dict):
    event_dict["severity"] = event_dict["level"]
    del event_dict["level"]
    return event_dict

def getJSONLogger():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper("iso"),
            use_gcp_fieldnames,
            add_otel_traceids,
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ]
    )
    return structlog.get_logger()