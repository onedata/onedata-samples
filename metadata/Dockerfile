FROM gitlab-registry.in2p3.fr/cta-lapp/cta-archive
#https://gitlab.in2p3.fr/CTA-LAPP/cta-archive/blob/master/Dockerfile

RUN conda install -c onedata fs.onedatafs=19.02.0-rc2=py36_0

# One test file to have inside of container
COPY gamma_test_generated_200.hdf5 .

COPY run.sh .
COPY run.py .
ENTRYPOINT ["./run.py"]
