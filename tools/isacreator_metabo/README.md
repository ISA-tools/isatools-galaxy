# ISA creator

Use a Galaxy source that has the ISA datatypes implemented. The easiest is to get the `phnmnl/galaxy` and use the `release_17.09_isa_k8s_resource_limts_runnerRestartJobs` branch. See [How-to install Galaxy locally with ISA-Tab datatype](https://docs.google.com/document/d/1fSO48GhJf-fLlAcBjfDzfKNK5tzsVCrM8E50HBlkH2g/edit#) for a step by step guide.

In the rest of this document, we suppose that you have installed galaxy into `$GALAXY` folder, and this `isatools-galaxy` repository into `$ISATOOLS` folder. For instance you may have defined:
```bash
GALAXY=$HOME/dev/galaxy
ISATOOLS=$HOME/dev/isatools-galaxy
```

## Install ISA API (isatools Python module)

Clone ISA API:
```bash
git clone -b isa_hackathon git://github.com/ISA-tools/isa-api.git
```

Install it on your computer:
```bash
cd isa-api
pip3 install --user -e .
```

## Installing the tool manually

### Install the tool XML file

```bash
cd $GALAXY/tools
ln -s $ISATOOLS
```

### Edit the tool conf

if `$HOME/dev/galaxy/config/tool_conf.xml` does not exist, make a copy from `$HOME/dev/galaxy/config/tool_conf.xml.sample`:
```bash
cp $GALAXY/config/tool_conf.xml.sample $GALAXY/config/tool_conf.xml
```

Edit the file `$GALAXY/config/tool_conf.xml` and add the following lines:
```xml
<section id="isa" name="Create ISA Data">
   <tool file="isatools-galaxy/tools/isacreator_metabo/isacreator_metabo.xml" />
</section>
```

### Edit the tool data table conf

if `$HOME/dev/galaxy/config/tool_data_table_conf.xml` does not exist, make a copy from `$HOME/dev/galaxy/config/tool_data_table_conf.xml.sample`:
```bash
cp $GALAXY/config/tool_data_table_conf.xml.sample $GALAXY/config/tool_data_table_conf.xml
```

Edit the file `$GALAXY/config/tool_data_table_conf.xml` and add the following lines:
```xml
	<!-- ISA creator CV terms -->
    <table name="isa_cvterms" comment_char="#">
        <columns>dbkey, name, value</columns>
        <file path="tool-data/isa_cvterms.loc" />
    </table>
```

### Edit galaxy.ini

Edit file `$GALAXY/config/galaxy.ini`, and uncomment lines:
```
...
tool_data_table_config_path = config/tool_data_table_conf.xml
...
tool_data_path = tool-data
...
```

### Install data file

Copy data file:
```bash
cp $ISATOOLS/tools/isacreator_metabo/tool-data/isa_cvterms.loc $GALAXY/tool-data/isa_cvterms.loc
```

## Installing using the install script

The `install_to_gx_and_run.sh` script install the tool for development purposes, and overwrite Galaxy configuration files. So be careful that it will erase your Galaxy configuration if you have any, uninstalling all tools already present in Galaxy.

Run:
```bash
cd $ISATOOLS/tools/isacreator_metabo
./install_to_gx_and_run.sh $GALAXY
```
to install this tool to Galaxy and run Galaxy automatically.

### What does install_to_gx_and_run.sh do?

It copies across the following files:

- `tool_data_table_conf.xml`
- `tool_conf.xml`

into the `config/` subdirectory in the Galaxy root.

It then makes sure that `tool_data_table_config_path` and `tool_data_path` properties in `galaxy.ini` are uncommented out.

Next, it creates the `isatools/` subdirectory in the `tools/` directory of Galaxy and copies across the tool files.

Finally, it runs Galaxy using the standard `run.sh` script.
