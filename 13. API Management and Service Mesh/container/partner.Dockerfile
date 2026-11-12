FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY partner_gateway.py /app/partner_gateway.py
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin --user-group app
USER 10001
ENV GATEWAY_BIND=0.0.0.0 GATEWAY_PORT=8080
EXPOSE 8080
CMD ["python3","-B","partner_gateway.py"]
