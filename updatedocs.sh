#!/bin/sh

pushd docs
rm -r _build/html
make html
rm -r _build/epub
make epub
popd

