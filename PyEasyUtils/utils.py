import inspect
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
    ItemList = toIterable(items, ignoreString = False)

    ItemList_New = [dict.get(Item, Item) for Item in ItemList]

    if isinstance(items, list):
        return ItemList_New
    if isinstance(items, tuple):
        return tuple(ItemList_New)
    if isinstance(items, (int, float, bool)):
        return ItemList_New[0]
    if isinstance(items, str):
        return str().join(ItemList_New)


def findKey(
    dict: dict,
    targetValue
):
    """
    Find key from dictionary
    """
    for Key, value in dict.items():
        if value == targetValue:
            return Key

#############################################################################################################

def getNamesFromMethod(
    method: object
):
    """
    Function to get qualName and methodName from classmethod
    """
    qualName = str(method.__qualname__)
    methodName = qualName.split('.')[1]
    return qualName, methodName


def getClassFromMethod(
    method: object
):
    """
    Function to get class from classmethod
    """
    '''
    Modules = list(inspect.getmodule(method).__dict__.values())
    Modules = [Module for Module in Modules if str(Module).startswith("<class '__main__.")]
    return Modules[-1]
    '''
    return inspect.getmodule(method).__dict__[method.__qualname__.split('.')[0]]

#############################################################################################################

def runEvents(
    events: Iterable
):
    """
    Function to run events
    """
    if isinstance(events, dict):
        for Event, Param in events.items():
            Event(*toIterable(Param if Param is not None else ())) if Event is not None else None
    else:
        for Event in iter(events):
            Event() if Event is not None else None

#############################################################################################################