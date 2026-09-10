import os
os.environ.setdefault("OPENBLAS_NUM_THREADS","2")
os.environ.setdefault("OMP_NUM_THREADS","2")
from carespace.pipeline import run_study
if __name__=="__main__":run_study()
