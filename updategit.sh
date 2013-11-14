#!/bin/sh

pushd docs
make html
popd

git add --ignore-removal .
git commit -m "$1" 
git push origin master

