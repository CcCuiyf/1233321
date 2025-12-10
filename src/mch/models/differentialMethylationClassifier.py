import logging
import os
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import NotFittedError

# ---- R / rpy2 env setting -------------------------------------------------------

os.environ.setdefault("R_ENABLE_JIT", "0")

os.environ.setdefault("R_LIBS_USER", "/databricks/rlibs")

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.rinterface_lib.callbacks import logger as rpy2_logger

rpy2_logger.setLevel(logging.ERROR)

try:
    robjects.r(
        '.libPaths(unique(c("/databricks/rlibs", .libPaths())))'
    )
    # Try load limma
    robjects.r('suppressPackageStartupMessages(library(limma))')
    print("[R INIT] limma loaded successfully via rpy2")
except Exception as e:
    print(f"[R INIT] Failed to configure R libPaths or load limma: {e}")

pd.DataFrame.iteritems = pd.DataFrame.items


class DifferentialMethylation(BaseEstimator, TransformerMixin):
    """
    Use limma to apply Methylation analysis using sklearn Transformer
    - fit: for each cancerType use runDM, collect differentially methylated probes
    - transform: only keep these differentially methylated probes in the dataset
    """

    def __init__(self):
        self.tempFileLocation = "/tmp/"
        self.result = None  # cancer type alias to list of differentially methylated probes
        self.design = None

    # X: DataFrame (sample x probe), index is sampleId
    # y: Series (label, e.g. cancerType)
    def fit(self, X: pd.DataFrame, y: pd.Series):
        print("fitting via limma")

        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            print("DM skip: only one class present, no differential methylation possible")
            self.result = []   # 表示不选特征
            return self
        
        cancerTypes = y.unique()
        combined_result = []

        n = 1
        for cancerType in cancerTypes:
            print(
                f"probe identification for: {cancerType}, "
                f"{n} of {len(cancerTypes)} cancer types"
            )
            n += 1

            condition = pd.Series(
                np.where(y == cancerType, cancerType, "otherCancerType")
            )
            results = self.runDifferentialMethylation(X, condition)
            combined_result = combined_result + results

        combined_result = list(set(combined_result))
        print(
            f"Number of probes identified from differential methylation analyses: "
            f"{len(combined_result)}"
        )
        self.result = combined_result
        return self

    def transform(self, X: pd.DataFrame):
        print("transforming via limma")

        if len(self.result) == 0:
            # 不筛选特征，直接返回 X
            return X

        if self.result is None:
            raise NotFittedError("Transformer must be fitted before transforming data.")

        print("transforming dataset to contain only differentially methylated features")

        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        elif not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X = X.copy()
        X.columns = X.columns.astype(str)

        return X[self.result]

    # inner：for single cancerType vs otherCancerType do limma analysis
    def runDifferentialMethylation(self, X: pd.DataFrame, y: pd.Series):
        print("Running analysis")


        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        elif not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        if isinstance(y, (np.ndarray, list, tuple)):
            y = pd.Series(y)
        elif not isinstance(y, pd.Series):
            y = pd.Series(y)


        X = X.apply(pd.to_numeric, errors="coerce")
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.dropna(axis="columns")

        design = pd.DataFrame(
            {
                "sampleId": pd.Series(X.index, dtype="string"),
                "cancerType": y.values,
            }
        )

        arrowData = self.convert_to_arrow(X)
        arrowDesign = self.convert_to_arrow(design)

        dataFilename = self.save_to_file(arrowData)
        designFilename = self.save_to_file(arrowDesign)

        try:
            result = self.run_r_script(dataFilename, designFilename)
        finally:
            try:
                os.remove(dataFilename)
            except OSError:
                pass
            try:
                os.remove(designFilename)
            except OSError:
                pass

        return result

    def run_r_script(self, data_filename: str, design_filename: str):
        r_script_path = Path(__file__).with_name("differentialMethylation.R")
        if not r_script_path.exists():
            raise FileNotFoundError(f"R script not found: {r_script_path}")

        robjects.r("options(rpy2_quiet = TRUE)")

        robjects.r["source"](str(r_script_path))

        if "runDM" not in robjects.globalenv:
            raise RuntimeError(
                "runDM not found in R global environment after sourcing "
                f"{r_script_path}"
            )

        runDM = robjects.globalenv["runDM"]

        fit = runDM(data_filename, design_filename)

        # R object -> Python object
        with (robjects.default_converter + pandas2ri.converter).context():
            py_obj = robjects.conversion.get_conversion().rpy2py(fit)

        probes: list[str] = []
        if isinstance(py_obj, pd.DataFrame):
            if py_obj.index.size > 0:
                probes = list(py_obj.index.astype(str))
            else:
                probes = [
                    str(c)
                    for c in py_obj.columns
                    if c not in ("sampleId", "cancerType", "Name")
                ]
        elif isinstance(py_obj, pd.Series):
            probes = [str(x) for x in py_obj.tolist()]
        elif isinstance(py_obj, (list, tuple, np.ndarray)):
            probes = [str(x) for x in list(py_obj)]
        else:
            logging.warning(
                "runDM returned unsupported type: %s; fallback to empty list",
                type(py_obj),
            )

        return probes

    def convert_to_arrow(self, df: pd.DataFrame) -> pa.Table:

        df = df.copy()
        df.columns = df.columns.map(str)

        schema_fields = []
        for col in df.columns:
            if col in ("sampleId", "cancerType", "Name"):
                schema_fields.append((col, pa.string()))
            else:
                schema_fields.append((col, pa.float64()))

        schema = pa.schema(schema_fields)
        arrowFrame = pa.Table.from_pandas(df, schema=schema)
        return arrowFrame

    def save_to_file(self, arrowFrame: pa.Table) -> str:
        location = self.tempFileLocation
        randomElement = str(uuid.uuid4())
        fileName = os.path.join(location, randomElement + ".feather")
        feather.write_feather(arrowFrame, fileName)
        return fileName
