#!/usr/bin/env bash

# point to a Galaxy source somewhere
GALAXY_ROOT=$1

cp galaxy/config/tool_data_table_conf.xml $GALAXY_ROOT/config/tool_data_table_conf.xml
cp galaxy/config/tool_conf.xml $GALAXY_ROOT/config/tool_conf.xml

sed 's/#tool_data_table_config_path/tool_data_table_config_path/' $GALAXY_ROOT/config/galaxy.ini.sample > $GALAXY_ROOT/config/galaxy.ini.tmp
sed 's/#tool_data_path/tool_data_path/' $GALAXY_ROOT/config/galaxy.ini.tmp > $GALAXY_ROOT/config/galaxy.ini
rm $GALAXY_ROOT/config/galaxy.ini.tmp

cp tool-data/isa_cvterms.loc $GALAXY_ROOT/tool-data/isa_cvterms.loc

mkdir -p $GALAXY_ROOT/tools/isatools/
cp isacreator_metabo.py $GALAXY_ROOT/tools/isatools/isacreator_metabo.py
cp isacreator_metabo.xml $GALAXY_ROOT/tools/isatools/isacreator_metabo.xml
cp isacreator_metabo_macros.xml $GALAXY_ROOT/tools/isatools/isacreator_metabo_macros.xml

$GALAXY_ROOT/run.sh
