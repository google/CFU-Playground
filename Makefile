
# The top directory where environment will be created.
TOP_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

# A pip `requirements.txt` file.
# https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
REQUIREMENTS_FILE := $(TOP_DIR)/conf/requirements.txt

# A conda `environment.yml` file.
# https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
ENVIRONMENT_FILE := $(TOP_DIR)/conf/environment.yml

include third_party/make-env/conda.mk

# Example make target which runs commands inside the conda environment.
test-command: | $(CONDA_ENV_PYTHON)
	@$(IN_CONDA_ENV) echo "Python is $$(which python)"
	@$(IN_CONDA_ENV) python --version


info:
	@echo TOP_DIR: $(TOP_DIR)

SF_INSTALL=env/symbiflow

help:
	@echo
	@echo ================================================================
	@echo " To install SymbiFlow, type 'make install-sf'."
	@echo
	@echo " To enter the SymbiFlow environment so that you can use it,"
	@echo "   type "make enter-sf".  This puts you in a subshell with"
	@echo "   everything set up; type 'exit' to leave."
	@echo ================================================================
	@echo


install-sf:
	@if [ -d "$(SF_INSTALL)" ]; then \
		echo ; \
		echo "$(SF_INSTALL) already exists.  Remove it if you want to reinstall."; \
		echo ; \
		exit 1; \
	fi
	@mkdir -p $(SF_INSTALL)
	@/bin/cp conf/environment-symbiflow.yml conf/environment.yml
	@/bin/cp conf/requirements-symbiflow.txt conf/requirements.txt
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/459/20211116-000105/symbiflow-arch-defs-install-ef6fff3c.tar.xz | tar -xJC $(SF_INSTALL)
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/459/20211116-000105/symbiflow-arch-defs-xc7a50t_test-ef6fff3c.tar.xz | tar -xJC $(SF_INSTALL)
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/459/20211116-000105/symbiflow-arch-defs-xc7a100t_test-ef6fff3c.tar.xz | tar -xJC $(SF_INSTALL)
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/459/20211116-000105/symbiflow-arch-defs-xc7a200t_test-ef6fff3c.tar.xz | tar -xJC $(SF_INSTALL)
	$(MAKE) env
	@echo
	@echo "Done installing SymbiFlow.  To enter the environment, type 'make enter-sf', which creates a new subshell, and 'exit' when done."
	@echo

enter-sf:
	-@export PATH=$(TOP_DIR)/env/symbiflow/bin:$(PATH) && $(MAKE) enter


.PHONY: enter-sf install-sf info
