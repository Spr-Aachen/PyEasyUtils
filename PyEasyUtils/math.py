from decimal import Decimal
from typing import Union

#############################################################################################################

def getDecimalPlaces(
    number: Union[int, float]
):
    """
    Function to get decimal places of a number
    """
    return abs(Decimal(str(number)).as_tuple().exponent)

#############################################################################################################