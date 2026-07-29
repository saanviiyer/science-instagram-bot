"""Account configuration for the science-Instagram pipeline.

Each account maps to one or more Nature per-subject RSS feeds, a pool of
hashtags, and (later) the Instagram Graph API credentials needed to publish.

Credentials are NOT stored here. Each account names an env var that will hold
its long-lived access token, plus its Instagram Business account id. Until those
accounts exist and tokens are provided, the publish step runs in dry-run only.

Nature subject feeds: https://www.nature.com/subjects/<slug>.rss
"""

# Base URL template for Nature subject feeds.
NATURE_FEED = "https://www.nature.com/subjects/{slug}.rss"

# Shared hashtags every science post can draw from.
COMMON_TAGS = ["#science", "#research", "#nature", "#scientificdiscovery", "#stem"]

# Publication these accounts cite as the source.
SOURCE_NAME = "Nature"

ACCOUNTS = {
    "chemistrynews": {
        "display_name": "Chemistry News",
        "feeds": ["chemistry"],
        "topic_line": "the latest chemistry research",
        "hashtags": [
            "#chemistry", "#chem", "#chemist", "#organicchemistry",
            "#materialsscience", "#catalysis", "#molecules", "#lablife",
        ],
    },
    "biologynews": {
        "display_name": "Biology News",
        "feeds": ["biological-sciences"],
        "topic_line": "new discoveries in biology",
        "hashtags": [
            "#biology", "#biotech", "#genetics", "#cellbiology",
            "#molecularbiology", "#evolution", "#microbiology", "#lifesciences",
        ],
    },
    "physicsnews": {
        "display_name": "Physics News",
        "feeds": ["physics"],
        "topic_line": "breakthroughs in physics",
        "hashtags": [
            "#physics", "#physicist", "#quantumphysics", "#astrophysics",
            "#particlephysics", "#condensedmatter", "#theoreticalphysics", "#optics",
        ],
    },
    "quantumnews": {
        "display_name": "Quantum News",
        "feeds": ["quantum-information"],
        "topic_line": "advances in quantum science",
        "hashtags": [
            "#quantum", "#quantumcomputing", "#quantumphysics", "#qubits",
            "#quantuminformation", "#superconductors", "#entanglement", "#quantumtech",
        ],
    },
    "environmentalnews": {
        "display_name": "Environmental News",
        "feeds": ["environmental-sciences"],
        "topic_line": "environmental science research",
        "hashtags": [
            "#environment", "#climate", "#climatechange", "#sustainability",
            "#ecology", "#conservation", "#earthscience", "#climatescience",
        ],
    },
    "spacenews": {
        "display_name": "Space News",
        "feeds": ["space-physics"],
        "topic_line": "the newest space and astrophysics research",
        "hashtags": [
            "#space", "#astronomy", "#astrophysics", "#cosmos",
            "#nasa", "#exoplanets", "#universe", "#spacescience",
        ],
    },
    "neuronews": {
        "display_name": "Neuroscience News",
        "feeds": ["neuroscience"],
        "topic_line": "neuroscience and brain-computer interface research",
        "hashtags": [
            "#neuroscience", "#brain", "#neuro", "#bci",
            "#neurotech", "#braincomputerinterface", "#cognition", "#neurons",
        ],
    },
    "medicinenews": {
        "display_name": "Medicine News",
        "feeds": ["medical-research"],
        "topic_line": "medical research and clinical science",
        "hashtags": [
            "#medicine", "#medicalresearch", "#health", "#healthcare",
            "#clinicaltrials", "#biomedicine", "#publichealth", "#medtech",
        ],
    },
    "ainews": {
        "display_name": "AI News",
        "feeds": ["machine-learning"],
        "topic_line": "AI and machine learning research",
        "hashtags": [
            "#ai", "#artificialintelligence", "#machinelearning", "#deeplearning",
            "#ml", "#neuralnetworks", "#datascience", "#airesearch",
        ],
    },
    "psychnews": {
        "display_name": "Psychology News",
        "feeds": ["psychology", "human-behaviour"],
        "topic_line": "psychology and human behaviour research",
        "hashtags": [
            "#psychology", "#neuroscience", "#mentalhealth", "#cognition",
            "#behavior", "#psychologyfacts", "#humanbehavior", "#brain",
        ],
    },
    "mathnews": {
        "display_name": "Math News",
        "feeds": ["mathematics-and-computing"],
        "topic_line": "new results in mathematics",
        "hashtags": [
            "#mathematics", "#math", "#maths", "#appliedmath",
            "#numbertheory", "#geometry", "#statistics", "#mathematician",
        ],
    },
}


def feed_urls(account_key):
    """Return the list of Nature RSS URLs for an account."""
    acct = ACCOUNTS[account_key]
    return [NATURE_FEED.format(slug=slug) for slug in acct["feeds"]]
