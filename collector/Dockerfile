FROM otel/opentelemetry-collector-contrib:0.119.0

COPY collector-config.yaml /etc/otelcol-contrib/config.yaml

EXPOSE 4317 4318 13133
# CMD otelcol --config /etc/otelcol-contrib/config.yaml
# ENTRYPOINT ["/otelcontribcol"]
# CMD ["--config", "/etc/otelcol-contrib/config.yaml"]