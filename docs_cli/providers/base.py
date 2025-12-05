from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def search(self, query: str, force_refresh: bool = False):
        """
        Neccessary search method for all providers to implement.
        Must return tuple of:
        (url: str, result_text: str, is_from_cache: bool)
        or
        (None, error_details: Any, None)
        """
        pass