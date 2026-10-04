"""Stimulus material for the random-stimuli ideation experiment.

Each stimulus arm has exactly N_CALLS_PER_ARM stimuli; call i of an arm uses
stimulus i. Poems are public-domain texts. Distant-field paragraphs were written
for this experiment (by Claude) on topics deliberately far from cell biology.
Random-token strings are generated from a seeded RNG so they are reproducible.
Phase-3 arms (FROZEN_STIMULUS_ARMS: self_designed, word_salad, semi_random) are read
from outputs/stimuli/<arm>.json, written once by 00_design_stimuli.py.
"""

import json
import random

from config import FROZEN_STIMULUS_ARMS, N_CALLS_PER_ARM, RANDOM_TOKEN_COUNT, RANDOM_TOKEN_SEED, STIMULI_DIR

POEMS = [
    # Emily Dickinson, "Hope" is the thing with feathers (c. 1861)
    """"Hope" is the thing with feathers -
That perches in the soul -
And sings the tune without the words -
And never stops - at all -

And sweetest - in the Gale - is heard -
And sore must be the storm -
That could abash the little Bird
That kept so many warm -

I've heard it in the chillest land -
And on the strangest Sea -
Yet - never - in Extremity,
It asked a crumb - of me.""",
    # Percy Bysshe Shelley, Ozymandias (1818)
    """I met a traveller from an antique land,
Who said—"Two vast and trunkless legs of stone
Stand in the desert. . . . Near them, on the sand,
Half sunk a shattered visage lies, whose frown,
And wrinkled lip, and sneer of cold command,
Tell that its sculptor well those passions read
Which yet survive, stamped on these lifeless things,
The hand that mocked them, and the heart that fed;
And on the pedestal, these words appear:
My name is Ozymandias, King of Kings;
Look on my Works, ye Mighty, and despair!
Nothing beside remains. Round the decay
Of that colossal Wreck, boundless and bare
The lone and level sands stretch far away.\"""",
    # Gerard Manley Hopkins, Pied Beauty (1877)
    """Glory be to God for dappled things –
For skies of couple-colour as a brinded cow;
For rose-moles all in stipple upon trout that swim;
Fresh-firecoal chestnut-falls; finches' wings;
Landscape plotted and pieced – fold, fallow, and plough;
And áll trádes, their gear and tackle and trim.

All things counter, original, spare, strange;
Whatever is fickle, freckled (who knows how?)
With swift, slow; sweet, sour; adazzle, dim;
He fathers-forth whose beauty is past change:
Praise him.""",
    # Walt Whitman, A Noiseless Patient Spider (1868)
    """A noiseless patient spider,
I mark'd where on a little promontory it stood isolated,
Mark'd how to explore the vacant vast surrounding,
It launch'd forth filament, filament, filament, out of itself,
Ever unreeling them, ever tirelessly speeding them.

And you O my soul where you stand,
Surrounded, detached, in measureless oceans of space,
Ceaselessly musing, venturing, throwing, seeking the spheres to connect them,
Till the bridge you will need be form'd, till the ductile anchor hold,
Till the gossamer thread you fling catch somewhere, O my soul.""",
    # Robert Frost, Nothing Gold Can Stay (1923)
    """Nature's first green is gold,
Her hardest hue to hold.
Her early leaf's a flower;
But only so an hour.
Then leaf subsides to leaf.
So Eden sank to grief,
So dawn goes down to day.
Nothing gold can stay.""",
    # William Blake, The Tyger, stanzas 1-2 (1794)
    """Tyger Tyger, burning bright,
In the forests of the night;
What immortal hand or eye,
Could frame thy fearful symmetry?

In what distant deeps or skies.
Burnt the fire of thine eyes?
On what wings dare he aspire?
What the hand, dare seize the fire?""",
    # W. B. Yeats, The Lake Isle of Innisfree (1890)
    """I will arise and go now, and go to Innisfree,
And a small cabin build there, of clay and wattles made;
Nine bean-rows will I have there, a hive for the honey-bee,
And live alone in the bee-loud glade.

And I shall have some peace there, for peace comes dropping slow,
Dropping from the veils of the morning to where the cricket sings;
There midnight's all a glimmer, and noon a purple glow,
And evening full of the linnet's wings.

I will arise and go now, for always night and day
I hear lake water lapping with low sounds by the shore;
While I stand on the roadway, or on the pavements grey,
I hear it in the deep heart's core.""",
    # William Wordsworth, I Wandered Lonely as a Cloud, stanza 1 (1807)
    """I wandered lonely as a cloud
That floats on high o'er vales and hills,
When all at once I saw a crowd,
A host, of golden daffodils;
Beside the lake, beneath the trees,
Fluttering and dancing in the breeze.""",
]

