FROM debian:testing

ENV RISCV_DIR=/toolchain/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14/bin
ENV PATH="/third_party/renode:${RISCV_DIR}:${PATH}"
ARG WORKDIR=/CFU-Playground

RUN apt update -y && apt install -y wget git python3-pip make gcc openocd yosys expect ccache verilator libevent-dev libjson-c-dev libusb-1.0-0-dev libftdi1-dev vim && rm -rf /var/lib/apt/lists/*

RUN mkdir /toolchain && cd /toolchain && wget -nv https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz && tar xf riscv64*tar.gz && rm riscv64*tar.gz

RUN mkdir /third_party/renode && wget -nv https://dl.antmicro.com/projects/renode/builds/renode-latest.linux-portable.tar.gz && tar xf renode-*tar.gz -C /third_party/renode --strip-components=1 && rm renode-*tar.gz && python3 -m pip install -r /third_party/renode/tests/requirements.txt

RUN git clone https://github.com/google/CFU-Playground ${WORKDIR}
WORKDIR ${WORKDIR}

RUN ./scripts/setup -ci
