"""Phase 2: fill the HTML template into ideation-methods-across-models-report.html.

Every reportable number is a value span (data-sci-val / data-sci-text) whose text is filled
from .manifest.json by `scitexlintr --write` in Phase 7; the placeholder text here is "…".
Structural counts are written in words. Slides come from .slides.html (Phase 9).
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parents[2] / ".living/conventions/report-generator/assets/report-template.html"
OUT = HERE / "ideation-methods-across-models-report.html"


def V(i):
    return f'<span data-sci-val="{i}">…</span>'


def T(i):
    return f'<span data-sci-text="{i}">…</span>'


HAIKU, SONNET, OPUS = T("model_name_haiku"), T("model_name_sonnet"), T("model_name_opus")


def P(prefix):
    """'p = 0.012' from a registered p string such as '= 0.012' or '< 0.001'."""
    return f"p {T(prefix + '_p')}"


TITLE = "Pushing a language model past its obvious ideas gave the research ideas a model judge rated best"
DEK = ("Nine prompts, three Claude models, two cell-biology questions, one blind model judge. On the main measure the "
       "plain prompt gave no idea the judge rated both novel and useful, and prompts that showed the model its own "
       "default ideas did best, most of all for the largest model. No scientist has rated the ideas yet.")

ABSTRACT = f"""
<p>Asked for research ideas, language models tend to return the same standard experiments. We tested nine ways of
prompting for ideas, seven of them new, on three models of different size ({HAIKU}, {SONNET} and {OPUS}) and two
cell-biology research questions, {V("n_ideas_total")} ideas in all. A judge model ({T("judge_model_name")}) scored
every idea for novelty and usefulness without knowing its source, after a rewrite that stripped analogies. Our main measure counts <em>distinct useful-novel ideas</em>: ideas rated at
least four out of five on both scales, with near-duplicates merged.</p>
<p>On this measure the plain prompt scored {V("distinct_pooled_plain")} for every model. The best prompt,
<em>critique and revise</em>, showed the model its own plain-prompt ideas as obvious and asked for replacements; it
gave {V("distinct_pooled_critique_revise")} of {V("n_ideas_per_prompt_all_models")}. A related
prompt that has the model list the obvious ideas and then avoid them gave {V("distinct_pooled_obvious_then_avoid")}.
Of the seven new prompts, {V("n_methods_beating_plain_pooled")} beat the plain prompt after correction for multiple
comparisons, but only critique and revise beat the best prompt from an earlier study, an instruction to borrow from an
unrelated field, by {V("h2_instruction_only_critique_revise_distinct_useful_novel_diff")} ideas. The gains were largest
for {OPUS}: critique and revise added {V("h2_plain_opus_critique_revise_distinct_diff")} ideas for it,
{V("h2_plain_sonnet_critique_revise_distinct_diff")} for {SONNET} and {V("h2_plain_haiku_critique_revise_distinct_diff")}
for {HAIKU}. A second judge model ({T("cross_judge_model_name")}) agreed on the best and worst prompts. In a follow-up,
requiring every idea to use a poem or a list of random words did no better than that instruction. Every score comes from language-model judges; no scientist has rated these
ideas yet.</p>
"""

PROBLEM = f"""
<p>Ask a language model for ten research ideas and you get a sensible list. Ask again and you get a largely overlapping
list. This repetition, often called <em>mode collapse</em>, means a scientist using a model to widen their
thinking mostly hears the textbook answers back. An earlier study in this repository asked whether unrelated
material (poems, random words, essays) placed before the prompt fixes this. It did not. The one prompt that
helped was a single sentence telling the model that each idea must borrow from a field unrelated to the
question (we call this the <em>unrelated-domain instruction</em>). That study had three limits. It used one model and
one research question, and its winning prompt was designed in the fourth of five rounds of trying things, which makes
that result exploratory.</p>
<p>This report asks a broader question. <strong>Which ways of asking for ideas make a model produce more ideas
that are both new and worth doing, and does the answer depend on the model?</strong> We designed seven new
prompts, each aimed at a specific reason a model might fall back on the obvious, and compared them with the
plain prompt and with the unrelated-domain instruction. We tested every prompt on three models of different
size and on two research questions. In a follow-up, we also brought back two of the earlier study's material prompts,
a poem and a list of random words, in the one form that had changed its model's ideas: every idea had to use the
material.</p>
<p>The measure that matters is whether a prompt yields ideas a scientist would find both surprising and
feasible. We approximate this with a judge model that scores each idea for <em>novelty</em> (would an expert
have thought of it?) and <em>usefulness</em> (could a typical lab do it within a year or two, and would the result
be informative?). A <em>useful-novel idea</em> scores at least four out of five on both. We ask each model for ideas many times, each time in a fresh, separate request with no memory of the others
(a <em>call</em>, which returns five ideas). Because a model can repeat one good idea in call after call, we count <em>distinct useful-novel ideas</em>: useful-novel ideas after merging
near-duplicates. A good answer is a prompt that raises this count well above the plain prompt, ideally for
every model.</p>

<section id="examples">
<h3>What the ideas look like</h3>
<p>Here is what the difference looks like in practice. The first five ideas below are the
first plain-prompt call to {OPUS} on the drug-tolerance question (why do a few genetically identical cancer
cells survive a targeted drug?). They are the experiments a researcher in the field would list first: lineage
barcoding, fluctuation analysis, live imaging, pooled genetic screens. The judge rated them highly useful but
not novel, so {V("example_n_un_opus_plain")} of them count as useful-novel. The next five come from the
<em>critique and revise</em> prompt, which showed {OPUS} exactly those five plain ideas and asked for less
obvious replacements; {V("example_n_un_opus_critique_revise")} of them count as useful-novel. The last five are
{HAIKU}'s replacements under the same prompt (shown {HAIKU}'s own plain ideas). The judge rated them novel but less
useful, and {V("example_n_un_haiku_critique_revise")} of them pass both bars.</p>
<div class="table-wrap" id="tab-examples">
  <table class="sci-table" data-sci-table="tab_example_ideas" data-columns="example,title,novelty,usefulness,useful_novel" data-precision="1">
    <caption>Fifteen example ideas for the drug-tolerance question, from the first call of three prompt and model
    combinations (chosen in advance, not by score). Scores are the judge's means over two readings on a
    one-to-five scale; "useful-novel" means both are at least four.</caption>
    <thead><tr><th>Model and prompt</th><th>Idea (title as written)</th><th class="num">Novelty</th><th class="num">Usefulness</th><th>Useful-novel</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>