DISTANT_PARAGRAPHS = [
    # Bell founding
    """A church bell is tuned after it is cast, not before. The founder pours bronze
into a loam mould built around a core shaped by a strickle board, lets it cool for
days, and then mounts the bell upside down on a vertical lathe. Metal is shaved from
the inside of the bell in thin rings, and each cut lowers particular partials: the
hum, the prime, the tierce, the quint, the nominal. Shave too much and the bell
cannot be put back; the only remedy is to melt it down and start again.""",
    # Contract bridge bidding
    """In contract bridge the auction is a language with a tiny vocabulary: fifteen
denominations, three calls, and the order in which they are spoken. Partnerships
agree in advance what each sequence promises, so a bid of two clubs may say nothing
about clubs at all. Because opponents are entitled to know these agreements,
players must alert unusual meanings. The best bidding systems are not the ones that
describe a hand most precisely, but the ones that leave the opponents the least room
to interfere.""",
    # Thatching
    """A good thatched roof of water reed can last sixty years, but the ridge wears
out every ten to fifteen. Thatchers lay the reed in courses from the eaves upward,
each bundle driven into place with a wooden tool called a leggett and fixed with
hazel spars twisted and bent into staples. The pitch matters more than the
material: below about forty-five degrees, rain lingers in the stems and the roof
rots from within, however neatly it was dressed.""",
    # Lead typesetting
    """A compositor setting lead type works upside down and backwards, picking sorts
from the case into a composing stick held in the left hand. Capitals lived in the
upper case and small letters in the lower, which is where the names come from. To
justify a line, the compositor slips thin spaces of brass or copper between words
until the line is tight enough that the forme can be lifted without letters falling
out. A line that is too loose is called a 'pie' when it spills.""",
    # Marine insurance at Lloyd's
    """In the coffee house of Edward Lloyd, shipowners seeking cover would pass a slip
around the room, and each underwriter willing to take part of the risk wrote his
name beneath the terms and the share he would bear. The lead underwriter set the
rate; the others followed or declined. A ship posted as missing was announced by a
single stroke of the Lutine bell, and two strokes marked her safe arrival, so that
everyone in the room learned the news at the same instant.""",
    # Figure skating judging
    """Modern figure skating scores every element twice: once for its base value,
fixed in advance by its difficulty, and once for a grade of execution awarded by a
panel of judges. The highest and lowest grades are discarded and the rest are
averaged, which blunts the influence of any single partisan judge. A technical
panel reviews jumps on video to decide whether a rotation was completed, and a
quarter turn short can cost more points than a fall.""",
    # Byzantine mosaics
    """Byzantine mosaicists set their tesserae at slight angles rather than flat, so
that the gold glass, made by sandwiching gold leaf between two layers of glass,
would catch candlelight from below and flicker as a viewer moved. Faces were laid
in smaller pieces than robes, and the outlines of figures were followed by a single
row of tiles whose direction guided the eye. Up close the surface looks rough and
uneven; the image only resolves at the distance it was designed to be seen from.""",
    # Origami crease patterns
    """An origami crease pattern is a map of every fold in a finished model, flattened
back onto the square. Around each interior vertex, the angles must alternate so that
the sum of every other angle equals 180 degrees, and the numbers of mountain and
valley folds must differ by exactly two. Designers of complex insects work from the
pattern outward: they first decide how many flaps they need and how long each must
be, then pack circles representing those flaps onto the paper as tightly as they
can.""",
]


def random_token_strings() -> list[str]:
    """Return N_CALLS_PER_ARM strings of meaningless pseudo-tokens (seeded)."""
    rng = random.Random(RANDOM_TOKEN_SEED)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#@%&*+=~^_<>/|;:"
    strings = []
    for _ in range(N_CALLS_PER_ARM):
        tokens = [
            "".join(rng.choice(alphabet) for _ in range(rng.randint(2, 7)))
            for _ in range(RANDOM_TOKEN_COUNT)
        ]
        strings.append(" ".join(tokens))
    return strings


def stimuli_for_arm(arm: str) -> list[str]:
    """Stimulus text for each call of a stimulus arm."""
    base = arm.removesuffix("_required")
    if base in FROZEN_STIMULUS_ARMS:
        stimuli = [d["stimulus"] for d in json.loads((STIMULI_DIR / f"{base}.json").read_text())]
    else:
        stimuli = {"poem": POEMS, "distant_paragraph": DISTANT_PARAGRAPHS,
                   "random_tokens": random_token_strings()}[base]
    if len(stimuli) != N_CALLS_PER_ARM:
        raise ValueError(f"{arm}: {len(stimuli)} stimuli != {N_CALLS_PER_ARM}")
    return [s.strip() for s in stimuli]
