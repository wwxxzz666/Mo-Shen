import warnings

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

try:
    import langchain_core  # noqa: F401
except ImportError:
    pass

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects`.*",
    category=PendingDeprecationWarning,
)

from .default_config import DEFAULT_STORY_CONFIG
from .graph.story_graph import StoryAgentsGraph

__all__ = ["DEFAULT_STORY_CONFIG", "StoryAgentsGraph"]
