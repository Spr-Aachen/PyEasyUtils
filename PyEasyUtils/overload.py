from typing import Optional, Type, Callable, Any
from functools import singledispatch, wraps

#############################################################################################################

class singledispatchmethod:
    '''
    Single-dispatch generic method descriptor.

    Supports wrapping existing descriptors and handles non-descriptor callables as instance methods.
    '''
    def __init__(self, method: Callable):
        if not (callable(method) and hasattr(method, "__get__")):
            raise TypeError(f"{method!r} is not callable or a descriptor")

        self.method = method

        self.dispatcher = singledispatch(method)

    def register(self, cls: Type, method: Optional[Callable] = None):
        '''
        Register a new implementation for the given class on a generic method.

        :param cls: The class to register the method for.
        :param method: The method to register. If None, returns a decorator.
        :return: A decorator function if method is None, otherwise None.
        '''
        return self.dispatcher.register(cls, func = method)

    @property
    def isAbstractMethod(self) -> bool:
        '''
        Check if the method is an abstract method.
        '''
        return getattr(self.method, '__isabstractmethod__', False)

    def __get__(self, obj: Any, cls: Optional[Type] = None):
        @wraps(self.method)
        def method(*args, **kwargs):
            '''
            Ref: https://stackoverflow.com/questions/24601722
            '''
            if args:
                method = self.dispatcher.dispatch(args[0].__class__)
            else:
                method = self.method
                for v in kwargs.values():
                    if v.__class__ in self.dispatcher.registry:
                        method = self.dispatcher.dispatch(v.__class__)
                        if method is not self.method:
                            break
            return method.__get__(obj, cls)(*args, **kwargs)
        method.register = self.register
        method.__isabstractmethod__ = self.isAbstractMethod
        return method

#############################################################################################################