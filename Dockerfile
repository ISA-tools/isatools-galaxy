FROM docker-registry.phenomenal-h2020.eu/phnmnl/scp-aspera:latest
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

LABEL Description="Allows users to upload data to MetaboLights Labs"
LABEL software.version=0.1.0
LABEL version=0.2
LABEL software="MetaboLights Labs Uploader"

ENV REVISION 77bb8886a1e15c4537928c4634e6a23428d93900 

RUN apt-get -y update && apt-get -y install --no-install-recommends \
                      python-dev python-pip git && \
    pip install --upgrade pip && pip install -U setuptools && \
    pip install -e git+https://github.com/EBI-Metabolights/MetaboLightsLabs-PythonCLI.git@$REVISION#egg=uploadtometabolightslabs && \
    apt-get purge -y python-dev python-pip git && \
    apt-get install -y --no-install-recommends python && \ 
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENTRYPOINT ["uploadToMetaboLightsLabs.py"]
