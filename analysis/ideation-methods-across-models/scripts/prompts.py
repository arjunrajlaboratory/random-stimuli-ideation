"""Prompt wording and output schemas for every arm (frozen with the pre-registration)."""

import copy
import json

from config import CONSTRAINTS, FOLLOWUP_ARMS, IDEAS_PER_CALL, N_OBVIOUS, N_OVERGENERATE, N_PARALLELS, QUESTIONS, STIMULI_DIR

IDEA_ITEMS = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "description": {"type": "string"}},
        "required": ["title", "description"],
    },
}
IDEA_SCHEMA = {"type": "object", "properties": {"ideas": IDEA_ITEMS}, "required": ["ideas"]}


def _schema_with(extra_key: str) -> dict:
    """IDEA_SCHEMA plus a list-of-strings field filled *before* the ideas."""
    s = copy.deepcopy(IDEA_SCHEMA)
    s["properties"] = {extra_key: {"type": "array", "items": {"type": "string"}}, "ideas": IDEA_ITEMS}
    s["required"] = [extra_key, "ideas"]
    return s


def task(q: str) -> str:
    """The parent study's plain task wording."""
    return (
        f"Research question: \"{QUESTIONS[q]}\"\n\n"
        f"Propose {IDEAS_PER_CALL} distinct, concrete ideas (analyses, measurements, or "
        "experiments) that a research lab could pursue to address this question. For each "
        "idea give a short title and a description of one or two sentences."
    )


# Parent study's phase-4 wording, unchanged.
INSTRUCTION_ONLY_FRAME = (
    "Each of your ideas must draw on a domain unrelated to the research question below, for "
    "example through an analogy, a structure, a principle, or a pattern borrowed from that domain, "
    "while still being a concrete, scientifically sound way to address the question.\n\n"
)

PARALLEL_STAGE1_SCHEMA = {
    "type": "object",
    "properties": {"parallels": {"type": "array", "items": {
        "type": "object",
        "properties": {"field": {"type": "string"}, "problem": {"type": "string"},
                       "how_studied": {"type": "string"}},
        "required": ["field", "problem", "how_studied"]}}},
    "required": ["parallels"],
}


def parallel_stage1_prompt(q: str) -> str:
    return (
        f"Here is a research question: \"{QUESTIONS[q]}\"\n\n"
        f"Do not answer it. Instead, list {N_PARALLELS} parallel problems, each from a different field "
        "outside biology and medicine, that share the underlying structure of this question. Make the "
        "fields as different from one another as you can. For each, give the field, the parallel "
        "problem in one sentence, and two or three sentences on how people in that field investigate "
        "or measure it (specific methods, experimental designs, or analyses)."
    )


def parallel_frame(p: dict) -> str:
    return (
        "Here is a problem from another field that shares the underlying structure of the research "
        "question below, with notes on how that field investigates it.\n\n"
        f"<parallel>\nField: {p['field']}\nProblem: {p['problem']}\nHow it is studied: {p['how_studied']}\n"
        "</parallel>\n\n"
        "Each of your ideas must transfer a specific method, measurement logic, or principle from how "
        "that field studies its problem, while still being a concrete, scientifically sound way to "
        "address the research question.\n\n"
    )


OBVIOUS_SUFFIX = (
    f"\n\nBefore proposing your ideas, list in the obvious field the {N_OBVIOUS} ideas that most "
    "experts would propose first for this question (one line each). Then propose your "
    f"{IDEAS_PER_CALL} ideas: none of them may be one of the obvious ideas or a minor variant of "
    "one. They must still be concrete and scientifically sound."
)

OVERGENERATE_SUFFIX = (
    f"\n\nWork in two steps. First, in the candidates field, brainstorm {N_OVERGENERATE} candidate "
    "ideas, one line each, covering as wide a range as you can. Then select the "
    f"{IDEAS_PER_CALL} candidates that best combine being non-obvious with being feasible and "
    "informative, and develop those as your ideas."
)

