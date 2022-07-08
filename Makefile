
# The top directory where environment will be created.
TOP_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

ifdef USE_SYMBIFLOW

# A pip `requirements.txt` file.
# https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
REQUIREMENTS_FILE := $(TOP_DIR)/conf/requirements-symbiflow.txt

# A conda `environment.yml` file.
# https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
ENVIRONMENT_FILE := $(TOP_DIR)/conf/environment-symbiflow.yml

else

# A pip `requirements.txt` file.
# https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
REQUIREMENTS_FILE := $(TOP_DIR)/conf/requirements.txt

# A conda `environment.yml` file.
# https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
ENVIRONMENT_FILE := $(TOP_DIR)/conf/environment.yml

endif


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

F4PGA_TIMESTAMP=20220729-181657
F4PGA_HASH=7833050

install-sf:
	@if [ -d "$(SF_INSTALL)" ]; then \
		echo ; \
		echo "$(SF_INSTALL) already exists.  Remove it if you want to reinstall."; \
		echo ; \
		exit 1; \
	fi
<<<<<<< HEAD
	@mkdir -p $(SF_INSTALL)/xc7/install
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/${F4PGA_TIMESTAMP}/symbiflow-arch-defs-install-xc7-${F4PGA_HASH}.tar.xz | tar -xJC $(SF_INSTALL)/xc7/install
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/${F4PGA_TIMESTAMP}/symbiflow-arch-defs-xc7a50t_test-${F4PGA_HASH}.tar.xz | tar -xJC $(SF_INSTALL)/xc7/install
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/${F4PGA_TIMESTAMP}/symbiflow-arch-defs-xc7a100t_test-${F4PGA_HASH}.tar.xz | tar -xJC $(SF_INSTALL)/xc7/install
	wget -qO- https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/${F4PGA_TIMESTAMP}/symbiflow-arch-defs-xc7a200t_test-${F4PGA_HASH}.tar.xz | tar -xJC $(SF_INSTALL)/xc7/install
=======
	@mkdir -p $(SF_INSTALL)
	
	wget -qO- "https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/20220523-230829/symbiflow-arch-defs-install-934b12d.tar.xz" | tar -xJC $(SF_INSTALL)
	wget -qO- "https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/20220523-230829/symbiflow-arch-defs-xc7a50t_test-934b12d.tar.xz" | tar -xJC $(SF_INSTALL)
	wget -qO- "https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/20220523-230829/symbiflow-arch-defs-xc7a100t_test-934b12d.tar.xz" | tar -xJC $(SF_INSTALL)
	wget -qO- "https://storage.googleapis.com/symbiflow-arch-defs/artifacts/prod/foss-fpga-tools/symbiflow-arch-defs/continuous/install/20220523-230829/symbiflow-arch-defs-xc7z010_test-934b12d.tar.xz" | tar -xJC $(SF_INSTALL)
	
	#wget -qO- "https://www.googleapis.com/download/storage/v1/b/symbiflow-arch-defs/o/artifacts%2Fprod%2Ffoss-fpga-tools%2Fsymbiflow-arch-defs%2Fcontinuous%2Finstall%2F497%2F20211222-000718%2Fsymbiflow-arch-defs-install-f9aa1caf.tar.xz?generation=1640179068316994&alt=media" | tar -xJC $(SF_INSTALL)
	#wget -qO- "https://www.googleapis.com/download/storage/v1/b/symbiflow-arch-defs/o/artifacts%2Fprod%2Ffoss-fpga-tools%2Fsymbiflow-arch-defs%2Fcontinuous%2Finstall%2F497%2F20211222-000718%2Fsymbiflow-arch-defs-xc7a50t_test-f9aa1caf.tar.xz?generation=1640179069641023&alt=media" | tar -xJC $(SF_INSTALL)
	#wget -qO- "https://www.googleapis.com/download/storage/v1/b/symbiflow-arch-defs/o/artifacts%2Fprod%2Ffoss-fpga-tools%2Fsymbiflow-arch-defs%2Fcontinuous%2Finstall%2F497%2F20211222-000718%2Fsymbiflow-arch-defs-xc7a100t_test-f9aa1caf.tar.xz?generation=1640179071622610&alt=media" | tar -xJC $(SF_INSTALL)
	#wget -qO- "https://www.googleapis.com/download/storage/v1/b/symbiflow-arch-defs/o/artifacts%2Fprod%2Ffoss-fpga-tools%2Fsymbiflow-arch-defs%2Fcontinuous%2Finstall%2F497%2F20211222-000718%2Fsymbiflow-arch-defs-xc7a200t_test-f9aa1caf.tar.xz?generation=1640179073346556&alt=media" | tar -xJC $(SF_INSTALL)
>>>>>>> Update Makefile
	$(MAKE) USE_SYMBIFLOW=1 env
	@echo
	@echo "Done installing SymbiFlow.  To enter the environment, type 'make enter-sf', which creates a new subshell, and 'exit' when done."
	@echo

enter-sf:
	-@export F4PGA_INSTALL_DIR=$(TOP_DIR)/$(SF_INSTALL) && $(MAKE) USE_SYMBIFLOW=1 enter


.PHONY: enter-sf install-sf info
