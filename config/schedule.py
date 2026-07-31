"""Per-account daily posting slots (local time).

Spread across daytime/evening windows so the 11 accounts don't all post at once
(which reads as a content farm and clusters your reach). The posting job runs
every 30 minutes and publishes each account's freshest un-posted draft once its
slot for the day has passed.

Edit freely. Format is 24h "HH:MM" local time.
"""

POST_SLOTS = {
    "chemistrynews":     "09:00",
    "biologynews":       "10:00",
    "physicsnews":       "11:30",
    "quantumnews":       "13:00",
    "environmentalnews": "14:30",
    "spacenews":         "16:00",
    "neuronews":         "17:30",
    "medicinenews":      "18:30",
    "ainews":            "19:30",
    "psychnews":         "20:30",
    "mathnews":          "21:30",
}
