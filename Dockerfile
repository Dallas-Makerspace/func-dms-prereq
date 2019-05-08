FROM python:3-alpine
EXPOSE 5000
LABEL function="true"
ENV fprocess="python /srv/func-dms-prereq.py"
ADD https://github.com/openfaas/faas/releases/download/0.9.14/fwatchdog /usr/bin
ADD Procfile requirements.txt src/ /srv/

WORKDIR /srv
RUN pip install -r requirements.txt && \
         chmod +x /usr/bin/fwatchdog && \
         adduser -D svc_dmsprereq && \
         chown -R nobody: /srv
USER svc_dmsprereq
ENTRYPOINT ["/usr/bin/fwatchdog"]
