import inspect
import signal
from typing import Type, TypeVar, List, Dict

T = TypeVar('T')

def instanciate_empty_instance(type: Type[T]) -> T:
    constructor_arguments: List = list(inspect.signature(type.__init__).parameters.keys())
    arguments: Dict = {key: None for key in constructor_arguments if not key == "self"}
    try:
        empty_instance: T = type(**arguments)
    except TypeError:
        empty_instance = type()
    return empty_instance

def get_variables_of_type(instance: T) -> List[str]:
    variables = list(vars(instance).items())
    without_protected = [key for key, value in variables if not key.startswith("_")
                         and not callable(value)]
    return without_protected


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
