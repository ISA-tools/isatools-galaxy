ISA Galaxy tools
================
We have developed a set of tools for the Galaxy-workflow-management system that 
wrap up various features from the 
[ISA API](https://github.com/ISA-tools/isa-api/).

Converters
----------
Convent to and from ISA-formatted content.
 - `isatab2json`: Convert ISA-Tab to ISA-JSON.

Create ISA content
------------------
Create ISA template content from study design information.
 - `create_metabo`: Create ISA for metabolomics.
 
ISA-Tab slicer
--------------
Query over ISA-Tab content.
 - `isa_factors_summary`: Get a summary of study groups (factor combinations) 
 their sample names.
 - `isa_get_study_factors`: Get the list of study factors.
 - `isa_get_study_factor_values`: For a given study factor get the list of 
 factor values used.
 - `isa_get_data_files_list`: For a given study factor and factor value get the 
 list of associated data files.
 - `isa_get_data_files_collection`: For a given study factor and factor value 
 get the associated data files as a data collection. This tool assumes the input
 Galaxy history item initially contains the full set of data files.
 
Validators
----------
Validate ISA-formatted content.
 - `isatab_validator`: Produce a validation report for a given ISA-Tab.
 
Tools in development
--------------------
Galaxy tools that are currently in development.
 - `json2isatab`: Convert ISA-JSON to ISA-Tab.
 - `isa-creator-plant-phenotyping`: Create ISA for plant phenotyping.
 - `isa-creator-genomics-transcriptomics`: Create ISA for genomics-transcriptomics.
  
___
The initial tool implementations in this repository were developed during the 
Horizon 2020 funded 
[PhenoMeNal: Large Scale Computing for Metabolomics](https://phenomenal-h2020.eu) 
project.  