![Logo](logo.png)

# MetaboLights Labs Uploader
Version: 0.1.0

## Short Description

Facilities for uploading data to MetaboLights Labs

## Description

MetaboLights is a database for Metabolomics experiments and derived information.
The database is cross-species, cross-technique and covers metabolite structures and their reference spectra as well as their biological roles, locations and concentrations, and experimental data from metabolic experiments.We will provide search services around spectral similarities and chemical structures.

We offer user-submission tools and have strong reporting capabilities. We will utilise and further develop de-facto standard formats where various components are encapsulated, such as the encoded spectral and chromatographic data, and associated information about the chemical structure, as well as metadata describing assays and the study as a whole.

MetaboLights semantic quality will be based on various controlled vocabularies linking data to existing resources such as BRENDA (tissue ontology) and other established ontologies. We are dedicated to collaborate closely with major parties in world-wide metabolomics communities, such as the Metabolomics Society and the associated Metabolomics Standards Initiative (MSI).

## Key features

- User-submission tools
- Strong reporting capabilities
- Utilise and further develop de-facto standard formats where various components are encapsulated

## Functionality

- Data Management / Study Dataset Deposition

## Approaches

- Metabolomics
- Isotopic Labelling Analysis

## Instrument Data Types

- MS
- NMR

## Approaches
  
## Instrument Data Types

## Tool Authors

- Venkata Chandrasekhar Nainala (EMBL-EBI)

## Container Contributors

- [Pablo Moreno](https://github.com/pcm32) (EMBL-EBI)
- [Philippe Rocca-Serra](https://github.com/proccaserra) (University of Oxford)

## Website

- http://www.ebi.ac.uk/metabolights/

## Git Repository

- https://github.com/EBI-Metabolights/MetaboLightsLabs-PythonCLI
- https://github.com/phnmnl/container-mtbl-labs-uploader

## Installation 

This tool is preloaded in PhenoMeNal Galaxy deployments.

For local individual installation of the container:

```bash
docker pull container-registry.phenomenal-h2020.eu/phnmnl/mtbl-labs-uploader
```

## Usage Instructions

Available on PhenoMeNal Galaxy instances under "PhenoMeNal H2020 Tools", under the section "Transfer".

For direct docker usage:

```bash
docker run -v $PWD:/data container-registry.phenomenal-h2020.eu/phnmnl/mtbl-labs-uploader -t "your-metabolights_labs_key" \
                                                                                          -i /data/maf.zip /data/data.tar /data/isa.zip \
                                                                                          -n -s
```

## Publications

- Haug, K., Salek, R. M., Conesa, P., Hastings, J., de Matos, P., Rijnbeek, M., ... & Maguire, E. (2012). MetaboLights—an open-access general-purpose repository for metabolomics studies and associated meta-data. Nucleic acids research, gks1004.
