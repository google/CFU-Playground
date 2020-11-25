from nmigen import *
from nmigen.back import rtlil, verilog

from cfu import Cfu


def main():
    cfu = Cfu()
    with open("cfu.v", "w") as f:
        f.write(verilog.convert(cfu, name='Cfu', ports=cfu.ports))

if __name__ == '__main__':
    main()
