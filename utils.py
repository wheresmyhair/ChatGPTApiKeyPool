import logging
from typing import List, Dict


logger = logging.getLogger(__name__)


class NoAvailableAPIKey(Exception):
    pass


class APIKeyPool:
    def __init__(self, api_keys: List[str]):
        self.available_keys = list(set(api_keys))
        self.removed_keys = []
        self.pending_keys: Dict = {}
        self.cooling_keys = []
        
    def has_key(self):
        return len(self.available_keys) > 0

    def get_key(self):
        if not self.has_key():
            if len(self.cooling_keys) == 0:
                raise NoAvailableAPIKey
            else:
                self.available_keys = self.cooling_keys
                self.cooling_keys = []
                logger.info(f"API keys cooling down: {self.available_keys}")
        return self.available_keys[0]

    def remove_key(self, key):
        self.available_keys.remove(key)
        self.removed_keys.append(key)
        self.pending_keys.pop(key, None)
        
    def pending_key(self, key):
        if key in self.pending_keys.keys():
            self.pending_keys[key] += 1
        else:
            self.pending_keys[key] = 1
            
        if self.pending_keys[key] > 5: # remove key if it has been pending for more than 5 times
            self.remove_key(key)
        else:
            self.cooling_key(key)
            
    def cooling_key(self, key):
        self.cooling_keys.append(key)
        self.available_keys.remove(key)