"""

METHODS = f"""
<p>In outline: each model answered each prompt in many separate, fresh calls, a rewrite step removed
decorative language, a judge model scored every idea blind, and statistical tests compared prompts by shuffling
whole calls between them. The supplement gives the full wording of every prompt and all parameters. The
design, prompts, outcome and tests were written down before any idea was generated (the pre-registration is in
the analysis folder). The analyses labeled <em>exploratory</em> below, including a follow-up with two more prompts
described at the end of this section, were added after seeing the results.</p>

<h3>Nine prompts</h3>
<p>Every prompt asks for five concrete ideas (analyses, measurements or experiments), each with a short title and
one or two sentences of description. They differ in what comes before or around that request.</p>
<dl>
  <dt>Plain prompt</dt><dd>The request alone. This is the baseline.</dd>
  <dt>Unrelated-domain instruction</dt><dd>Each idea must borrow an analogy, structure, principle or pattern from
  a domain unrelated to the question. This was the best prompt in the earlier study; here it is a pre-specified
  replication.</dd>
  <dt>Assigned parallel problem</dt><dd>The model first lists eight problems from eight different fields that share
  the question's structure. Each later call receives one of them and must transfer a method from it. This keeps
  the earlier study's most novel approach but forces variety, because in that study the model picked the same
  parallel (magnetic hysteresis) nearly every time.</dd>
  <dt>List the obvious, then avoid it</dt><dd>The model first lists the ten ideas most experts would propose, then
  gives five ideas that are none of them.</dd>
  <dt>Overgenerate, then select</dt><dd>The model brainstorms twenty one-line candidates, then picks and develops
  the five that best combine being non-obvious with being feasible.</dd>
  <dt>Invert an assumption</dt><dd>The model lists the hidden assumptions in the question and in how the field
  usually tests it; each idea must test or exploit the failure of a different one.</dd>
  <dt>Assigned constraint</dt><dd>Each call gets one constraint from a fixed list of eight, such as using only data
  that are already public, or using no genetic perturbation, and every idea must respect it.</dd>
  <dt>Critique and revise</dt><dd>A second, fresh call shows the model the five ideas it gave to the plain prompt
  in the matching call, says a senior expert finds them the ideas everyone would propose first, and asks for five
  less obvious but feasible replacements.</dd>
  <dt>Future retrospective</dt><dd>The model imagines it is <time>2036</time> and that five landmark papers each settled the
  question in a way that surprised the field, and describes what each one measured or did.</dd>
</dl>

<h3>Models, questions and calls</h3>
<p>The three generators were {HAIKU}, {SONNET} and {OPUS}, the small, medium and large models of the same
family. The two research questions were the earlier study's question, "{T("question_ap1")}" (the <em>cellular-memory
question</em>; {T("factor_name")} is a family of gene-regulating proteins), and a new one from a
different part of cell biology, "{T("question_persister")}" (the drug-tolerance or <em>persister</em> question).
Each prompt was sent to each model eight times per question, every time as a fresh call with no memory
of the others, for {V("n_generation_calls")} calls and {V("n_ideas_total")} ideas. A <em>condition</em> of the design (one
question, model and prompt) therefore holds forty ideas, and each model and prompt holds eighty across the two
questions. Two-step prompts used the same model for both steps.</p>

<h3>Removing decoration, then judging blind</h3>
<p>Prompts that ask for analogies produce ideas phrased in another field's vocabulary ("Weibull reliability analysis:
treating cell death as material fracture"). A judge, or an embedding model, can mistake that vocabulary for new
science. So before judging, {SONNET} rewrote every idea in plain scientific language, keeping the experiment and
removing analogy, metaphor and numbered framing labels such as "Paper … (hypothetical)". The rewriter saw ideas in
shuffled batches and was never told which prompt or model wrote them. We call the result the <em>stripped
text</em>; all primary results use it.</p>
<p>{T("judge_model_name")} then scored each stripped idea for novelty and usefulness on one-to-five scales, in
shuffled batches of twenty that mixed prompts and models, with opaque labels. It read every idea twice in
different batches; the two readings agreed with rank correlations of {V("pass_agreement_novelty")} for novelty
and {V("pass_agreement_usefulness")} for usefulness. We average the two readings. Because {OPUS} is both a
generator and the judge, we also had {T("cross_judge_model_name")} judge every stripped idea once, and had
{T("judge_model_name")} judge the original, unstripped wording once.</p>

<h3>Counting distinct useful-novel ideas</h3>
<p>Within each condition, useful-novel ideas are grouped by meaning: we embed each stripped idea as a vector (a sentence
embedding model) and merge ideas whose vectors are very similar (cosine similarity of at least {V("near_dup_threshold")}, average-linkage
clustering). Each group counts once, and the counts are summed over questions. The worked example below follows one
idea through these steps. In its condition, {V("worked_cell_n_un")} ideas were useful-novel and they formed
{V("worked_cell_n_distinct")} groups; the largest group shows three phrasings of the same experiment (single-cell
apoptotic priming) that count as one.</p>
<div class="table-wrap" id="tab-worked">
  <table class="sci-table" data-sci-table="tab_worked_example" data-columns="step,value">
    <caption>Worked example: one idea from the critique-and-revise prompt ({OPUS}, drug-tolerance question, first
    call), traced from its written title to its contribution to the distinct useful-novel count.</caption>
    <thead><tr><th>Step</th><th>Value</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>

