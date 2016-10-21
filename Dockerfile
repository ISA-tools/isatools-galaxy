FROM docker-registry.phenomenal-h2020.eu/phnmnl/scp-aspera:latest
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

ENV REVISION c11eedc877819f8e546de14dbf9e387b1e116eee 

RUN apt-get -y update && apt-get -y install --no-install-recommends \
                      python-dev python-pip git && \
    pip install --upgrade pip && pip install -U setuptools && \
    pip install -e git+https://github.com/EBI-Metabolights/MetaboLightsLabs-PythonCLI.git@$REVISION#egg=uploadtometabolightslabs && \
    apt-get purge -y python-dev python-pip git && \
    apt-get install -y --no-install-recommends python && \ 
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENTRYPOINT ["uploadToMetaboLightsLabs.py"]
