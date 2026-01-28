import pandas as pd

def load_returns(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)

    # Safety checks
    assert not df.isnull().values.any(), "NaNs detected in returns data"
    assert df.shape[1] >= 2, "Need at least 2 assets"

    return df