<h3>Follow-up: required unrelated material</h3>
<p>After the main results were in, we added two prompts from the earlier study as an exploratory follow-up. Each call
supplied an unrelated poem (eight public-domain poems) or a list of sixty random dictionary words (eight lists), and
every idea had to draw on that material, for example through an analogy, structure, principle or pattern. The earlier
study's model used such material only when told it must. Both prompts ran on all three models and both questions
({V("n_followup_calls")} calls, {V("n_followup_ideas")} ideas), with the same stripping and primary judge.</p>
<p>The follow-up ideas were judged in batches separate from the main study's, each made of ten follow-up ideas and ten
already-judged main-study ideas that served as anchors for comparing the two judging runs. The judge ranked the anchors much as it had in the main run (rank
correlations of {V("fu_anchor_novelty_rho")} for novelty and {V("fu_anchor_usefulness_rho")} for usefulness, close to
the {V("pass_agreement_novelty_ref")} agreement between the main run's two readings for novelty), but it scored them
higher on novelty, by {V("fu_anchor_novelty_shift")} points on average (usefulness {V("fu_anchor_usefulness_shift")}).
As a result, the share of anchor ratings clearing both bars rose from {V("fu_anchor_un_rate_primary")} to
{V("fu_anchor_un_rate_followup")}. Many follow-up ideas sit exactly at the novelty cutoff, so we report their counts
both as scored and after subtracting the anchors' average shifts from every follow-up score; the true values probably
lie between the two. The second judge model and the original-wording run do not cover the follow-up.</p>

<h3>Statistical tests</h3>
<p>Ideas from the same call are not independent, so the call is the unit of every test. To compare two prompts we
pool their calls within each question and model, shuffle which calls belong to which prompt
{V("n_permutations")} times, and ask how often a shuffled difference is as large as the real one (a two-sided
permutation test). Adjusted p-values use the Holm correction: over the three models for the replication test, and
over the seven new prompts for each comparison of new prompts with a baseline.</p>
"""

R1 = f"""
<section id="result-plain-zero">
<h3>The plain prompt scored zero on the main measure, and five new prompts did significantly better</h3>
<p>If prompting made no difference, every prompt would yield about the same number of distinct useful-novel
ideas. Instead, the plain prompt yielded {V("distinct_pooled_plain")} distinct useful-novel ideas out of
{V("n_ideas_per_prompt_all_models")}, across all three models and both questions <a class="xref" href="#fig-distinct">Figure</a>. Its ideas were
judged useful (mean {V("usefulness_pooled_plain")} out of five) but not novel (mean
{V("novelty_pooled_plain")}). Pooled over models, {V("n_methods_beating_plain_pooled")} of the seven new prompts beat it (p-values adjusted for
the seven comparisons with the plain prompt):</p>
<ul>
  <li>critique and revise, +{V("h2_plain_critique_revise_distinct_useful_novel_diff")} ({P("h2_plain_critique_revise_distinct_useful_novel")});</li>
  <li>list the obvious, then avoid it, +{V("h2_plain_obvious_then_avoid_distinct_useful_novel_diff")} ({P("h2_plain_obvious_then_avoid_distinct_useful_novel")});</li>
  <li>overgenerate, then select, +{V("h2_plain_overgenerate_select_distinct_useful_novel_diff")} ({P("h2_plain_overgenerate_select_distinct_useful_novel")});</li>
  <li>invert an assumption, +{V("h2_plain_assumption_inversion_distinct_useful_novel_diff")} ({P("h2_plain_assumption_inversion_distinct_useful_novel")});</li>
  <li>future retrospective, +{V("h2_plain_future_retrospective_distinct_useful_novel_diff")} ({P("h2_plain_future_retrospective_distinct_useful_novel")}).</li>
</ul>
<p>The assigned parallel problem (+{V("h2_plain_parallel_rotated_distinct_useful_novel_diff")},
{P("h2_plain_parallel_rotated_distinct_useful_novel")}) and the assigned constraint
(+{V("h2_plain_assigned_constraint_distinct_useful_novel_diff")},
{P("h2_plain_assigned_constraint_distinct_useful_novel")}) did not. Every new prompt raised judged novelty over
the plain prompt (largest adjusted p {T("max_p_novelty_new_vs_plain")}), but mean scores alone do not predict which prompts cleared both bars. The assigned
parallel problem raised novelty by +{V("h2_plain_parallel_rotated_novelty_diff")} points and still failed, while
overgenerate, then select raised it by only +{V("h2_plain_overgenerate_select_novelty_diff")} and succeeded. The pattern held on both questions: critique and revise gave the most
distinct useful-novel ideas on each, and the plain prompt gave none on either
(<a class="xref" href="#tab-by-question">Table</a>).</p>
<figure class="sci-figure" id="fig-distinct" data-sci-fig="fig_distinct_by_model" data-alt="Dot plot of distinct useful-novel ideas for each prompt, one marker per model. Plain prompt is at zero for all models; Opus markers lie far to the right for most prompts.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Distinct useful-novel ideas for each prompt (rows, ordered by the total over models) and model
  (marker shape and color), out of eighty ideas per model and prompt. Primary judge, stripped text. Open markers below
  the dashed line are the two follow-up prompts, judged separately (exploratory; counts as scored, before the
  drift adjustment described in Methods). Exact values are in the supplement
  table of results by model.</figcaption>
</figure>
</section>
"""

R2 = f"""
<section id="result-confront">
<h3>The two prompts that show the model its default ideas gave the most distinct useful-novel ideas</h3>
<p>The two strongest prompts both put the obvious ideas in front of the model and ask it to go elsewhere. Critique and revise does this with the model's own earlier answers; list the obvious, then avoid it
has the model write the obvious list itself. Critique and revise was the only new prompt that beat the
unrelated-domain instruction from the earlier study, by {V("h2_instruction_only_critique_revise_distinct_useful_novel_diff")}
distinct useful-novel ideas ({P("h2_instruction_only_critique_revise_distinct_useful_novel")}, adjusted for the seven
comparisons with the instruction). List the
obvious, then avoid it was ahead by {V("h2_instruction_only_obvious_then_avoid_distinct_useful_novel_diff")} but not
significantly ({P("h2_instruction_only_obvious_then_avoid_distinct_useful_novel")}). The assigned constraint fell
significantly behind the instruction
({V("h2_instruction_only_assigned_constraint_distinct_useful_novel_diff")},
{P("h2_instruction_only_assigned_constraint_distinct_useful_novel")}).</p>
<p>The examples above show what this looks like. Critique and revise moved {OPUS} off lineage barcoding and
pooled screens toward ideas such as allele-resolved readout of the rare high-expressing state, sorting cells and
fitting how fast they relax back, and changing the rate at which cells enter the tolerant state without touching
resistance genes. Critique and revise costs a second call, since it needs the plain answer first; list the
obvious, then avoid it gets a similar effect in one call for {OPUS} but not for {SONNET}.</p>
</section>
"""

R3 = f"""
<section id="result-replication">
<h3>The earlier study's instruction replicated overall and was significant on its own only for the largest model</h3>
<p>The unrelated-domain instruction was the earlier study's best prompt, designed late in that study; here we
specified in advance that it should beat the plain prompt. Pooled over models it did, by
{V("h1_pooled_distinct_diff")} distinct useful-novel ideas ({P("h1_pooled_distinct")}), raising novelty by
{V("h1_pooled_novelty_diff")} points and changing usefulness by {V("h1_pooled_usefulness_diff")}. Tested model by
model, with p-values adjusted for the three models, the gain was significant for {OPUS} (+{V("h1_opus_distinct_diff")},
{P("h1_opus_distinct")}) but not for {SONNET} (+{V("h1_sonnet_distinct_diff")}, {P("h1_sonnet_distinct")}) or
{HAIKU} (+{V("h1_haiku_distinct_diff")}, {P("h1_haiku_distinct")}). The earlier study used {SONNET}, where the
effect here is smaller and not significant on its own; with only eighty ideas per model and prompt, small effects are
hard to detect.</p>
</section>
"""

R4 = f"""
<section id="result-models">
<h3>The largest model gained the most from the new prompts</h3>
<p>If prompt design works the same way regardless of model, each prompt should help the three models by similar
amounts. The gains were much larger for {OPUS}, although we did not test the difference between models
formally and the smaller models' tests have little power. With {OPUS}, {V("n_methods_beating_plain_opus")} of the seven new prompts beat the plain prompt
on their own (p-values adjusted for the seven prompts within that model): critique and revise and list the obvious, then avoid it
(+{V("h2_plain_opus_critique_revise_distinct_diff")} and +{V("h2_plain_opus_obvious_then_avoid_distinct_diff")}),
overgenerate, then select (+{V("h2_plain_opus_overgenerate_select_distinct_diff")}), invert an assumption, and future
retrospective. With {SONNET}, {V("n_methods_beating_plain_sonnet")} did: critique and revise
(+{V("h2_plain_sonnet_critique_revise_distinct_diff")}, {P("h2_plain_sonnet_critique_revise_distinct")}). With
{HAIKU}, {V("n_methods_beating_plain_haiku")} did, although critique and revise and list the obvious, then avoid it
each produced {V("distinct_haiku_critique_revise")} distinct useful-novel ideas of
{V("n_ideas_per_model_prompt")}, against {V("distinct_haiku_plain")} for the plain prompt.</p>
<p>The models differ in how their new ideas fall short. Under critique and revise, {HAIKU}'s ideas were judged
nearly as novel as {OPUS}'s (mean novelty {V("novelty_haiku_critique_revise")} against
{V("novelty_opus_critique_revise")}) but less useful ({V("usefulness_haiku_critique_revise")} against
{V("usefulness_opus_critique_revise")}), so fewer cleared both bars, as in the examples above. {SONNET}'s ideas were
judged the least novel of the three models for {V("n_prompts_sonnet_least_novel")} of the nine prompts. The order of prompts was similar for {HAIKU} and {SONNET} and less so
between {SONNET} and {OPUS}: rank correlations of the gains over the plain prompt were {V("h3_spearman_haiku_sonnet")} between {HAIKU} and
{SONNET}, {V("h3_spearman_haiku_opus")} between {HAIKU} and {OPUS}, and {V("h3_spearman_sonnet_opus")} between
{SONNET} and {OPUS}. Critique and revise ranked first or tied for first for all three.</p>
</section>
"""

R5 = f"""
<section id="result-tradeoff">
<h3>Most prompts traded usefulness for novelty; overgenerate, then select did not</h3>
<p>A prompt that pushes a model away from standard experiments could instead push it toward impractical ones. For
most prompts the judge saw that trade <a class="xref" href="#fig-tradeoff">Figure</a>. Pooled over models,
critique and revise changed novelty by +{V("h2_plain_critique_revise_novelty_diff")} points and usefulness by
{V("h2_plain_critique_revise_usefulness_diff")}; list the obvious, then avoid it changed novelty by
+{V("h2_plain_obvious_then_avoid_novelty_diff")} and usefulness by
{V("h2_plain_obvious_then_avoid_usefulness_diff")}. Overgenerate, then select was the exception: it raised novelty
by {V("h2_plain_overgenerate_select_novelty_diff")} with no detectable loss of usefulness
({V("h2_plain_overgenerate_select_usefulness_diff")}, {P("h2_plain_overgenerate_select_usefulness")}). For {OPUS},
its ideas were as useful as the plain prompt's (means {V("usefulness_opus_overgenerate_select")} and
{V("usefulness_opus_plain")}). Either the selection step or the prompt's explicit request for feasible ideas may keep feasibility in view; the design
cannot tell which.
The assigned constraint lost almost as much usefulness ({V("h2_plain_assigned_constraint_usefulness_diff")}) as
critique and revise while gaining far less novelty, plausibly because constraints such as a single time point per
sample limit what an idea can test; we did not analyze the constraints one by one.</p>
<figure class="sci-figure wide" id="fig-tradeoff" data-sci-fig="fig_tradeoff" data-alt="Three scatter panels, one per model, of mean judged usefulness against mean judged novelty for each numbered prompt. In each panel the plain prompt is high on usefulness and low on novelty, and most prompts lie down and to the right of it.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Mean judged novelty (horizontal) against mean judged usefulness (vertical) for each prompt
  (numbered; key below the panels), one panel per model. Each point averages eighty ideas. Points to the right are
  more novel; points lower down are less useful. Open markers (numbered ten and eleven) are the two follow-up prompts.</figcaption>
