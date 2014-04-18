#!/bin/sh

cd ~
zip -er -p wajehior laf-fabric-data.zip laf-fabric-data/laf-fabric.cfg laf-fabric-data/bhs3/[abcdm]* laf-fabric-data/calap/[abcdm]*
mv laf-fabric-data.zip ~/Dropbox/DANS/current/demos/apps/shebanq/results_latest/laf-fabric-data.zip
