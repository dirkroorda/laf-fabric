#!/bin/sh

pushd docs
make html
popd

git commit -a -m "Release $1" 
git push origin master