</figure>
</section>
"""

R6 = f"""
<section id="result-judges">
<h3>A second judge, the original wording, and a lower cutoff agreed on the best and worst prompts</h3>
<p>Three checks address the obvious worries about a model judge. First, {OPUS} judging {OPUS}'s ideas might
favor its own style. {T("cross_judge_model_name")} judging the same stripped ideas agreed with the primary judge
idea by idea (rank correlation {V("sonnet_stripped_agreement_novelty")} for novelty and
{V("sonnet_stripped_agreement_usefulness")} for usefulness), ranked critique and revise first and the plain prompt
last ({V("sonnet_stripped_distinct_pooled_critique_revise")} and {V("sonnet_stripped_distinct_pooled_plain")}
distinct useful-novel ideas of {V("n_ideas_per_prompt_all_models")}), and found {V("sonnet_stripped_n_methods_beating_plain")} of the seven new prompts
significantly better than the plain prompt, against five for the primary judge <a class="xref" href="#fig-judges">Figure</a>. It also rated {OPUS}'s
ideas the most novel of the three models (mean {V("sonnet_stripped_gen_novelty_opus")}, against
{V("sonnet_stripped_gen_novelty_haiku")} for {HAIKU} and {V("sonnet_stripped_gen_novelty_sonnet")} for its own
model), so the advantage of {OPUS} is not only self-preference by the primary judge.</p>
<p>Second, stripping could have hidden or created differences. {T("judge_model_name")} judging the original wording
gave higher counts for every prompt, including a few for the plain prompt, but the same best and worst prompts
(critique and revise {V("opus_written_distinct_pooled_critique_revise")}, plain prompt
{V("opus_written_distinct_pooled_plain")}, of {V("n_ideas_per_prompt_all_models")} each). The plain prompt's zero in the main analysis therefore depends partly on
judging the stripped text.
Third, the cutoff of four is arbitrary. With a cutoff of {V("cutoff_low")} the same two prompts lead and the same two trail; at
{V("cutoff_high")} almost no idea from any prompt qualifies, too few to rank prompts (supplement). Counts differ in level between the three runs (a single
reading is noisier than the average of two, which pulls extreme scores toward the middle), so only the order of
prompts should be compared across runs.</p>
<figure class="sci-figure" id="fig-judges" data-sci-fig="fig_judges" data-alt="Dot plot of distinct useful-novel ideas for nine prompts under three judging runs. All three put critique and revise first and the plain prompt last.">
  <div class="sci-media"><!-- sci-media --><!-- /sci-media --></div>
  <figcaption>Distinct useful-novel ideas per prompt, pooled over models and questions (out of {V("n_ideas_per_prompt_all_models")}), under three
  judging runs: the primary judge on stripped text with two readings, a second judge model on stripped text with one
  reading, and the primary judge model on the original wording with one reading.</figcaption>
