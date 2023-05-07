import serial
import threading
import time
from argparse import ArgumentParser
import numpy as np


def read_serial(print_lines=True, n_measurements=-1):
    before = 0
    after = 0
    i = 0
    measurements = []

    with serial.Serial("/dev/ttyUSB1", 1843200, timeout=10000) as ser:
        while True:
            line = ser.readline().decode()
            if "//measure_time_anchor_start" in line:
                before = time.time()
            if "//measure_time_anchor_end" in line:
                after = time.time()
                t = after - before
                if print_lines:
                    print(f"\n\nMeasured execution time: {t}s\n")
                measurements.append(t)
                i += 1
                if i == n_measurements:
                    measurements = np.array(measurements)
                    print(f"Mean (sec):    {np.mean(measurements)}")
                    print(f"Min (sec):     {np.min(measurements)}")
                    print(f"Max (sec):     {np.max(measurements)}")
                    print(f"Max-Min (sec): {np.max(measurements) - np.min(measurements)}")
                    print(f"STD (sec):     {np.std(measurements)}")
                    return

            if print_lines:
                print(line, end="")


def main_interactive():
    thread = threading.Thread(target=read_serial)
    thread.start()

    with serial.Serial("/dev/ttyUSB1", 1843200, timeout=10000) as ser:
        while True:
            inp = input(">>> ")
            ser.write(inp.encode())


def main(verbose: bool, n_measurements: int):
    thread = threading.Thread(
        target=read_serial, kwargs={"print_lines": verbose, "n_measurements": n_measurements}
    )
    thread.start()

    with serial.Serial("/dev/ttyUSB1", 1843200, timeout=10000) as ser:
        input("Press any key to continue... ")
        print("1")
        ser.write("1".encode())
        print("1")
        ser.write("1".encode())
        print("g")
        ser.write("g".encode())
        # for _ in range(n_measurements):
        #     print("g")
        #     ser.write("g".encode())
            
    thread.join()


if __name__ == "__main__":
    parser = ArgumentParser("measure time over uart")
    parser.add_argument("-i", "--interactive", action="store_const", const=True, default=False)
    parser.add_argument("-n", "--n_measurements", default=10, type=int)
    parser.add_argument("-v", "--verbose", action="store_const", const=True, default=False)
    args = parser.parse_args()

    if args.interactive:
        main_interactive()
    else:
        main(args.verbose, args.n_measurements)
