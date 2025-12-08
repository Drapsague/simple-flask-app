import pickle
import os

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


class UserCacheManager:
    """
    User cache manager for profile previews.
    Uses internal attributes to build cache file locations.
    """

    def __init__(self, username):
        self.username = username
        self.cache_key = None

    def set_cache_key(self, key):
        self.cache_key = key

    def get_cache_filename(self):
        filename = f"{self.cache_key}_{self.username}.pkl"
        return os.path.join(CACHE_DIR, filename)

    def save_obj(self, obj):
        path = self.get_cache_filename()
        with open(path, "wb") as f:
            pickle.dump(obj, f)

    def load_obj(self):
        path = self.get_cache_filename()
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
