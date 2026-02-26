import pandas as pd

class DataFrame:
    def __init__(self, data):
        if isinstance(data, pd.DataFrame):
            self._df = data
        else:
            self._df = pd.DataFrame(data)

    def where(self, condition_func):
        if callable(condition_func):
            return DataFrame(self._df[condition_func(self._df)])
        return DataFrame(self._df[condition_func])

    def select(self, *columns):
        return DataFrame(self._df[list(columns)])

    def avg_by(self, column):
        return DataFrame(self._df.groupby(column).mean())

    def resample(self, rule):
        return DataFrame(self._df.resample(rule).mean())

    def scale(self):
        print("Scaling numerical features...")
        return DataFrame((self._df - self._df.mean()) / self._df.std())

    def encode(self, column):
        print(f"One-hot encoding {column}...")
        return DataFrame(pd.get_dummies(self._df, columns=[column]))

    def to_parquet(self, path):
        print(f"Saving to Parquet: {path}")
        self._df.to_parquet(path)

    def __getattr__(self, name):
        return getattr(self._df, name)

    def __repr__(self):
        return repr(self._df)

__all__ = ["DataFrame"]
