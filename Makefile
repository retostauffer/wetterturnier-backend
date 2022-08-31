

# Create tarball for autosubmit.
asversion:=$(shell cat autosubmit/autosubmit.py | egrep VERSION | sed 's/.*VERSION://g')

autosubmit: SHELL:=/bin/bash
.PHONY: autosubmit
autosubmit:
	tar -cvzf autosubmit_$(shell printf "%s" ${asversion}).tar.gz \
		autosubmit/autosubmit.py autosubmit/autosubmit_MyFile*