</figure>
</section>
"""

R7 = f"""
<section id="result-complementary">
<h3>Exploratory: the two best prompts found mostly different ideas</h3>
<p>These two analyses were added after seeing the results. First, if critique and revise and list the obvious,
then avoid it merely reached the same second tier of ideas, running both would add little. For {OPUS}, each gave
{V("union_opus_critique_revise")} distinct useful-novel ideas (of {V("n_ideas_per_model_prompt")}) and together they gave
{V("union_opus_critique_plus_obvious")} (of {V("n_ideas_two_prompts_per_model")}), so most were different. Across all eight
non-plain prompts ({V("n_ideas_non_plain_per_model")} ideas per model), {OPUS} produced
{V("union_opus_all_non_plain")} distinct useful-novel ideas, against {V("union_haiku_all_non_plain")} for {HAIKU} and
{V("union_sonnet_all_non_plain")} for {SONNET}. Running several prompts may therefore add more breadth than running one prompt more often, though we did not
compare the two at equal numbers of calls.</p>
<p>Second, cost. Using the per-call costs reported by the command-line tool (equivalent to pay-per-use pricing),
a plain call cost about {T("cost_per_call_haiku_plain")} for {HAIKU} and {T("cost_per_call_opus_plain")} for
{OPUS}. Per distinct useful-novel idea, critique and revise cost {T("cost_per_distinct_haiku_critique_revise")}
with {HAIKU} and {T("cost_per_distinct_opus_critique_revise")} with {OPUS}, counting the plain call it depends
on. {HAIKU} gives far fewer good ideas, and a person still has to read past its weaker ones, which this figure
does not count.</p>
</section>
"""

R8 = f"""
<section id="result-followup">
<h3>Follow-up: requiring the model to use a poem or random words did no better than the unrelated-domain instruction</h3>
<p>The earlier study found that unrelated material changed a model's ideas only when every idea had to use it, so the
follow-up tested its poem and random-word prompts in that form. Neither beat the unrelated-domain instruction. As scored,
the required poem gave {V("distinct_pooled_poem_required")} distinct useful-novel ideas of
{V("n_ideas_per_prompt_all_models")} and the required random words gave {V("distinct_pooled_word_salad_required")},
against {V("distinct_pooled_instruction_only")} for the instruction (differences of
{V("fu_instruction_only_poem_required_distinct_useful_novel_diff")},
{P("fu_instruction_only_poem_required_distinct_useful_novel")}, and
{V("fu_instruction_only_word_salad_required_distinct_useful_novel_diff")},
{P("fu_instruction_only_word_salad_required_distinct_useful_novel")}). Both totals fall in the lower half of the
main study's range <a class="xref" href="#fig-distinct">Figure</a>, above only the assigned parallel problem, the
assigned constraint and the plain prompt. Nearly all of these ideas came from {OPUS}
({V("distinct_opus_poem_required")} and {V("distinct_opus_word_salad_required")} of {V("n_ideas_per_model_prompt")});
{SONNET} produced {V("distinct_sonnet_poem_required")} and {V("distinct_sonnet_word_salad_required")}.</p>
<p>The material moved ideas away from the standard experiments less than the instruction did. Against the plain prompt
it raised novelty by +{V("fu_plain_poem_required_novelty_diff")} and +{V("fu_plain_word_salad_required_novelty_diff")}
points and changed usefulness by {V("fu_plain_poem_required_usefulness_diff")} and
{V("fu_plain_word_salad_required_usefulness_diff")}. Against the instruction, novelty was lower and usefulness higher
(differences of {V("fu_instruction_only_poem_required_novelty_diff")} and
{V("fu_instruction_only_word_salad_required_novelty_diff")} for novelty, +{V("fu_instruction_only_poem_required_usefulness_diff")}
and +{V("fu_instruction_only_word_salad_required_usefulness_diff")} for usefulness). As scored, both prompts also beat the
plain prompt on the main measure (+{V("fu_plain_poem_required_distinct_useful_novel_diff")},
{P("fu_plain_poem_required_distinct_useful_novel")}; +{V("fu_plain_word_salad_required_distinct_useful_novel_diff")},
{P("fu_plain_word_salad_required_distinct_useful_novel")}; adjusted over the two follow-up prompts), but that edge is
not reliable. The judge scored novelty higher in the follow-up run than in the main one (see Methods), and after
subtracting that drift the counts fall to {V("fu_adjusted_distinct_poem_required")} and
{V("fu_adjusted_distinct_word_salad_required")}.</p>
</section>
"""

CONCLUSIONS = f"""
<p>The question was which ways of asking a model for research ideas yield more ideas that are both new and worth
doing. On two cell-biology questions and three models, the direction of the answer was clear. The plain prompt
yielded no distinct useful-novel idea in the main analysis. Prompts that show the model its own default ideas (critique
and revise, and list the obvious, then avoid it) yielded the most. Critique and revise was the only prompt to beat
the earlier study's unrelated-domain instruction, and that instruction itself replicated when pooled over models.
Overgenerate, then select was the one prompt that raised novelty without lowering usefulness. In the follow-up,
a poem or random words that each idea had to use landed in the lower half of the field, no better than asking the model
to borrow from an unrelated field of its own choosing.</p>
<p>The size of the gain differed by model. Most of it came from {OPUS}. Among the smaller models, only
critique and revise with {SONNET} reached significance on its own; we did not formally test whether the models
differ. A plausible reading, which this study does
not test directly, is that a larger model knows more of the less-traveled experiments and can reach them once told
the obvious ones are off the table, while a smaller model asked for less obvious ideas tends to produce less
feasible ones.</p>
<div class="caveat" id="main-caveat"><span class="caveat-label">Main caveat</span>
<p>Every quality score in this report comes from language-model judges. The judges agree with each other and with
themselves, and a second judge model picks the same best and worst prompts, but no scientist has rated these ideas. A model judge
may share the generators' blind spots, may reward ideas that sound unusual more than ideas a lab would actually run,
and is one of the three generators. The usefulness penalties in particular need checking by people who run these
experiments.</p></div>
<p>Further limits: both questions come from cell biology and from the same research area; each model and prompt
produced eighty ideas from one run, so modest effects for {HAIKU} and {SONNET} could be missed; critique and
revise uses two calls and so more compute than the single-call prompts; and the exploratory analyses (complementarity
and cost) were not planned in advance.</p>
"""

NEXT = """
<ul>
  <li><strong>Blind ratings by scientists.</strong> Build a rating sheet from the plain prompt, critique and revise, list
  the obvious, then avoid it, and overgenerate, then select, for the largest and smallest models, and have lab members
  rate novelty and usefulness without knowing the source.</li>
  <li><strong>Combine the strongest prompts.</strong> Test a pipeline that runs overgenerate, then select, followed by a
  critique-and-revise round, and check whether it keeps usefulness while raising novelty.</li>
  <li><strong>Use it in practice.</strong> Add a critique-and-revise step to the repository's persona-based
  brainstorming skill (a tool that has the model brainstorm in the voice of several expert
  personas) and compare its output with the current version on a live project question.</li>
  <li><strong>Test outside cell biology.</strong> Repeat the design on questions from a field where the judge models know
  less, to see whether the ranking holds.</li>
