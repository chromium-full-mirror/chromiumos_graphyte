# Copyright (c) 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

SHELL := bash

PYLINTRC=pylintrc
PYLINT_OPTIONS=--rcfile=$(PYLINTRC) --msg-template='{path}:{line}: {msg_id}: {msg}'

LINT_BLACKLIST=

LINT_FILES=$(shell find . -name '*.py' -type f | sort)
LINT_WHITELIST=$(filter-out $(LINT_BLACKLIST),$(LINT_FILES))

lint:
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

.PHONY: .phony
