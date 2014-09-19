#!/bin/sh

cd ~
zip -r laf-fabric-data.zip laf-fabric-data/laf-fabric.cfg laf-fabric-data/etcbc4/[abcdm]* laf-fabric-data/calap/[abcdm]* laf-fabric-data/px
mv laf-fabric-data.zip ~/Dropbox/DANS/current/demos/apps/shebanq/results_latest/laf-fabric-data.zip