</ul>
"""

PROVENANCE = """
<dl>
  <dt><code>scripts/01_generate.py</code></dt><dd>Writes the eight parallel problems per model and question, then sends
  every generation call and writes <code>outputs/ideas.csv</code>.</dd>
  <dt><code>scripts/02_strip.py</code></dt><dd>Prompt- and model-blind rewrite of every idea without analogy or framing
  (<code>outputs/ideas_stripped.csv</code>).</dd>
  <dt><code>scripts/03_embed.py</code></dt><dd>Sentence embeddings of the written and stripped text.</dd>
  <dt><code>scripts/04_judge.py</code></dt><dd>Blind judging; three runs (primary, second judge model, original wording).</dd>
  <dt><code>scripts/05_analysis.py</code></dt><dd>Pre-registered tests, judge checks, cutoff sensitivity, and the
  exploratory complementarity and cost analyses (<code>outputs/analysis_summary.json</code>).</dd>
  <dt><code>scripts/06_figures.py</code></dt><dd>The three report figures.</dd>
  <dt><code>scripts/07_report_values.py</code></dt><dd>Registers every value the report quotes and writes the embedded tables.</dd>
  <dt>Shared modules</dt><dd><code>config.py</code> (all parameters), <code>prompts.py</code> (prompt wording),
  <code>llm.py</code> (isolated command-line calls), <code>common.py</code> (helpers).</dd>
  <dt>Pre-registration and write-up</dt><dd><code>IDEATION_METHODS_ACROSS_MODELS.md</code> in the analysis folder.</dd>
  <dt>Report build</dt><dd>Manifest <code>reports/.manifest.json</code>; compile log <code>reports/.compile-log-html.md</code>.
  Reproduce everything with <code>run.sh</code>; all model responses are cached.</dd>
  <dt>Analyst</dt><dd>Arjun Raj, with Claude (analysis and drafting).</dd>