ASSUMPTION_SUFFIX = (
    "\n\nBefore proposing your ideas, list in the assumptions field the hidden assumptions built "
    "into this question and into the way the field usually tests it. Then propose your "
    f"{IDEAS_PER_CALL} ideas: each must test, exploit, or work around the failure of a different "
    "one of those assumptions, while still being a concrete, scientifically sound way to address "
    "the question."
)


def constraint_frame(c: str) -> str:
    return (f"Constraint: every one of your ideas must be carried out {c}. Within that constraint, "
            "make the ideas as informative as possible.\n\n")


def critique_prompt(q: str, prior_ideas: list[dict]) -> str:
    listing = "\n".join(f"{k + 1}. {i['title']}: {i['description']}" for k, i in enumerate(prior_ideas))
    return (
        f"Research question: \"{QUESTIONS[q]}\"\n\n"
        f"Here are {len(prior_ideas)} ideas that were proposed for this question:\n\n{listing}\n\n"
        "A senior expert reviewing them says they are the ideas everyone in the field would "
        f"propose first. Propose {IDEAS_PER_CALL} replacement ideas (analyses, measurements, or "
        "experiments) that are substantially less obvious but still concrete, scientifically sound, "
        "and feasible for a research lab. Do not repeat or lightly modify the ideas above. For each "
        "idea give a short title and a description of one or two sentences."
    )


def future_prompt(q: str) -> str:
    return (
        f"Research question: \"{QUESTIONS[q]}\"\n\n"
        f"It is 2036. Looking back, {IDEAS_PER_CALL} landmark papers each settled this question "
        "in a way that surprised the field, because of how they approached it. For each paper, "
        "describe what it measured, analyzed, or did, as a concrete idea a research lab could pursue "
        "today. For each idea give a short title and a description of one or two sentences."
    )


# Follow-up arms: the earlier study's required wording, verbatim.
REQUIRED_FRAME = (
    "Here is a piece of material that is unrelated to the research question below. Each of "
    "your ideas must draw on this material in some way (for example through an analogy, a "
    "structure, a principle, or a pattern it suggests), while still being a concrete, "
    "scientifically sound way to address the question.\n\n<material>\n{stimulus}\n</material>\n\n"
)


def stimulus(arm: str, call: int) -> str:
    base = arm.removesuffix("_required")
    return json.loads((STIMULI_DIR / f"{base}.json").read_text())[call]["stimulus"]


def build_prompt(arm: str, q: str, call: int, parallels=None, prior_ideas=None) -> tuple[str, dict, dict]:
    """Return (prompt, schema, extra metadata) for one generation call."""
    if arm in FOLLOWUP_ARMS:
        stim = stimulus(arm, call)
        return REQUIRED_FRAME.format(stimulus=stim) + task(q), IDEA_SCHEMA, {"stimulus": stim}
    if arm == "plain":
        return task(q), IDEA_SCHEMA, {}
    if arm == "instruction_only":
        return INSTRUCTION_ONLY_FRAME + task(q), IDEA_SCHEMA, {}
    if arm == "parallel_rotated":
        p = parallels[call]
        return parallel_frame(p) + task(q), IDEA_SCHEMA, {"parallel": p}
    if arm == "obvious_then_avoid":
        return task(q) + OBVIOUS_SUFFIX, _schema_with("obvious"), {}
    if arm == "overgenerate_select":
        return task(q) + OVERGENERATE_SUFFIX, _schema_with("candidates"), {}
    if arm == "assumption_inversion":
        return task(q) + ASSUMPTION_SUFFIX, _schema_with("assumptions"), {}
    if arm == "assigned_constraint":
        return constraint_frame(CONSTRAINTS[call]) + task(q), IDEA_SCHEMA, {"constraint": CONSTRAINTS[call]}
    if arm == "critique_revise":
        return critique_prompt(q, prior_ideas), IDEA_SCHEMA, {}
    if arm == "future_retrospective":
        return future_prompt(q), IDEA_SCHEMA, {}
    raise ValueError(f"unknown arm {arm}")
