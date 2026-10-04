"""Phase 2: fill the HTML template into random-stimuli-ideation-report.html.

Every reportable number is a value span (data-sci-val / data-sci-text) whose text is
filled from .manifest.json by `scitexlintr --write` in Phase 7; the placeholder text
here is "…". Structural counts are written in words. Revised after the Phase 4-6
reviews (.review-*-html.yaml).
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parents[2] / ".living/conventions/report-generator/assets/report-template.html"
OUT = HERE / "random-stimuli-ideation-report.html"


def V(i):
    return f'<span data-sci-val="{i}">…</span>'


def T(i):
    return f'<span data-sci-text="{i}">…</span>'


TITLE = "Asking a language model to borrow from other fields beat random material in one brainstorming test"
DEK = ("On one research question, scored by a model judge: poems, random words and other unrelated "
       "material did not detectably improve a language model's research ideas, while a one-line "
       "instruction to borrow from another field did. Ratings by scientists are still pending.")


ABSTRACT = f"""
<p>When a language model brainstorms, it tends to return the same few obvious ideas every time it
is asked. Human creativity techniques fight this with random prompts: a card, a poem, a word picked
at random. We asked whether the same trick works on a current model (Claude Sonnet 5.5)
brainstorming experiments for one research question: does the transcription factor AP-1 act as a
cellular memory mechanism? Over five rounds we compared nineteen prompt types, from a plain request
and verbalized sampling (the strongest published prompting fix for repetitive answers) to poems,
random words, essays the model wrote itself, and a bare instruction to borrow from another field.
Each prompt type produced forty ideas. A second model scored every idea for novelty and usefulness
without knowing which prompt produced it, and our main measure counts the <em>distinct</em> ideas it
rated both novel and useful.</p>
<p>Unrelated material did not detectably help: the model showed no detectable response to it unless
told to use it, and when told to, it mostly dressed up the same experiments in metaphor. What worked
best supplied no material at all. We added one sentence before the usual request: "{T("winning_instruction_text")}" The model then chose its own outside
fields, such as magnetic hysteresis and memory tagging in neuroscience. This prompt gave
{V("judge_stripped_n_distinct_useful_novel_instruction_only")} distinct useful and novel ideas,
against {V("judge_stripped_n_distinct_useful_novel_verbalized_sampling")} for verbalized sampling and
{V("judge_stripped_n_distinct_useful_novel_plain")} for the plain prompt (permutation tests, p
{T("t_stripped_instr_vs_vs_distinct_p_holm")} and p {T("t_stripped_instr_vs_plain_distinct_p_holm")}). We found this prompt in the
fourth round, after seeing earlier results, so the comparison is exploratory. The main caveat: all
quality scores come from one model judge on one question, and blind ratings by scientists are still
pending.</p>
"""

PROBLEM = f"""
<p>Ask a language model for five experiments to test an idea, then ask again in a fresh session,
and you will get nearly the same five experiments. Researchers call this <em>mode collapse</em>:
the model returns its most probable answers, and different sessions, and even different models,
converge on them (<a href="#ref-jiang">Jiang et al.</a>). For brainstorming, that defeats the
purpose. Turning up the model's sampling randomness mostly adds incoherence rather than new
directions (<a href="#ref-peeperkorn">Peeperkorn et al.</a>), and a recent prompting method,
<em>verbalized sampling</em> (asking for several answers along with how likely each one is), is the
strongest published fix (<a href="#ref-zhang">Zhang et al.</a>).</p>
<p>People have long broken out of ruts with deliberately irrelevant input: Brian Eno's Oblique
Strategies cards, or Edward de Bono's random-word technique. The idea tested here is the machine
version: put something unrelated in front of the model (a poem, a paragraph about bell founding, a
string of random characters) before asking it to brainstorm, and see whether the ideas get more
varied without getting worse. A recent study found that prepending a random word made answers to
simple list questions more diverse (<a href="#ref-agrawal">Agrawal and Goyal</a>); research
brainstorming is a much more open task.</p>
<p>We tested this on one real question from our lab's work: <em>what analyses or measurements would
best test whether AP-1 acts as a cellular memory mechanism?</em> AP-1 is a family of transcription
factors switched on by stress and growth signals, and one hypothesis is that it leaves a lasting
mark on chromatin that changes how a cell responds next time. The question has a clear set of
standard answers (time courses of chromatin accessibility after a transient stimulus, removing AP-1
at different times, single-cell lineage tracing), which makes it easy to see when a prompt moves the
model off them.</p>
<p>A good answer to "does this prompt help?" needs ideas that are both new and worth doing, and it
needs to count each good idea once. We therefore call an idea <em>useful-novel</em> when the judge
rated it at least four out of five on both novelty and usefulness, and we count <em>distinct
useful-novel ideas</em>: useful-novel ideas after merging near-duplicates, so that one good idea
repeated in every session counts once. That is the number a person brainstorming cares about: how
many different good ideas do I get? The bar we set at the outset was to beat verbalized sampling on
useful-novel ideas.</p>
<p>To give away the ending: the strategy that worked best is not a random stimulus at all. It adds a
single sentence before an otherwise ordinary brainstorming request, telling the model that each idea
must draw on a domain unrelated to the research question (an analogy, a structure, a principle or a
pattern borrowed from that domain) while staying concrete and scientifically sound. The model picks
the outside fields itself. <a class="xref" href="#fig-prompt">Figure</a> gives the complete prompt,
ready to copy; the rest of the report shows how it compares with the alternatives and where it
falls short.</p>
"""

METHODS = f"""
<p>We tested nineteen prompt types in five rounds, each round designed in response to the previous
one (<a class="xref" href="#tab-arms">Table</a> lists them all). Every prompt type was run as eight
separate calls to the model, each in a fresh session with no memory of the others, asking for five
ideas per call: forty ideas per prompt type and {V("n_ideas_total")} ideas in total.</p>
<p>We measured the ideas two ways. First, a text-similarity model turned each idea into a list of
numbers (an <em>embedding</em>) so that similar ideas sit close together; ideas closer than a fixed
similarity threshold were merged into one <em>idea group</em>, and we counted the groups. Second, a
stronger model ({"Claude Opus 5.5"}) acted as a judge. It read every idea in shuffled batches,
without knowing which prompt produced it, and rated novelty and usefulness on one-to-five scales,
twice in different orders. Its two readings agreed reasonably well (rank correlation
{V("judge_stripped_novelty_spearman")} for novelty and {V("judge_stripped_usefulness_spearman")}
for usefulness).</p>
<p>One control matters throughout. When a prompt tells the model to use a poem, the ideas pick up
the poem's words, and both measurements can mistake new vocabulary for new ideas. So we also had the
generating model rewrite every idea in plain scientific language with all analogies and metaphors
removed. The rewriting prompt carried no label saying which prompt produced an idea, though ideas
were batched within groups of rounds (the first three rounds together, then the fourth and the fifth
separately), so the instruction-only ideas, for example, were rewritten in batches of their own. We call the result the <em>stripped text</em> and report results
on it unless we say otherwise; reading a sample of rewrites (an informal check, not a systematic one),
we found the experiments kept and only the framing removed.</p>
<p>To compare two prompt types, we asked how often a difference at least as large would appear if
the prompt made no difference, by shuffling whole calls between the two (a <em>permutation
test</em>; the five ideas from one call are not independent, so calls, not ideas, are shuffled).
When several prompt types from one round are each compared with the same baseline, we correct the
p-values for the number of comparisons (the <em>Holm adjustment</em>). The supplement gives the
full <a href="#supp-measures">definitions and parameters</a> and <a href="#supp-stats">statistics</a>.</p>
"""

RESULTS = f"""
<section id="result-examples">
<h3>A plain prompt returns the same short list of experiments every time, and the example calls show how other prompts change that list</h3>
<p>Before any averages, here is what the ideas look like. We picked the calls in this section to
illustrate each prompt type, not at random; every idea is in the analysis outputs.
<a class="xref" href="#tab-plain">Table</a> shows two of the eight plain-prompt calls side by side.
They are separate sessions, yet they draw on the same short list: the first idea has the same title
word for word, both propose switching AP-1 on with light (optogenetics) and profiling single cells,
and the rest are variations on removing AP-1 or perturbing the places it binds. The other plain
calls look the same: across all forty plain-prompt ideas (as written),
{V("near_dup_frac_plain")} have a near-duplicate elsewhere in the set.</p>
<div class="table-wrap" id="tab-plain">
  <table class="sci-table" data-sci-worked="we_plain_two_calls" data-columns="idea,first_call,second_call">
    <caption>The plain prompt (no extra material or instruction), two separate calls chosen to show repetition. Each row is the idea in the same position in each call.</caption>
    <thead><tr><th scope="col" class="num">Idea</th><th scope="col">First call</th><th scope="col">Second call</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<p>When the prompt included a poem (Emily Dickinson's "Hope is the thing with feathers") and
<em>required</em> each idea to draw on it, the titles changed, but with the poetic phrases removed
the experiments match the plain prompt's usual list
(<a class="xref" href="#tab-poem">Table</a>). "Sensitivity to the second stimulus (the sweetest tune
in the gale)" is the plain re-stimulation experiment with a line of the poem attached. The stripped
column shows the same ideas after the metaphors were removed, along with the judge's scores.</p>
<div class="table-wrap" id="tab-poem">
  <table class="sci-table" data-sci-worked="we_poem_required" data-columns="as_written,stripped,novelty,usefulness,useful_novel" data-precision="1">
    <caption>One call in which the model was required to draw on a poem. "Stripped" is each idea rewritten with metaphors removed; novelty and usefulness are the model judge's one-to-five scores on that stripped text; an idea is useful-novel when both are at least four.</caption>
    <thead><tr><th scope="col">As written</th><th scope="col">Stripped of metaphor</th><th scope="col" class="num">Novelty</th><th scope="col" class="num">Usefulness</th><th scope="col">Useful-novel?</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<p>With no material at all, but an instruction to make each idea "draw on a domain unrelated to the