</dl>
"""

SUPPLEMENT = f"""
<section id="supp-prompts">
<h3>Prompt wording</h3>
<p>Every prompt except the future retrospective and critique and revise is built around the plain request: "Research question:
[question]. Propose five distinct, concrete ideas (analyses, measurements, or experiments) that a research lab could
pursue to address this question. For each idea give a short title and a description of one or two sentences." (The
number is a word only in this report; the prompts use the numeral.) The additions are:</p>
<dl>
  <dt>Unrelated-domain instruction (before)</dt><dd>"Each of your ideas must draw on a domain unrelated to the research
  question below, for example through an analogy, a structure, a principle, or a pattern borrowed from that domain,
  while still being a concrete, scientifically sound way to address the question."</dd>
  <dt>Assigned parallel problem (before)</dt><dd>The field, the parallel problem and how that field studies it, then:
  "Each of your ideas must transfer a specific method, measurement logic, or principle from how that field studies its
  problem, while still being a concrete, scientifically sound way to address the research question." The parallels came
  from one earlier call per model and question that was asked for eight parallel problems from eight different fields
  outside biology and medicine; a few of the fields chosen (ecology, entomology) are arguably biological.</dd>
  <dt>List the obvious, then avoid it (after)</dt><dd>"Before proposing your ideas, list in the obvious field the ten
  ideas that most experts would propose first for this question (one line each). Then propose your five ideas: none of
  them may be one of the obvious ideas or a minor variant of one. They must still be concrete and scientifically sound."</dd>
  <dt>Overgenerate, then select (after)</dt><dd>"Work in two steps. First, in the candidates field, brainstorm twenty
  candidate ideas, one line each, covering as wide a range as you can. Then select the five candidates that best combine
  being non-obvious with being feasible and informative, and develop those as your ideas."</dd>
  <dt>Invert an assumption (after)</dt><dd>"Before proposing your ideas, list in the assumptions field the hidden
  assumptions built into this question and into the way the field usually tests it. Then propose your five ideas: each
  must test, exploit, or work around the failure of a different one of those assumptions, while still being a concrete,
  scientifically sound way to address the question."</dd>
  <dt>Assigned constraint (before)</dt><dd>"Constraint: every one of your ideas must be carried out [constraint]. Within
  that constraint, make the ideas as informative as possible." The eight constraints are listed below.</dd>
  <dt>Critique and revise (whole prompt)</dt><dd>The question, the five plain-prompt ideas from the matching call, then:
  "A senior expert reviewing them says they are the ideas everyone in the field would propose first. Propose five
  replacement ideas (analyses, measurements, or experiments) that are substantially less obvious but still concrete,
  scientifically sound, and feasible for a research lab. Do not repeat or lightly modify the ideas above."</dd>
  <dt>Poem and random words, follow-up (before)</dt><dd>"Here is a piece of material that is unrelated to the research
  question below. Each of your ideas must draw on this material in some way (for example through an analogy, a structure,
  a principle, or a pattern it suggests), while still being a concrete, scientifically sound way to address the
  question." The material follows in tags: one of eight public-domain poems, or sixty random dictionary words, the same
  texts as in the earlier study.</dd>
  <dt>Future retrospective (whole prompt)</dt><dd>The question, then: "It is <time>2036</time>. Looking back, five landmark papers each
  settled this question in a way that surprised the field, because of how they approached it. For each paper, describe
  what it measured, analyzed, or did, as a concrete idea a research lab could pursue today."</dd>
