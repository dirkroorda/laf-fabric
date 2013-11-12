#!/bin/sh

git add .
git rm -r -f '*.pyc'
git rm -r -f '*.swp'
git rm -r -f '.DS_Store'
git commit -m "$1" 
git push origin master

