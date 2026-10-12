from opentelemetry import trace
from opentelemetry.sdk.trace.sampling import Decision
from opentelemetry.trace import NonRecordingSpan, SpanContext, SpanKind, TraceFlags

from ai.backend.logging.otel import RootClientDropSampler

_TRACE_ID = 0x0AF7651916CD43DD8448EB211C80319C


def _parent(sampled: bool) -> trace.Span:
    flags = TraceFlags(TraceFlags.SAMPLED if sampled else TraceFlags.DEFAULT)
    return NonRecordingSpan(
        SpanContext(
            trace_id=_TRACE_ID, span_id=0xB7AD6B7169203331, is_remote=True, trace_flags=flags
        )
    )


class TestRootClientDropSampler:
    def test_drops_client_span_without_parent(self) -> None:
        result = RootClientDropSampler().should_sample(None, _TRACE_ID, "GET", SpanKind.CLIENT)

        assert result.decision is Decision.DROP

    def test_samples_server_span_without_parent(self) -> None:
        result = RootClientDropSampler().should_sample(None, _TRACE_ID, "GET /", SpanKind.SERVER)

        assert result.decision is Decision.RECORD_AND_SAMPLE

    def test_samples_client_span_under_sampled_parent(self) -> None:
        context = trace.set_span_in_context(_parent(sampled=True))

        result = RootClientDropSampler().should_sample(context, _TRACE_ID, "GET", SpanKind.CLIENT)

        assert result.decision is Decision.RECORD_AND_SAMPLE

    def test_follows_unsampled_parent(self) -> None:
        context = trace.set_span_in_context(_parent(sampled=False))

        result = RootClientDropSampler().should_sample(context, _TRACE_ID, "GET /", SpanKind.SERVER)

        assert result.decision is Decision.DROP
