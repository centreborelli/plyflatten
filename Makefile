.PHONY: help install test release-patch release-minor release-major

.DEFAULT: help
help:
	@echo "make install"
	@echo "    Install the package in editable mode with the \`dev\` and"
	@echo "    \`test\` extras and run \`pre-commit install\`"
	@echo
	@echo "make test"
	@echo "    Run tests with \`pytest\`"
	@echo
	@echo "make release-{patch,minor,major}"
	@echo "    Increment the version number to the next patch/minor/major"
	@echo "    version (following semanting versioning) using \`bumpversion\`"

install:
	pip install -e ".[dev,test]"
	pre-commit install

BOLD=$$(tput bold)
NORMAL=$$(tput sgr0)

test:
	pytest .

release-patch:
	@# Remove the trailing -dev0 from version number and tag the new version
	bumpversion release --tag
	@echo "${BOLD}Tagged version: $$(bumpversion --dry-run --list patch | grep current_version | cut -d= -f2)${NORMAL}"
	@make dev

release-minor:
	@# Increment to the new minor
	bumpversion minor --no-commit
	@# Remove the trailing -dev0 from version number
	bumpversion release --allow-dirty --tag
	@echo "${BOLD}Tagged version: $$(bumpversion --dry-run --list patch | grep current_version | cut -d= -f2)${NORMAL}"
	@make dev

release-major:
	@# Increment to the new major
	bumpversion major --no-commit
	@# Remove the trailing -dev0 from version number
	bumpversion release --allow-dirty --tag
	@echo "${BOLD}Tagged version: $$(bumpversion --dry-run --list patch | grep current_version | cut -d= -f2)${NORMAL}"
	@make dev

dev:
	@# Increment to the new patch (automatically adds -dev0 to it)
	bumpversion patch --message "Post-release: {new_version}"
	@echo "${BOLD}Current version: $$(bumpversion --dry-run --list patch | grep current_version | cut -d= -f2)${NORMAL}"
