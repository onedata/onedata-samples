FROM gitlab-registry.in2p3.fr/cta-lapp/cta-archive AS extractor

# Install Oneclient 
FROM onedata/oneclient:19.02.1

# Copy CTA matadata extration tools from the image
WORKDIR /app
COPY --from=extractor /app .

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY run.sh .
COPY run.py .
ENTRYPOINT ["./run.py"]
