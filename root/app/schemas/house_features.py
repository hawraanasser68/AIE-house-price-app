from pydantic import BaseModel
from typing import Optional, List

#inputs to ml model
class HouseFeatures(BaseModel):
    # ===== NUMERIC FEATURES =====
    OverallQual: Optional[int] = None
    GrLivArea: Optional[float] = None
    GarageCars: Optional[int] = None
    TotalBsmtSF: Optional[float] = None
    FullBath: Optional[int] = None
    YearBuilt: Optional[int] = None
    YearRemodAdd: Optional[int] = None

    # ===== CATEGORICAL FEATURES =====
    ExterQual: Optional[str] = None
    KitchenQual: Optional[str] = None
    BsmtQual: Optional[str] = None
    Neighborhood: Optional[str] = None
    MSZoning: Optional[str] = None
