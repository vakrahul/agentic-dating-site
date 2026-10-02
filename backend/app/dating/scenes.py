from __future__ import annotations

SCENE_TEMPLATES: list[tuple[tuple[str, ...], str]] = [
    (("coffee", "cafe", "espresso", "tea"), "a quiet coffee shop by the window"),
    (("travel", "wanderlust", "trip", "vacation", "backpacking"), "an airport gate during a long layover"),
    (("food", "cooking", "baking", "cuisine", "restaurant", "foodie"), "a Saturday food market"),
    (("fitness", "gym", "running", "marathon", "workout"), "a running trail after rain"),
    (("music", "concert", "guitar", "band", "vinyl"), "a small live-music venue before the headliner"),
    (("art", "museum", "painting", "gallery", "drawing"), "an art museum on a slow weekday"),
    (("tech", "software", "startup", "coding", "ai"), "a tech meetup with bad name tags"),
    (("hiking", "outdoors", "camping", "trail", "mountain"), "a hiking trailhead at sunrise"),
    (("book", "reading", "novel", "library", "poetry"), "an independent bookstore on a rainy afternoon"),
    (("photo", "photography", "camera"), "a scenic overlook at golden hour"),
    (("film", "cinema", "movie", "documentary"), "a cinema lobby after a late screening"),
    (("gaming", "games", "esports"), "an arcade with tired carpets"),
    (("cycling", "bike", "bicycle"), "a bike-path cafe stop"),
    (("yoga", "meditation", "pilates"), "a rooftop yoga class before work"),
    (("ski", "snowboard", "snow"), "a ski lodge with a fire going"),
    (("surf", "beach", "ocean", "swim"), "a beach at sunset with cold drinks"),
    (("volunteer", "community", "nonprofit"), "a community fundraiser"),
    (("fashion", "style", "design"), "a pop-up design shop"),
]


def pick_scene(interests_a: list[str], interests_b: list[str]) -> str:
    shared = {str(i).lower() for i in interests_a} & {str(i).lower() for i in interests_b}
    if not shared:
        return "a coffee shop"
    joined = " ".join(shared)
    for keywords, scene in SCENE_TEMPLATES:
        for keyword in keywords:
            if keyword in joined:
                return scene
    first = sorted(shared)[0]
    return f"a coffee shop talking about {first}"
