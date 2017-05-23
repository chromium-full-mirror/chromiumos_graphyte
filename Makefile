# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

SHELL := bash

PYTHON=python

PYLINTRC=pylintrc
PYLINT_OPTIONS=--rcfile=$(PYLINTRC) --msg-template='{path}:{line}: {msg_id}: {msg}'

FORMATS=gztar

LINT_BLACKLIST=
LINT_FILES=$(shell find . -name '*.py' -type f | sort)
LINT_WHITELIST=$(filter-out $(LINT_BLACKLIST),$(LINT_FILES))

UNITTEST_RUNNER=./unittest_runner.py
UNITTEST_BLACKLIST=
UNITTEST_FILES=$(shell find . -name '*_unittest.py' | sort)
UNITTEST_WHITELIST=$(filter-out $(UNITTEST_BLACKLIST), $(UNITTEST_FILES))

.PHONY: .phony

default: .phony
	#no build step is required

install: .phony
	pip install .

dist: .phony
	python setup.py sdist --formats=$(FORMATS)

clean: .phony
	rm -rf build dist MANIFEST graphyte.egg-info overlay-*

lint: .phony
	@set -e -o pipefail; \
	out=$$(mktemp); \
	echo Linting $(shell echo $(LINT_WHITELIST) | wc -w) files...; \
	if [ -n "$(LINT_WHITELIST)" ] && \
	    ! pylint $(PYLINT_OPTIONS) $(LINT_WHITELIST) \
	    |& tee $$out; then \
	  echo; \
	  echo To re-lint failed files, run:; \
	  echo make lint LINT_WHITELIST=\""$$( \
	    grep '^\*' $$out | cut -c22- | tr . / | \
	    sed 's/$$/.py/' | tr '\n' ' ' | sed -e 's/ $$//')"\"; \
	  echo; \
	  rm -f $$out; \
	  exit 1; \
	fi; \
	echo ...no lint errors! You are awesome!; \
	rm -f $$out

test: .phony
	@set -e
	$(PYTHON) $(UNITTEST_RUNNER) $(UNITTEST_WHITELIST)

overlay-%: .phony
	rm -rf $@
	mkdir $@
	rsync -aK graphyte pylintrc Makefile $(UNITTEST_RUNNER) $@/
	overlay_name="$(subst overlay-,,$@)"; \
	for prefix in \
	    "partner_private" \
	    "private-overlays/project-goofy-private/chromeos-base" \
	    "private-overlays/overlay-$${overlay_name}-private/chromeos-base"; \
	do \
	  path="../../$${prefix}/graphyte-$${overlay_name}"; \
	  if [ -e "$${path}" ]; then \
	    rsync -aK $${path}/graphyte $@/; \
	  fi; \
	done

lint-overlay-%: overlay-%
	make -C $< lint; \
	rm -rf $(subst lint-,,$@)

test-overlay-%: overlay-%
	make -C $< test; \
	rm -rf $(subst test-,,$@)
