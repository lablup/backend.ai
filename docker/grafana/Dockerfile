ARG GRAFANA_VERSION=latest
FROM grafana/grafana-enterprise:${GRAFANA_VERSION}

# Install plugins
RUN grafana cli plugins install redis-datasource && \
    grafana cli plugins install fifemon-graphql-datasource && \
    grafana cli plugins install grafana-piechart-panel && \
    grafana cli plugins install marcusolsson-json-datasource && \
    grafana cli plugins install yesoreyeram-infinity-datasource
