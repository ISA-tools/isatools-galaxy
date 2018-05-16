Use a Galaxy source that has the ISA datatypes implemented. The easiest is to get the `phnmnl/galaxy` and use the `release_17.09_plus_isa_k8s_resource_limts` branch:

```
git clone https://github.com/phnmnl/galaxy
cd galaxy
git checkout release_17.09_plus_isa_k8s_resource_limts
```

Make sure you are in the `tools/isacreator_metabo` directory and run:
```
./install_to_gx_and_run.sh /path/to/galaxy
```
to install this tool to Galaxy and run Galaxy via its `run.sh` script.

### What does install_to_gx_and_run.sh do?

It copies across the following files:

- `tool_data_table_conf.xml`
- `tool_conf.xml`

into the `config/` subdirectory in the Galaxy root.

It then makes sure that `tool_data_table_config_path` and `tool_data_path` properties in `galaxy.ini` are uncommented out.

Next, it creates the `isatools/` subdirectory in the `tools/` directory of Galaxy and copies across the tool files.

Finally, it runs Galaxy using the standard `run.sh` script.
