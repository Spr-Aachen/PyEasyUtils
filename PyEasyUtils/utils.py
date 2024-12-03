import collections
collections.Iterable = collections.abc.Iterable
import inspect
from typing import Union

#############################################################################################################

def toIterable(
    items,
    ignoreString: bool = True
):
    '''
    Function to make item iterable
    '''
    if isinstance(items, collections.Iterable) or hasattr(items, '__iter__'):
        ItemList = [items] if isinstance(items, (str, bytes)) and ignoreString else items
    else:
        ItemList = [items]

    return ItemList


def itemReplacer(
    dict: dict,
    items: object
):
    '''
    Function to replace item using dictionary lookup
    '''
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

def getClassFromMethod(
    method: object
):
    """
    Function to get class from method
    """
    '''
    Modules = list(inspect.getmodule(method).__dict__.values())
    Modules = [Module for Module in Modules if str(Module).startswith("<class '__main__.")]
    return Modules[-1]
    '''
    return inspect.getmodule(method).__dict__[method.__qualname__.split('.')[0]]

#############################################################################################################

def runEvents(
    events: Union[list, dict]
):
    """
    Function to run events
    """
    if isinstance(events, list):
        for Event in events:
            Event() if Event is not None else None
    if isinstance(events, dict):
        for Event, Param in events.items():
            Event(*toIterable(Param if Param is not None else ())) if Event is not None else None

#############################################################################################################