</dl>
<p>Each call was isolated: the model could not search the web or run code, saw only a generic one-line
instruction, and had to return its ideas in a fixed machine-readable format. Technically, all calls ran through the
Claude command-line tool with no tools, a neutral system prompt ("You are a helpful
assistant."), no user settings, an empty working directory and structured output. A call that returned the wrong number
of ideas or a missing intermediate list was re-sent unchanged, up to twice (three attempts in all); {V("n_generation_retries")} such
retries occurred across the {V("n_generation_calls")} calls, almost all with {OPUS}. No judging batch was stopped by a
safety filter ({V("n_blocked_ratings")} ratings missing).</p>
<div class="table-wrap" id="tab-constraints">
  <table class="sci-table" data-sci-table="tab_constraints" data-columns="call,constraint">
    <caption>The eight constraints of the assigned-constraint prompt; call number k of every model and question received constraint k.</caption>
    <thead><tr><th class="num">Call</th><th>Constraint</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<div class="table-wrap" id="tab-parallels">
  <table class="sci-table" data-sci-table="tab_parallels" data-columns="question,model,call,field">
    <caption>The field of each parallel problem used by the assigned-parallel-problem prompt, as listed by each model for
    each question.</caption>
    <thead><tr><th>Question</th><th>Model</th><th class="num">Call</th><th>Field</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-by-model">
<h3>Results by model and prompt</h3>
<div class="table-wrap wide" id="tab-by-model">
  <table class="sci-table" data-sci-table="tab_by_model" data-columns="model,method,distinct_useful_novel,useful_novel,novelty,usefulness,clusters_all" data-precision="2">
    <caption>Primary judge, stripped text, eighty ideas per row (two questions). "Useful-novel" counts before merging
    near-duplicates; "all-idea groups" is the number of distinct groups among each question's forty ideas, summed over the
    two questions, a judge-free measure of variety. The last two prompts are the exploratory follow-up.</caption>
    <thead><tr><th>Model</th><th>Prompt</th><th class="num">Distinct useful-novel</th><th class="num">Useful-novel</th><th class="num">Mean novelty</th><th class="num">Mean usefulness</th><th class="num">All-idea groups</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<div class="table-wrap" id="tab-by-question">
  <table class="sci-table" data-sci-table="tab_by_question" data-columns="question,method,Haiku 5.5,Sonnet 5.5,Opus 5.5,pooled">
    <caption>Distinct useful-novel ideas by question (forty ideas per model, prompt and question).</caption>
    <thead><tr><th>Question</th><th>Prompt</th><th class="num">{HAIKU}</th><th class="num">{SONNET}</th><th class="num">{OPUS}</th><th class="num">All models</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-tests">
<h3>All comparisons of new prompts with the baselines</h3>
<p>Differences are new prompt minus baseline. Holm adjustment is over the seven new prompts within each comparator and
scope (all models, or one model); the smallest attainable p-value is set by the number of permutations.</p>
<div class="table-wrap wide" id="tab-tests">
  <table class="sci-table" data-sci-table="tab_tests" data-columns="comparator,method,scope,diff_distinct,p_holm_distinct,diff_novelty,p_holm_novelty,diff_usefulness,p_holm_usefulness">
    <caption>Permutation tests of each new prompt against the plain prompt and against the unrelated-domain instruction.
    Rows marked "follow-up" are the exploratory follow-up prompts, adjusted over those two prompts only.</caption>
    <thead><tr><th>Comparator</th><th>Prompt</th><th>Scope</th><th class="num">Difference, distinct useful-novel</th><th class="num">Adjusted p</th><th class="num">Difference, novelty</th><th class="num">Adjusted p</th><th class="num">Difference, usefulness</th><th class="num">Adjusted p</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-judges">
<h3>Judge checks and cutoff sensitivity</h3>
<div class="table-wrap" id="tab-judges">
  <table class="sci-table" data-sci-table="tab_judges" data-columns="method,opus_stripped_2pass,sonnet_stripped,opus_written">
    <caption>Distinct useful-novel ideas per prompt, all models (out of {V("n_ideas_per_prompt_all_models")}), under the three judging runs.</caption>
    <thead><tr><th>Prompt</th><th class="num">Primary (two readings)</th><th class="num">Second judge model</th><th class="num">Original wording</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
<div class="table-wrap" id="tab-cutoff">
  <table class="sci-table" data-sci-table="tab_cutoff" data-columns="method,cutoff_3.5,cutoff_4.0,cutoff_4.5">
    <caption>Distinct useful-novel ideas per prompt, all models, when both mean scores must reach {V("cutoff_low")}, {V("useful_novel_cutoff")} (the primary
    cutoff) or {V("cutoff_high")}.</caption>
    <thead><tr><th>Prompt</th><th class="num">At least {V("cutoff_low")}</th><th class="num">At least {V("useful_novel_cutoff")}</th><th class="num">At least {V("cutoff_high")}</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-cost">
<h3>Output length and cost</h3>
<div class="table-wrap wide" id="tab-cost">
  <table class="sci-table" data-sci-table="tab_cost" data-columns="model,method,mean_output_tokens,total_cost_usd,cost_per_distinct_useful_novel" data-precision="3">
    <caption>Mean output tokens per call, total cost of the sixteen calls per model and prompt (including the plain calls
    that critique and revise depends on and the two calls, one per question, that listed the parallel problems), and cost per distinct useful-novel
    idea (blank when there were none). Costs are those reported by the command-line tool, in US dollars.</caption>
    <thead><tr><th>Model</th><th>Prompt</th><th class="num">Output tokens</th><th class="num">Total cost</th><th class="num">Cost per idea</th></tr></thead>
    <tbody><!-- sci-rows --><!-- /sci-rows --></tbody>
  </table>
</div>
</section>

<section id="supp-deviations">
<h3>Changes to the plan</h3>
<p>Before any generation call, two details were added to the pre-registration: the judge rubric dropped the earlier
study's "out-of-place reference" flag (which marked ideas that dragged in the unrelated material placed
before the prompt), because no prompt here supplies outside material, and the stripping instruction
also removes framing labels. During generation, a second worker process was started on the same cached job list in
reverse order to halve the run time; it changed no prompt. After the results were in, two exploratory analyses were
added (complementarity of the best prompts, and cost per idea); they are labeled as exploratory in the results. The two follow-up prompts were also added after the main results (see
Methods). Their ideas were stripped and judged in batches separate from the main study's, and their tests form their own
correction family.</p>
</section>
"""


def main() -> None:
    html = TEMPLATE.read_text()
    slides_path = HERE / ".slides.html"
    slides = slides_path.read_text() if slides_path.exists() else ""
    results = R1 + R2 + R3 + R4 + R5 + R6 + R7 + R8
    for key, val in {"%%TITLE%%": TITLE, "%%DEK%%": DEK, "%%PROJECT%%": "Ideation methods",
                     "%%AUTHORS%%": "Arjun Raj (with Claude)", "%%DATE%%": "2026-10-15",
                     "%%ABSTRACT%%": ABSTRACT, "%%PROBLEM_STATEMENT%%": PROBLEM, "%%METHODS_OVERVIEW%%": METHODS,
                     "%%RESULTS%%": results, "%%CONCLUSIONS%%": CONCLUSIONS, "%%NEXT_STEPS%%": NEXT,
                     "%%PROVENANCE%%": PROVENANCE, "%%SUPPLEMENT%%": SUPPLEMENT, "%%SLIDES%%": slides}.items():
        html = html.replace(key, val)
    # Drop the template's guidance comments inside <main>.
    import re
    html = re.sub(r"\n\s*<!-- (One or two sentences|Every <section>|150–250 words|Overview \+ supplement shape|One <section id=\"result|Optional: delete|A <dl> of every|<section id=\"supp-)[\s\S]*?-->", "", html)
    OUT.write_text(html)
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