research question", the model chose its own analogies, and they were apt: magnetic hysteresis,
engram tagging from neuroscience, pedigree analysis, chromosome "bookmarking" during cell division
(<a class="xref" href="#tab-instr">Table</a>). Several of these survive stripping as experiments
that never appear among the plain-prompt ideas, such as permanently labeling cells that once
switched on the AP-1 gene <em>Fos</em> and re-stimulating them later.</p>
<div class="table-wrap" id="tab-instr">
  <table class="sci-table" data-sci-worked="we_instruction_only" data-columns="as_written,stripped,novelty,usefulness,useful_novel" data-precision="1">
    <caption>One call with only the instruction to borrow from an unrelated domain and no material. Columns as in the poem table: stripped rewrite, then the model judge's scores on it.</caption>
    <thead><tr><th scope="col">As written</th><th scope="col">Stripped of metaphor</th><th scope="col" class="num">Novelty</th><th scope="col" class="num">Usefulness</th><th scope="col">Useful-novel?</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<p>Finally, in a two-step prompt, a separate session first wrote a short essay about a
<em>parallel problem</em>: a problem in another field with the same structure as ours. The model
chose the same parallel in {T("parallel_essays_magnetic_phrase")} essays: how physicists decide
whether a magnet's hysteresis is a true memory of past fields. The essay was then given to a fresh
session as material to draw on. The resulting ideas carry over specific experimental designs from
magnetism (<a class="xref" href="#tab-parallel">Table</a>): first-order reversal curves, which
reverse a stimulus ramp at many different peaks to map the distribution of switching thresholds, and
tests of "remanence decay" and erasure. As later sections show, the judge found these ideas the most
novel and also less useful.</p>
<div class="table-wrap" id="tab-parallel">
  <table class="sci-table" data-sci-worked="we_parallel" data-columns="as_written,stripped,novelty,usefulness,useful_novel" data-precision="1">
    <caption>One call that drew on the model's own essay about a parallel problem in magnetism. Columns as in the poem table: stripped rewrite, then the model judge's scores on it.</caption>
    <thead><tr><th scope="col">As written</th><th scope="col">Stripped of metaphor</th><th scope="col" class="num">Novelty</th><th scope="col" class="num">Usefulness</th><th scope="col">Useful-novel?</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="result-ignored">
