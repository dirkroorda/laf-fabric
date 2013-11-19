#!/bin/sh

pushd docs
make html
#make pdf
make epub
popd

