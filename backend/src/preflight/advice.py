"""Customer-facing advice in the brief's language (PRD §16: report advice follows the brief).

The report's "next time" lines are composed in code from run data, never by a model, so each
template exists once per supported language. Any other language falls back to English.
Fields inside the templates (scene text, panel details) stay as the run produced them.
"""

from typing import Final

ENGLISH = "en"

_TEMPLATES: Final[dict[str, dict[str, str]]] = {
    "en": {
        "soft_screen": (
            "Screenshot {n}: {where} only {px} px wide, so it looks soft in a 1080 px video. "
            "Upload the original screenshot from the device (for example 1170 x 2532 from an "
            "iPhone) for a sharp result."
        ),
        "soft_where_crop": "its screen is",
        "soft_where_plain": "it is",
        "screenshot_issue": "Screenshot {n}: {issue}.",
        "excluded": (
            "Screenshot {n} {shows}, not {product}; it was left out of every video. Upload a "
            "screen of your own product to use it."
        ),
        "excluded_shows_brand": "shows {brand}",
        "excluded_shows_none": "does not show the product",
        "off_brand_kept": (
            "Some screenshots may not show your product, but too few would remain without them; "
            "replace them before launching."
        ),
        "cta_mismatch": (
            'Your call to action "{given}" speaks to someone other than your audience '
            '"{audience}"{reason}. The videos use a call to action for your audience instead; '
            "{fix}."
        ),
        "cta_fix_buyer": "change buyer_cta to the action your audience should take",
        "cta_fix_none": "set buyer_cta in the brief to choose it yourself",
        "weakest_reported": (
            "Simulated viewers dropped on '{text}' ({span}, {simulator}: {detail}): shorten "
            "this scene or tighten its wording."
        ),
        "weakest_series": (
            "The {simulator} series was weakest on '{text}' ({span}): shorten this scene or "
            "tighten its wording."
        ),
        "rework_hook": (
            "The weakest moment is in the opening scene: rework the hook '{hook}' (from {field})."
        ),
        "rework_cta": (
            "The weakest moment is in the closing scene: rework the call to action '{cta}' "
            "(from {field})."
        ),
        "low_confidence": (
            "The ranking has low confidence (one simulator, or the simulators disagree): "
            "treat the winner as a hypothesis and A/B test it before committing."
        ),
        "production": (
            "Production quality: the smallest screen in the videos is {px} px wide, so scores "
            "are capped at {percent} %. Screenshots at least {sharp} px wide lift the cap."
        ),
        "craft_still": (
            "Variant {variant}: nothing happens on screen for {seconds} s around {at}; viewers "
            "scroll on in stretches over {limit} s. Add a scene or a focus region to tap."
        ),
        "craft_voice": (
            "Variant {variant}: the voice covers only {percent} % of the video; give every "
            "scene a voice line so the narration carries the whole ad."
        ),
        "craft_loudness": (
            "Variant {variant}: the mix is {lufs} LUFS, outside the {low} to {high} LUFS "
            "range social feeds play at."
        ),
        "sim_tribe_v2": "brain sim",
        "sim_gemini_panel": "simulated viewer panel",
    },
    "sv": {
        "soft_screen": (
            "Skärmdump {n}: {where} bara {px} px bred, så den blir mjuk i en video som är "
            "1080 px bred. Ladda upp originalskärmdumpen från enheten (till exempel "
            "1170 x 2532 från en iPhone) för en skarp bild."
        ),
        "soft_where_crop": "skärmen i bilden är",
        "soft_where_plain": "bilden är",
        "screenshot_issue": "Skärmdump {n}: {issue}.",
        "excluded": (
            "Skärmdump {n} {shows}, inte {product}, och användes därför inte i någon video. "
            "Ladda upp en skärm från er egen produkt i stället."
        ),
        "excluded_shows_brand": "visar {brand}",
        "excluded_shows_none": "visar inte produkten",
        "off_brand_kept": (
            "Några skärmdumpar visar kanske inte er produkt, men för få skulle bli kvar utan "
            "dem. Byt ut dem innan ni lanserar."
        ),
        "cta_mismatch": (
            'Er uppmaning "{given}" vänder sig till någon annan än målgruppen '
            '"{audience}"{reason}. Videorna använder i stället en uppmaning till målgruppen; '
            "{fix}."
        ),
        "cta_fix_buyer": "ändra buyer_cta till det målgruppen ska göra",
        "cta_fix_none": "fyll i buyer_cta i briefen för att välja den själv",
        "weakest_reported": (
            "Simulerade tittare tappade vid '{text}' ({span}, {simulator}: {detail}): korta "
            "scenen eller skärp texten."
        ),
        "weakest_series": (
            "Kurvan från {simulator} var svagast vid '{text}' ({span}): korta scenen eller "
            "skärp texten."
        ),
        "rework_hook": (
            "Det svagaste ögonblicket ligger i öppningsscenen: skriv om kroken '{hook}' "
            "(från {field})."
        ),
        "rework_cta": (
            "Det svagaste ögonblicket ligger i slutscenen: skriv om uppmaningen '{cta}' "
            "(från {field})."
        ),
        "low_confidence": (
            "Rankningen har låg säkerhet (en simulator, eller simulatorerna är oeniga): se "
            "vinnaren som en hypotes och A/B-testa den innan ni bestämmer er."
        ),
        "production": (
            "Produktionskvalitet: den minsta skärmen i videorna är {px} px bred, så poängen "
            "begränsas till {percent} %. Skärmdumpar som är minst {sharp} px breda tar bort "
            "begränsningen."
        ),
        "sim_tribe_v2": "hjärnsimuleringen",
        "craft_still": (
            "Variant {variant}: ingenting händer i bild under {seconds} s runt {at}; tittare "
            "scrollar vidare när det står still längre än {limit} s. Lägg till en scen eller "
            "ett fokusområde att trycka på."
        ),
        "craft_voice": (
            "Variant {variant}: rösten täcker bara {percent} % av videon; ge varje scen en "
            "röstreplik så att berättarrösten bär hela annonsen."
        ),
        "craft_loudness": (
            "Variant {variant}: mixen ligger på {lufs} LUFS, utanför intervallet {low} till "
            "{high} LUFS som sociala flöden spelar upp i."
        ),
        "sim_gemini_panel": "den simulerade tittarpanelen",
    },
}


def advice(key: str, language: str | None, **fields: object) -> str:
    """The ``key`` template in ``language`` (ISO 639-1; English when unsupported), filled in."""
    table = _TEMPLATES.get((language or "").strip().casefold()[:2], _TEMPLATES[ENGLISH])
    return table[key].format(**fields)
