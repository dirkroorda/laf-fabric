#!/bin/sh

git rm -r -f '*.DS_Store'

# Compiled source #
###################
git rm --cached -r -f '*.com'
git rm --cached -r -f '*.class'
git rm --cached -r -f '*.dll'
git rm --cached -r -f '*.exe'
git rm --cached -r -f '*.o'
git rm --cached -r -f '*.so'

# Packages #
############
# it's better to unpack these files and commit the raw source
# git has its own built in compression methods
git rm --cached -r -f '*.7z'
git rm --cached -r -f '*.dmg'
git rm --cached -r -f '*.gz'
git rm --cached -r -f '*.iso'
git rm --cached -r -f '*.jar'
git rm --cached -r -f '*.rar'
git rm --cached -r -f '*.tar'
git rm --cached -r -f '*.zip'

# Logs and databases #
######################
git rm --cached -r -f '*.log'
git rm --cached -r -f '*.sql'
git rm --cached -r -f '*.sqlite'

# OS generated files #
######################
git rm --cached -r -f '.DS_Store'
git rm --cached -r -f '.DS_Store?'
git rm --cached -r -f '._*'
git rm --cached -r -f '.Spotlight-V100'
git rm --cached -r -f '.Trashes'
git rm --cached -r -f 'ehthumbs.db'
git rm --cached -r -f 'Thumbs.db'

# Temporary files #
###################
git rm --cached -r -f '*.swp'
git rm --cached -r -f '*.pyc'

git add --ignore-removal .
git commit -m "remove junk" 
git push origin master
