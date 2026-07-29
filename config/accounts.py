"""Account configuration for the science-Instagram pipeline.

Each account maps to one or more Nature per-subject RSS feeds, a tiered pool of
hashtags, and (later) the Instagram Graph API credentials needed to publish.

Hashtags are grouped into tiers so each post can mix small-niche tags (where a
new account can actually rank), mid-size tags, and a few broad tags:
    "hashtags": {"niche": [...], "mid": [...], "broad": [...]}
The caption builder rotates within each tier per post, so sets vary instead of
being identical every time.

Credentials are NOT stored here. Each account names an env var that will hold
its long-lived access token, plus its Instagram Business account id. Until those
accounts exist and tokens are provided, the publish step runs in dry-run only.

Nature subject feeds: https://www.nature.com/subjects/<slug>.rss
"""

# Base URL template for Nature subject feeds.
NATURE_FEED = "https://www.nature.com/subjects/{slug}.rss"

# Shared broad tags any science post can draw from (added to the broad tier).
COMMON_TAGS = ["#science", "#research", "#scicomm"]

# Publication these accounts cite as the source.
SOURCE_NAME = "Nature"

ACCOUNTS = {
    "chemistrynews": {
        "display_name": "Chemistry News",
        "feeds": ["chemistry"],
        "topic_line": "the latest chemistry research",
        "hashtags": {
            "niche": ["#catalysis", "#organicchemistry", "#materialsscience",
                      "#electrochemistry", "#chemistrylab", "#compchem"],
            "mid": ["#chemistry", "#chemist", "#molecules", "#nanotech"],
            "broad": ["#stem", "#chemistrylife", "#sciencefacts"],
        },
    },
    "biologynews": {
        "display_name": "Biology News",
        "feeds": ["biological-sciences"],
        "topic_line": "new discoveries in biology",
        "hashtags": {
            "niche": ["#cellbiology", "#molecularbiology", "#microbiology",
                      "#genomics", "#evolutionarybiology", "#crispr"],
            "mid": ["#genetics", "#biotech", "#evolution", "#lifesciences"],
            "broad": ["#biology", "#stem", "#sciencefacts"],
        },
    },
    "physicsnews": {
        "display_name": "Physics News",
        "feeds": ["physics"],
        "topic_line": "breakthroughs in physics",
        "hashtags": {
            "niche": ["#condensedmatter", "#particlephysics", "#optics",
                      "#photonics", "#theoreticalphysics", "#quantummechanics"],
            "mid": ["#astrophysics", "#quantumphysics", "#physicist", "#nanophysics"],
            "broad": ["#physics", "#stem", "#sciencefacts"],
        },
    },
    "quantumnews": {
        "display_name": "Quantum News",
        "feeds": ["quantum-information"],
        "topic_line": "advances in quantum science",
        "hashtags": {
            "niche": ["#qubits", "#quantuminformation", "#superconductors",
                      "#entanglement", "#quantumhardware", "#quantumalgorithms"],
            "mid": ["#quantumcomputing", "#quantumtech", "#quantumphysics", "#computing"],
            "broad": ["#quantum", "#physics", "#stem"],
        },
    },
    "environmentalnews": {
        "display_name": "Environmental News",
        "feeds": ["environmental-sciences"],
        "topic_line": "environmental science research",
        "hashtags": {
            "niche": ["#climatescience", "#ecology", "#biodiversity",
                      "#carboncapture", "#earthscience", "#conservationscience"],
            "mid": ["#climatechange", "#sustainability", "#conservation", "#renewables"],
            "broad": ["#climate", "#environment", "#nature"],
        },
    },
    "spacenews": {
        "display_name": "Space News",
        "feeds": ["space-physics"],
        "topic_line": "the newest space and astrophysics research",
        "hashtags": {
            "niche": ["#exoplanets", "#solarwind", "#heliophysics",
                      "#planetaryscience", "#cosmology", "#spacephysics"],
            "mid": ["#astrophysics", "#astronomy", "#cosmos", "#spacescience"],
            "broad": ["#space", "#nasa", "#universe"],
        },
    },
    "neuronews": {
        "display_name": "Neuroscience News",
        "feeds": ["neuroscience"],
        "topic_line": "neuroscience and brain-computer interface research",
        "hashtags": {
            "niche": ["#braincomputerinterface", "#neurotech", "#bci",
                      "#computationalneuroscience", "#neuralnetworks", "#neuroimaging"],
            "mid": ["#neuroscience", "#neurons", "#cognition", "#brainhealth"],
            "broad": ["#brain", "#stem", "#sciencefacts"],
        },
    },
    "medicinenews": {
        "display_name": "Medicine News",
        "feeds": ["medical-research"],
        "topic_line": "medical research and clinical science",
        "hashtags": {
            "niche": ["#clinicaltrials", "#biomedicine", "#translationalmedicine",
                      "#precisionmedicine", "#immunology", "#medicalresearch"],
            "mid": ["#medicine", "#healthcare", "#publichealth", "#medtech"],
            "broad": ["#health", "#stem", "#sciencefacts"],
        },
    },
    "ainews": {
        "display_name": "AI News",
        "feeds": ["machine-learning"],
        "topic_line": "AI and machine learning research",
        "hashtags": {
            "niche": ["#deeplearning", "#neuralnetworks", "#airesearch",
                      "#nlp", "#reinforcementlearning", "#mlresearch"],
            "mid": ["#machinelearning", "#datascience", "#ml", "#aitools"],
            "broad": ["#ai", "#artificialintelligence", "#tech"],
        },
    },
    "psychnews": {
        "display_name": "Psychology News",
        "feeds": ["psychology", "human-behaviour"],
        "topic_line": "psychology and human behaviour research",
        "hashtags": {
            "niche": ["#cognitivescience", "#behavioralscience", "#socialpsychology",
                      "#neuropsychology", "#psychresearch", "#humanbehaviour"],
            "mid": ["#psychology", "#cognition", "#mentalhealth", "#behavior"],
            "broad": ["#brain", "#science", "#psychologyfacts"],
        },
    },
    "mathnews": {
        "display_name": "Math News",
        "feeds": ["mathematics-and-computing"],
        "topic_line": "new results in mathematics",
        "hashtags": {
            "niche": ["#numbertheory", "#appliedmathematics", "#topology",
                      "#probabilitytheory", "#discretemath", "#mathresearch"],
            "mid": ["#mathematics", "#appliedmath", "#statistics", "#mathematician"],
            "broad": ["#math", "#maths", "#stem"],
        },
    },
}


def feed_urls(account_key):
    """Return the list of Nature RSS URLs for an account."""
    acct = ACCOUNTS[account_key]
    return [NATURE_FEED.format(slug=slug) for slug in acct["feeds"]]
