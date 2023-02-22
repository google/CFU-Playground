import matlab
from matlab import engine
from pathlib import Path

DEFAULT_WD = Path(__file__).parent / "matlab" / "simc_1_functions"


def get_engine(wd = DEFAULT_WD):
    eng = engine.start_matlab()
    eng.cd(str(wd), nargout=0)
    return eng