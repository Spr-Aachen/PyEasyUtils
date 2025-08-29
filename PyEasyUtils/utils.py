import inspect
from types import FunctionType, MethodType
from typing import Iterable

#############################################################################################################

def toIterable(
    *items,
    ignoreString: bool = True
):
    """
    Function to make item iterable
    """
    iterableItems = []
    for item in items:
        if hasattr(item, '__iter__'):
            iterableItem = [item] if isinstance(item, (str, bytes)) and ignoreString else item
        else:
            iterableItem = [item]
        #yield from iterableItem
        iterableItems.extend(iterableItem)
    return tuple(iterableItems)# if len(iterableItems) > 1 else iterableItems[0]

#############################################################################################################

def itemReplacer(
    dict: dict,
    items: object
):
    """
    Function to replace item using dictionary lookup
    """
    itemList = toIterable(items, ignoreString = False)

    itemList_new = [dict.get(item, item) for item in itemList]

    if isinstance(items, list):
        return itemList_new
    if isinstance(items, tuple):
        return tuple(itemList_new)
    if isinstance(items, (int, float, bool)):
        return itemList_new[0]
    if isinstance(items, str):
        return str().join(itemList_new)


def findKey(
    dict: dict,
    targetValue: object
):
    """
    Find key from dictionary
    """
    for key, value in dict.items():
        if value == targetValue:
            return key

#############################################################################################################

def getNamesFromMethod(
    method: object
):
    """
    Function to get className and methodName from classmethod
    """
    if type(method) not in [FunctionType, MethodType]:
        raise Exception("Only accept classmethod or function")
    qualName = method.__qualname__
    className, methodName = qualName.split('.') if '.' in qualName else (None, qualName)
    return className, methodName


def getClassFromMethod(
    method: object
):
    """
    Function to get class from classmethod
    """
    className = getNamesFromMethod(method)[0]
    return inspect.getmodule(method).__dict__[className]

#############################################################################################################

def runEvents(
    events: Iterable
):
    """
    Function to run events
    """
    if isinstance(events, dict):
        for event, param in events.items():
            event(*toIterable(param if param is not None else ())) if event is not None else None
    else:
        for event in iter(events):
            event() if event is not None else None

#############################################################################################################