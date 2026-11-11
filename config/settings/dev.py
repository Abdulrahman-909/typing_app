from .base import *

DEBUG = True

# Single-process development only. Production uses Redis.
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
