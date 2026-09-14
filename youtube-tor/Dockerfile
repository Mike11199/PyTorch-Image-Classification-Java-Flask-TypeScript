FROM alpine:3.22
RUN apk add --no-cache tor su-exec iptables
COPY torrc /etc/tor/torrc
COPY entrypoint.sh healthcheck.sh firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/healthcheck.sh /usr/local/bin/firewall.sh
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s CMD /usr/local/bin/healthcheck.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