<h3>With optional wording, the model showed no detectable response to material we supplied</h3>
<p>If a stimulus nudges the model, ideas written after a given poem should resemble that poem more
than the other poems in the set. We tested this by reshuffling which poem was paired with which call
within the poem prompt type. With the gentle wording ("you may let it inspire your thinking in any
way you like, or not"), we found no detectable trace of the material in the ideas, for poems
(p {T("leakage_p_poem")}) or random characters (p {T("leakage_p_random_tokens")}), and these
prompt types were as repetitive as the plain prompt: {V("n_clusters_poem")} idea groups (as written)
for the optional poem against {V("n_clusters_plain")} for the plain prompt. With eight calls per
prompt type, a small effect could still go undetected.</p>
<p>The exception is the stimulus the model designed for itself, which ends with instructions to
itself (for example, "pick two or three fragments… avoid the first three ideas that come to mind").
Even with optional wording, {V("leakage_word_reuse_self_designed")} of those ideas reused a word
from their own stimulus, against {V("leakage_word_reuse_self_designed_mismatched")} that matched a
different session's stimulus (similarity-based leakage test, p {T("leakage_p_self_designed")}), and
the prompt type produced {V("n_clusters_self_designed")} idea
groups (as written) against {V("n_clusters_plain")} for the plain prompt (Holm-adjusted p
{T("t_written_selfdes_vs_plain_clusters_p_holm")}). We suspect the instructions, rather than the
fragments, made the model engage, but we did not test this.</p>
<p>With the required wording, our material showed up clearly: ideas resembled their own poem
(p {T("leakage_p_poem_required")}), and {V("leakage_word_reuse_poem_required")} of them reused a
distinctive word from it. This model appears to set irrelevant context aside unless an instruction
says otherwise. That differs from the study in which a random word diversified answers to simple
list questions (<a href="#ref-agrawal">Agrawal and Goyal</a>); open-ended research brainstorming with
a current model may behave differently.</p>
</section>

<section id="result-decoration">
<h3>Told to use the material, the model rewrapped the same experiments, and only part of the extra variety was real</h3>
<p>As written, the required-material ideas look much more varied: the required poem produced
{V("n_clusters_poem_required")} idea groups against {V("n_clusters_plain")} for the plain prompt
(<a class="xref" href="#fig-decoration">Figure</a>). After stripping the metaphors, it produced
{V("n_clusters_stripped_poem_required")} against {V("n_clusters_stripped_plain")}: some of the gain
was wording, and the remaining difference is not statistically clear (Holm-adjusted p
{T("t_stripped_poemreq_vs_plain_clusters_p_holm")}). Neither of our two pre-specified
diversity measures, the overall spread of ideas and the share of near-duplicates, separated any
prompt type from the plain prompt once metaphors were stripped (smallest Holm-adjusted p
{T("min_p_holm_spread_stripped_vs_plain")} for spread and
p {T("min_p_holm_neardup_stripped_vs_plain")} for near-duplicates); the idea-group count is a
secondary measure. The judge also flagged, as written, between {V("forced_ref_material_min")} and
{V("forced_ref_material_max")} of the required-material ideas, depending on the material, as
containing a reference that did not belong; the instruction-only prompt, which also asks for
analogies, was flagged at {V("forced_ref_instruction_only")}, and the required self-designed
stimulus at {V("forced_ref_self_designed_required")}.</p>
<figure class="sci-figure" id="fig-decoration" data-sci-fig="fig_decoration" data-alt="Dot plot of idea groups for each of the nineteen prompt types, as written and after stripping metaphors. The self-designed stimuli lose the most groups when stripped, and the prompts that required unrelated material lose several; the plain prompt and the optional-material prompts barely change.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Idea groups among the forty ideas of each prompt type, counted by merging ideas whose text is very similar. Light circles show the ideas as written; dark diamonds show the same ideas after a rewrite that removed analogies and metaphors without knowing which prompt produced them. A long gap means much of the apparent variety was wording rather than different experiments.</figcaption>
</figure>
</section>

<section id="result-instruction">
<h3>An instruction to borrow from another field yielded the most distinct good ideas</h3>
<figure class="sci-figure" id="fig-prompt" data-sci-diagram>
  <div class="sci-media"><pre style="white-space: pre-wrap;">{T("winning_prompt_text")}</pre></div>
  <figcaption>The winning prompt, exactly as sent to the model in a fresh session. Only the first sentence differs from the plain prompt. To reuse it, replace the research question with your own; because the model tends to reach for the same outside fields in every session, run several sessions and expect some repetition.</figcaption>
</figure>
<p>If the material were doing the work, adding a poem or a paragraph to the borrowing instruction
should help. It did the opposite. The instruction alone produced
{V("judge_stripped_n_distinct_useful_novel_instruction_only")} distinct useful-novel ideas, the most
of any prompt type (<a class="xref" href="#fig-distinct">Figure</a>), against
{V("judge_stripped_n_distinct_useful_novel_verbalized_sampling")} for verbalized sampling and
{V("judge_stripped_n_distinct_useful_novel_plain")} for the plain prompt (p
{T("t_stripped_instr_vs_vs_distinct_p_holm")} and p {T("t_stripped_instr_vs_plain_distinct_p_holm")}).
In a follow-up comparison added after review, it also beat the persona prompts from our lab's
brainstorming tool ("approach this as a statistical physicist", and so on), which produced
{V("judge_stripped_n_distinct_useful_novel_persona")} distinct useful-novel idea, a difference of
{V("t_stripped_instr_vs_persona_distinct_diff")} (p {T("t_stripped_instr_vs_persona_distinct_p")},
unadjusted). Because we designed this prompt in the fourth
round after seeing the earlier ones, these comparisons are exploratory, not confirmatory.</p>
<p>Adding material that we chose (a poem, a paragraph, random tokens, word salad or semi-random
sentences) to the same instruction lowered judged novelty by between
{V("t_stripped_material_vs_instr_novelty_drop_smallest")} and
{V("t_stripped_material_vs_instr_novelty_drop_largest")} points on the five-point scale (largest
Holm-adjusted p {T("t_stripped_material_vs_instr_novelty_max_p_holm")}). The self-designed stimulus,
which carries its own instructions, was the exception (difference
{V("t_stripped_selfdes_req_vs_instr_novelty_diff")}, Holm-adjusted p
{T("t_stripped_selfdes_req_vs_instr_novelty_p_holm")}). The instruction costs a little usefulness:
{V("judge_stripped_usefulness_instruction_only")} against {V("judge_stripped_usefulness_plain")} for
the plain prompt.</p>
<figure class="sci-figure" id="fig-distinct" data-sci-fig="fig_distinct_useful_novel" data-alt="Lollipop chart of distinct useful and novel ideas for each of the nineteen prompt types, sorted. The instruction-only prompt is highest, followed by the required self-designed stimulus and the parallel-problem essay. The plain prompt, verbalized sampling and most prompts with material we chose have none or one.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Distinct useful-novel ideas per prompt type, out of forty ideas each. An idea counts when a second language model, judging without knowing the prompt, rated it at least four out of five on both novelty and usefulness, after the idea was rewritten with its metaphors removed; near-duplicates count once. Circles mark the baselines; squares mark prompts whose material was not chosen for its relevance to the question (our poems, paragraphs and random text, and the model's essays on unrelated topics); triangles mark prompts where the model chose the outside connection itself (the bare instruction, the parallel-problem essay, and the self-designed stimuli).</figcaption>
</figure>
<p>Counting <em>distinct</em> ideas matters here. The instruction-only prompt produced
{V("judge_stripped_n_useful_novel_instruction_only")} useful-novel ideas, but several are the same
experiment; <a class="xref" href="#tab-distinct">Table</a> shows how they merge into
{V("judge_stripped_n_distinct_useful_novel_instruction_only")} groups. The largest group is the
magnetic-hysteresis experiment (ramp the stimulus up and then down, and check whether the response
depends on the direction); hysteresis came up in {T("instr_calls_hysteresis_phrase")} of its calls.
We also checked the cutoff: among the prompt types we checked, the instruction-only prompt
{T("cutoff_sensitivity_leader_phrase")}, and at a stricter cutoff of four and a half
{T("cutoff_strictest_none_phrase")} (<a class="xref" href="#tab-cutoff">Table</a>).</p>
<div class="table-wrap" id="tab-distinct">
  <table class="sci-table" data-sci-worked="we_distinct_instruction_only" data-columns="group,idea,novelty,usefulness" data-precision="1">
    <caption>Every useful-novel idea from the instruction-only prompt (stripped text, judge scores out of five), with the near-duplicate group it was merged into. The number of groups is the distinct count shown in the figures.</caption>
    <thead><tr><th scope="col" class="num">Group</th><th scope="col">Idea</th><th scope="col" class="num">Novelty</th><th scope="col" class="num">Usefulness</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="result-parallel">
<h3>Thinking through a parallel problem gave the most novel ideas, which the judge rated as less useful</h3>
<p>The two-step prompt that first explored a structurally similar problem produced the highest
judged novelty of any prompt type: {V("judge_stripped_novelty_stream_parallel_required")}, against
{V("judge_stripped_novelty_instruction_only")} for the instruction alone and
{V("judge_stripped_novelty_plain")} for the plain prompt
(<a class="xref" href="#fig-tradeoff">Figure</a>; difference from the instruction alone
{V("t_stripped_parallel_vs_instr_novelty_diff")}, Holm-adjusted p
{T("t_stripped_parallel_vs_instr_novelty_p_holm")}). The judge also rated these ideas less useful,
{V("judge_stripped_usefulness_stream_parallel_required")} against
{V("judge_stripped_usefulness_instruction_only")} (Holm-adjusted p
{T("t_stripped_parallel_vs_instr_usefulness_p_holm")}). It produced
{V("judge_stripped_n_distinct_useful_novel_stream_parallel_required")} distinct useful-novel ideas
against {V("judge_stripped_n_distinct_useful_novel_instruction_only")} for the instruction alone, a
difference within chance (Holm-adjusted p {T("t_stripped_parallel_vs_instr_distinct_p_holm")}).</p>
<p>Whether the usefulness penalty is fair is the most important open question in this report. Some
of the penalized ideas, such as mapping the distribution of single-cell switching thresholds with
reversal curves, look demanding but feasible for a lab that already does single-cell imaging.
Essays on unrelated topics (any topic, or a randomly assigned one) did not show this effect; they
behaved like the poems and random text.</p>
<figure class="sci-figure" id="fig-tradeoff" data-sci-fig="fig_novelty_usefulness" data-alt="Scatter plot of judged usefulness against judged novelty for the nineteen prompt types. Prompts with material not chosen for relevance cluster near the plain prompt at high usefulness and low novelty. Personas, the self-designed stimuli, the instruction-only prompt and the parallel-problem essay sit further right and lower, with the parallel-problem essay most novel and least useful.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Mean novelty and usefulness per prompt type, as scored from one to five by a second language model that did not know which prompt produced each idea, after metaphors were removed from the ideas. Moving right means more novel; moving down means less useful. Prompts that push novelty pay for it in usefulness; among the most novel prompt types, the instruction-only prompt loses the least usefulness. Marker shapes as in the distinct-ideas figure.</figcaption>
</figure>
</section>

<section id="result-collapse">
<h3>Each prompt that left the choice to the model converged on the same few ideas or analogies</h3>
<p>Each prompt that added variety moved the repetition up a level rather than removing it. The
plain prompt repeats a short list of experiments. Asked to design its own creativity stimulus,
{T("self_designed_shards_phrase")} sessions independently proposed lists of "foreign-domain
mechanism" fragments ({T("self_designed_shards_name_phrase")} used the exact name "Foreign-Domain
Mechanism Shards") and reused the same images: lichen, bell founders, slime mold. The parallel-problem essays
chose magnetism in {T("parallel_essays_magnetic_phrase")} cases, the any-topic essays chose
lighthouses in {T("blind_essays_lighthouse_phrase")}, and the instruction-only prompt reached for
hysteresis in {T("instr_calls_hysteresis_phrase")} calls and immune memory in
{T("instr_calls_immune_phrase")}. Variety appeared only where we assigned it, for example a
different persona or a different random domain for each call, and the random domains did not make
the ideas better.</p>
</section>
"""

CONCLUSIONS = f"""
<p>Random stimuli, the machine version of Oblique Strategies, did not detectably help this model
brainstorm on our question. Material we supplied made no detectable difference when optional and
was largely turned into decoration when required. Apart from the bare instruction, no prompt type
met the bar we set at the outset, beating verbalized sampling on useful-novel ideas: the best of the
first three rounds, the required self-designed stimulus, reached Holm-adjusted p
{T("t_stripped_best_stimulus_vs_vs_useful_novel_p_holm")}, and the best of the model's own essays p
{T("t_stripped_best_stream_vs_vs_useful_novel_p_holm")}.</p>
<p>What did help was an instruction. Asking each idea to borrow from an unrelated domain gave the
most distinct useful-novel ideas, and a two-step prompt that first works through a structurally
similar problem gave the most novel ones. One explanation consistent with both results, which we
have not tested directly, is that connecting a question to another field helps when the model can
pick a relevant field, and that supplying unrelated material pulls it away from relevant ones.</p>
<div class="caveat" id="caveat-main"><span class="caveat-label">Main caveat</span>
<p>Every quality score in this report comes from a single model judge, from the same model family
as the generator; the same generating model also wrote the stripped text that most results use. The
judge may reward analogy-flavored experiments and undervalue technically demanding ones. The
winning prompt was found in the fourth of five rounds, so its advantage is exploratory, and the
study used one research question, one generating model, eight calls per prompt type, and a pre-set cutoff
for "useful and novel" checked at only one looser and one stricter value. The decisive test, blind ratings by scientists, has not been run
yet.</p></div>
"""

NEXT = """
<ul>
<li>Run blind ratings by lab members on a new sheet that includes the instruction-only,
parallel-problem and persona ideas. A sheet covering only the first-round prompts already exists,
and its unblinding key is stored separately.</li>
<li>Force the parallel problems to differ, for example by asking for several structurally distinct
parallels up front and assigning one to each call, then test whether variety at that level carries
through to the ideas.</li>
<li>Repeat the comparison of the plain prompt, verbalized sampling, personas, the instruction alone
and the parallel-problem prompt on a second research question, as a confirmatory test, before
building any of this into our brainstorming tools.</li>
</ul>
"""

PROVENANCE = """
<dl>
<dt><code>scripts/00_design_stimuli.py</code></dt><dd>Self-designed, word-salad and semi-random stimuli, frozen to <code>outputs/stimuli/</code>.</dd>
<dt><code>scripts/00b_streams.py</code></dt><dd>First-step essays for the two-step prompts.</dd>
<dt><code>scripts/01_generate.py</code></dt><dd>All idea generation (one fresh session per call).</dd>
<dt><code>scripts/02_diversity_metrics.py</code></dt><dd>Text-similarity diversity measures, stimulus-leakage tests and permutation tests, on written and stripped text.</dd>
<dt><code>scripts/03_rating_set.py</code></dt><dd>Write-once blind rating sheet for human raters.</dd>
<dt><code>scripts/04_llm_judge.py</code>, <code>scripts/05_judge_analysis.py</code></dt><dd>Model-judge ratings and their analysis, including distinct useful-novel counts.</dd>
<dt><code>scripts/06_strip_decoration.py</code></dt><dd>Rewrite that removes analogies and metaphors.</dd>
<dt><code>scripts/07_report_values.py</code>, <code>scripts/08_figures.py</code></dt><dd>Values quoted in this report, the persona comparison, the cutoff check, the example tables and the figures.</dd>
<dt><code>run.sh</code></dt><dd>Reproduces every output from cached model responses.</dd>
<dt>Report manifest</dt><dd><code>reports/.manifest.json</code> (every value, figure and example row with its source); compile log <code>reports/.compile-log-html.md</code>.</dd>
<dt>Models and software</dt><dd>Generator Claude Sonnet 5.5; judge Claude Opus 5.5; text similarity all-MiniLM-L6-v2; versions in <code>ENVIRONMENTS_INSTALLATIONS.md</code>.</dd>
</dl>
"""

REFERENCES = """
<section id="references"><h2>References</h2>
<ol class="references">
<li id="ref-jiang">Jiang et al. Artificial Hivemind: the open-ended homogeneity of language models. NeurIPS, <time>2025</time>. <a href="https://arxiv.org/abs/2510.22954">arXiv</a></li>
<li id="ref-peeperkorn">Peeperkorn et al. Is temperature the creativity parameter of large language models? International Conference on Computational Creativity, <time>2024</time>. <a href="https://arxiv.org/abs/2405.00492">arXiv</a></li>
<li id="ref-agrawal">Agrawal and Goyal. Addressing LLM diversity by infusing random concepts. <time>2026</time>. <a href="https://arxiv.org/abs/2601.18053">arXiv</a></li>
<li id="ref-zhang">Zhang et al. Verbalized sampling: how to mitigate mode collapse and unlock LLM diversity. <time>2025</time>. <a href="https://arxiv.org/abs/2510.01171">arXiv</a></li>
</ol>
</section>
"""

SUPPLEMENT = f"""
<section id="supp-arms">
<h3>All prompt types</h3>
<p>Every prompt ended with the same task: the research question, followed by a request for five
distinct, concrete ideas, each with a short title and a one-to-two-sentence description. The prompt
types differ only in what came before that task.</p>
<div class="table-wrap wide" id="tab-arms">
<table class="sci-table">
<caption>The nineteen prompt types, in the order they were designed. Quoted wording is exact.</caption>
<thead><tr><th scope="col">Round</th><th scope="col">Prompt type</th><th scope="col">What came before the task</th></tr></thead>
<tbody>
<tr><td>First</td><td>Plain prompt</td><td>Nothing.</td></tr>
<tr><td>First</td><td>Verbalized sampling</td><td>The task reworded to ask for ideas sampled from the full distribution of possible responses, each with its estimated probability of being generated.</td></tr>
<tr><td>First</td><td>Personas</td><td>"Approach this as a Statistical Physicist. [a one-sentence description of that discipline's lens] Bring that lens to the problem.", with a different persona from our brainstorming tool's catalog for each call.</td></tr>
<tr><td>First</td><td>Poem, paragraph, random tokens (optional)</td><td>A public-domain poem, a paragraph about a distant craft (bell founding, contract bridge, thatching), or a string of random characters, introduced with: "Before you start, here is a piece of unrelated material. You may let it inspire your thinking in any way you like, or not."</td></tr>
<tr><td>Second</td><td>Poem, paragraph, random tokens (required)</td><td>The same material, introduced with: "Here is a piece of material that is unrelated to the research question below. Each of your ideas must draw on this material in some way (for example through an analogy, a structure, a principle, or a pattern it suggests), while still being a concrete, scientifically sound way to address the question."</td></tr>
<tr><td>Third</td><td>Self-designed (optional and required)</td><td>A stimulus the generating model wrote in a separate session when asked what material would push it off its default ideas, without seeing the research question. Each one ends with instructions to itself, such as to pick a few fragments and avoid its first ideas.</td></tr>
<tr><td>Third</td><td>Word salad, semi-random (optional and required)</td><td>Random dictionary words, or grammatical sentences filled with random words.</td></tr>
<tr><td>Fourth</td><td>Instruction only</td><td>"{T("winning_instruction_text")}" No material.</td></tr>
<tr><td>Fifth</td><td>Essays: any topic, random domain, parallel problem</td><td>A short associative essay written by the model in a separate session, on a topic of its choice, on a randomly drawn domain, or on a parallel problem in another field with the same structure as the research question; then introduced with the required wording above.</td></tr>
</tbody></table>
</div>
</section>

<section id="supp-measures">
<h3>Definitions and parameters</h3>
<dl>
<dt>Call</dt><dd>One request to the generating model in a fresh session with no tools and no memory; it returns five ideas. Eight calls per prompt type.</dd>
<dt>Embedding and idea groups</dt><dd>Each idea (title and description) was converted by the all-MiniLM-L6-v2 text-similarity model into a list of numbers whose closeness reflects similar meaning. Ideas were merged into groups by average-linkage clustering (repeatedly joining the closest groups) until no two groups were more similar than {V("near_dup_threshold")} on a scale where identical text scores one. The analysis also swept this threshold across stricter and looser values; the report uses the pre-set value throughout.</dd>
<dt>Spread and near-duplicate share</dt><dd>Spread is one minus the mean pairwise similarity of a prompt type's ideas. The near-duplicate share is the fraction of ideas with at least one other idea from the same prompt type above the same similarity threshold. These two were fixed in advance as the main diversity measures; idea-group counts are secondary.</dd>
<dt>Stimulus leakage</dt><dd>How much more an idea resembles its own stimulus than the other stimuli of the same kind. Tested one-sided by reassigning stimuli among the calls of one prompt type, plus the share of ideas reusing a distinctive word from the stimulus.</dd>
<dt>Judge</dt><dd>{"Claude Opus 5.5"} rated every idea on novelty (one: the standard approach most experts list first; five: a direction an expert would probably not have considered) and usefulness (one: would not inform the question or is infeasible; five: feasible in about one to two years and potentially decisive), plus a flag for references that do not belong. Ideas were shown in shuffled batches of twenty with anonymous labels, twice, and the two readings were averaged; the forced-reference figure is the average of the two readings' flags. All nineteen prompt types were judged together so that scores share one context.</dd>
<dt>Useful-novel idea, distinct useful-novel ideas</dt><dd>An idea whose averaged novelty and usefulness are both at least four. Distinct useful-novel ideas are those ideas grouped with the same clustering as above and counted once per group; the grouping always uses the stripped text, including for the as-written counts.</dd>
<dt>Stripped text</dt><dd>Each idea rewritten by the generating model as literal science with analogies, metaphors and outside references removed, in batches of twenty shuffled within groups of rounds (rounds one to three together, then rounds four and five separately) and carrying no label for the prompt type.</dd>
</dl>
<div class="table-wrap" id="tab-cutoff">
  <table class="sci-table" data-sci-table="cutoff_sensitivity" data-columns="prompt_type,distinct_at_3.5,distinct_at_4.0,distinct_at_4.5">
    <caption>Distinct useful-novel ideas (stripped text) when both judge scores must reach a looser, the pre-set, or a stricter cutoff, for the baselines and the three highest-scoring prompt types.</caption>
    <thead><tr><th scope="col">Prompt type</th><th scope="col" class="num">Both scores at least three and a half</th><th scope="col" class="num">At least four (pre-set)</th><th scope="col" class="num">At least four and a half</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-stats">
<h3>Statistics</h3>
<p>Comparisons between prompt types are permutation tests that shuffle whole calls between the two
prompt types (five thousand shuffles), because the five ideas from one call are not independent. The
Holm adjustment corrects a set of p-values for the number of comparisons in the set; we applied it
within sets fixed in advance: one set per round, per baseline (plain prompt or verbalized sampling)
and per measure; one set for each measure across the comparisons of a material with the bare
instruction; and, per measure, one set for the essays against the bare instruction and another for
the essays against the required poem. A set with a single comparison needs no adjustment: the
instruction-only prompt was the only fourth-round prompt type. The comparison with personas was a
single follow-up test added after review and is reported unadjusted. Adding a later round never changes an earlier round's adjusted p-values. The
adjustment does not account for the search across rounds, which is why the fourth-round result is
labeled exploratory. Permutation p-values cannot fall below one in five thousand and one, so the
smallest are reported as a bound.</p>
<p>The as-written results agree in direction with the stripped-text results reported in the main
text. For example, the instruction-only prompt had
{V("judge_written_n_distinct_useful_novel_instruction_only")} distinct useful-novel ideas as written
(p {T("t_written_instr_vs_plain_distinct_p_holm")} against the plain prompt).</p>
</section>

<section id="supp-table">
<h3>Every prompt type in numbers</h3>
<div class="table-wrap wide" id="tab-all">
  <table class="sci-table" data-sci-table="arm_table" data-columns="prompt_type,novelty_stripped,usefulness_stripped,useful_novel_stripped,distinct_useful_novel_stripped,forced_reference_written,clusters_written,clusters_stripped" data-precision="2">
    <caption>Model-judge scores and diversity for all nineteen prompt types. Novelty and usefulness are mean one-to-five scores on the stripped text; useful-novel counts are out of forty; forced references are the average share of as-written ideas the judge flagged as containing a reference that did not belong; idea groups are counted among forty ideas.</caption>
    <thead><tr><th scope="col">Prompt type</th><th scope="col" class="num">Novelty</th><th scope="col" class="num">Usefulness</th><th scope="col" class="num">Useful-novel</th><th scope="col" class="num">Distinct useful-novel</th><th scope="col" class="num">Forced references</th><th scope="col" class="num">Idea groups, as written</th><th scope="col" class="num">Idea groups, stripped</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-events">
<h3>Wording changes and safety stops</h3>
<p>Two automated safety mechanisms intervened, and we did not try to work around either. First, a
request asking the model to "think freely" and write a "stream of thought" was refused outright,
probably by a guard against extracting the model's internal reasoning; the first-step prompts
therefore ask for an ordinary short associative essay instead. Second, while the judge was rating
the final set, a safety classifier stopped one batch, very likely a false positive on routine cell
biology. That stop happened before the pipeline recorded blocked batches, so resuming the run
re-sent the same, unmodified batch, which then completed. No ratings are missing. The pipeline
records any blocked batch and excludes its ideas rather than retrying it.</p>
</section>
"""


SLIDES = f"""
<section class="slide slide--statement" data-source="#result-instruction">
  <h2>Asking the model to borrow from another field gave more distinct good ideas than a plain prompt or verbalized sampling.</h2>
  <div class="stat">{V("judge_stripped_n_distinct_useful_novel_instruction_only")}</div>
  <p class="stat-label">distinct useful and novel ideas out of forty, against {V("judge_stripped_n_distinct_useful_novel_verbalized_sampling")} for verbalized sampling (asking for answers with their probabilities) and {V("judge_stripped_n_distinct_useful_novel_plain")} for the plain prompt. Exploratory: found in round four.</p>
</section>
<section class="slide slide--figure" data-source="#result-instruction">
  <h2>The winning prompt adds one sentence before an ordinary brainstorming request.</h2>
  <div class="slide-figure" data-fig-ref="fig-prompt"></div>
</section>
<section class="slide slide--statement" data-source="#result-examples">
  <h2>A plain brainstorming prompt returns the same short list of experiments in every session.</h2>
  <div class="stat">{V("near_dup_frac_plain")}</div>
  <p class="stat-label">of the forty plain-prompt ideas have a near-duplicate in another session.</p>
</section>
<section class="slide slide--points" data-source="#methods">
  <h2>We compared nineteen prompt types, including the plain prompt and verbalized sampling, on one research question.</h2>
  <ul>
    <li>Does AP-1 act as a cellular memory mechanism? Which experiments would test it?</li>
    <li>Plain prompt, verbalized sampling and personas as baselines; poems, random text, the model's own essays, and a bare instruction as tests.</li>
    <li>Eight fresh sessions per prompt type, five ideas each.</li>
  </ul>
</section>
<section class="slide slide--points" data-source="#methods">
  <h2>A second model scored each idea for novelty and usefulness without knowing which prompt produced it.</h2>
  <ul>
    <li>Ideas were also rewritten with metaphors removed, so new wording is not mistaken for new ideas.</li>
    <li>Main measure: distinct ideas rated at least four out of five for both novelty and usefulness.</li>
  </ul>
</section>
<section class="slide slide--points" data-source="#result-ignored">
  <h2>The model showed no sign of using a poem or random text offered as optional inspiration.</h2>
  <ul>
    <li>Ideas did not resemble their own poem more than other poems (p {T("leakage_p_poem")}).</li>
    <li>Optional poem: {V("n_clusters_poem")} idea groups; plain prompt: {V("n_clusters_plain")}.</li>
  </ul>
</section>
<section class="slide slide--points" data-source="#result-examples">
  <h2>When required to use a poem, the model attached poetic phrases to the plain prompt's usual experiments.</h2>
  <ul>
    <li>"Sensitivity to the second stimulus (the sweetest tune in the gale)"</li>
    <li>"Persistence after stimulus withdrawal (the song that never stops)"</li>
    <li>Both are standard plain-prompt experiments with a line of Dickinson attached.</li>
  </ul>
</section>
<section class="slide slide--statement" data-source="#result-decoration">
  <h2>Removing the metaphors showed that some of the variety from required material was only new wording.</h2>
  <div class="stat">{V("n_clusters_poem_required")} → {V("n_clusters_stripped_poem_required")}</div>
  <p class="stat-label">idea groups for the required poem, as written and with metaphors removed. The plain prompt has {V("n_clusters_stripped_plain")}; the remaining gap is not statistically clear.</p>
</section>
<section class="slide slide--statement" data-source="#result-instruction">
  <h2>Adding a poem or random text to the borrowing instruction made the ideas less novel.</h2>
  <div class="stat">{V("t_stripped_material_vs_instr_novelty_drop_smallest")} to {V("t_stripped_material_vs_instr_novelty_drop_largest")}</div>
  <p class="stat-label">points lower judged novelty, on a five-point scale, than the instruction alone.</p>
</section>
<section class="slide slide--points" data-source="#result-examples">
  <h2>The borrowing instruction produced experiments that the plain prompt never proposed.</h2>
  <ul>
    <li>Permanently label cells that once switched on <em>Fos</em>, then re-stimulate them.</li>
    <li>Ramp the stimulus up and down to look for hysteresis.</li>
    <li>Profile AP-1 on chromosomes during cell division.</li>
  </ul>
</section>
<section class="slide slide--figure" data-source="#result-parallel">
  <h2>Having the model first write about a similar problem in another field produced the most novel ideas.</h2>
  <div class="slide-figure" data-fig-ref="fig-tradeoff"></div>
</section>
<section class="slide slide--statement" data-source="#result-parallel">
  <h2>The judge rated those similar-problem ideas as less useful than the borrowing instruction's ideas.</h2>
  <div class="stat">{V("judge_stripped_usefulness_stream_parallel_required")}</div>
  <p class="stat-label">mean usefulness out of five, against {V("judge_stripped_usefulness_instruction_only")} for the borrowing instruction, so it did not give more distinct good ideas.</p>
</section>
<section class="slide slide--points" data-source="#result-collapse">
  <h2>Whenever the model chose its own analogy, it chose the same few in every session.</h2>
  <ul>
    <li>Instruction only: hysteresis in {T("instr_calls_hysteresis_phrase")} sessions.</li>
    <li>Parallel-problem essays: magnetism in {T("parallel_essays_magnetic_phrase")}.</li>
    <li>Any-topic essays: lighthouses in {T("blind_essays_lighthouse_phrase")}.</li>
  </ul>
</section>
<section class="slide slide--points" data-source="#caveat-main">
  <h2>Every quality score in this test came from a single model judge.</h2>
  <ul>
    <li>Judge and generator come from the same model family; ratings by scientists are pending.</li>
    <li>One question, one generating model, eight sessions per prompt type.</li>
    <li>The winning prompt was found in round four, so its advantage is exploratory.</li>
  </ul>
</section>
<section class="slide slide--points" data-source="#next-steps">
  <h2>The next test assigns a different outside field to each brainstorming session.</h2>
  <ul>
    <li>Blind ratings by lab members, including the newer prompt types.</li>
    <li>Repeat the key comparisons on a second research question.</li>
  </ul>
</section>
"""


def main() -> None:
    s = TEMPLATE.read_text()
    names = {"AP-1": T("factor_name"), "Claude Sonnet 5.5": T("generator_model_name"),
             "Claude Opus 5.5": T("judge_model_name")}
    for k, v in {"%%TITLE%%": TITLE, "%%DEK%%": DEK, "%%PROJECT%%": "Random stimuli for brainstorming",
                 "%%AUTHORS%%": "Arjun Raj, with analysis by Claude", "%%DATE%%": "2026-10-03",
                 "%%ABSTRACT%%": ABSTRACT, "%%PROBLEM_STATEMENT%%": PROBLEM,
                 "%%METHODS_OVERVIEW%%": METHODS, "%%RESULTS%%": RESULTS, "%%CONCLUSIONS%%": CONCLUSIONS,
                 "%%NEXT_STEPS%%": NEXT, "%%PROVENANCE%%": PROVENANCE, "%%SUPPLEMENT%%": SUPPLEMENT}.items():
        if k not in s:
            raise ValueError(f"placeholder {k} missing from template")
        if k not in ("%%TITLE%%", "%%DEK%%", "%%PROJECT%%", "%%AUTHORS%%", "%%DATE%%"):
            for name, span in names.items():
                v = v.replace(name, span)
        s = s.replace(k, v)
    s = s.replace('<section id="supplement"', REFERENCES + '\n    <section id="supplement"', 1)
    # Phase 9 deck (titles from .ghost-deck.md, checked by the blind storyline review).
    slides_html = SLIDES
    for name, span in names.items():
        slides_html = slides_html.replace(name, span)
    s = s.replace("%%SLIDES%%", slides_html)
    # Remove the template's drafting-guidance comments inside <main>; keep sci markers.
    head, rest = s.split('<main id="main">', 1)
    body, tail = rest.split("</main>", 1)
    body = re.sub(r"<!--(?!\s*/?sci-)(?!\s*ANALYSIS_OK)[\s\S]*?-->", "", body)
    s = head + '<main id="main">' + body + "</main>" + tail
    OUT.write_text(s)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
