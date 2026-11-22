# Nordwerk Data Platform - shortcuts for Linux / macOS (on Windows: .\run.ps1 <command>)
PY ?= python

.PHONY: install showcase setup run generate check status test unit e2e cov lint
install:  ; $(PY) -m pip install -r requirements.txt
showcase: ; $(PY) manage.py showcase
setup:    ; $(PY) manage.py setup
run:      ; $(PY) manage.py run
generate: ; $(PY) manage.py run --generate
check:    ; $(PY) manage.py check
status:   ; $(PY) manage.py status
test:     ; $(PY) manage.py test all
unit:     ; $(PY) manage.py test unit
e2e:      ; $(PY) manage.py test e2e
cov:      ; $(PY) manage.py test all --cov
lint:     ; $(PY) manage.py lint
