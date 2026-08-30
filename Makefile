SHELL := /bin/bash

CASE_ID ?= 案例编号：____
POLE_DB ?= /Users/zhangyuxi/Desktop/000基础数据/pole_data.db
PYTHON ?= /Users/zhangyuxi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
NODE ?= /Users/zhangyuxi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
NODE_MODULES ?= /Users/zhangyuxi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules
CHROME_PATH ?= /Applications/Google Chrome.app/Contents/MacOS/Google Chrome

export CASE_ID POLE_DB PYTHON NODE NODE_MODULES CHROME_PATH

.DEFAULT_GOAL := all

.PHONY: all data assets deck report script pdf verify privacy-check doctor open clean help

all: report deck script verify

data:
	@mkdir -p data .build
	@"$(PYTHON)" scripts/build_data.py

assets: data
	@mkdir -p assets/images .build/visuals
	@"$(PYTHON)" scripts/sanitize_photos.py
	@NODE_PATH="$(NODE_MODULES)" "$(NODE)" scripts/export_visuals.mjs

deck: assets
	@mkdir -p dist .build
	@NODE_PATH="$(NODE_MODULES)" "$(NODE)" scripts/build_deck.mjs
	@NODE_PATH="$(NODE_MODULES)" "$(NODE)" scripts/build_pdf.mjs

report: assets
	@mkdir -p dist .build/report-render
	@"$(PYTHON)" scripts/build_report.py

script:
	@mkdir -p dist .build/script-render
	@"$(PYTHON)" scripts/build_script.py

verify:
	@"$(PYTHON)" scripts/verify.py

privacy-check:
	@"$(PYTHON)" scripts/privacy_check.py

doctor:
	@"$(PYTHON)" scripts/doctor.py

open: all
	@open dist 2>/dev/null || true

clean:
	@rm -rf .build dist
	@mkdir -p .build dist

help:
	@echo 'make all                         构建报告、交互答辩、PDF和逐字稿'
	@echo 'make data POLE_DB="/path/db"     重建全省脱敏演示数据'
	@echo 'make report | deck | script      单独构建一种成果'
	@echo 'make verify                       完整质量验收'
	@echo 'make privacy-check                隐私与坐标泄露检查'

