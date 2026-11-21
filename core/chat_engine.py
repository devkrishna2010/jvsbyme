"""
J.A.R.V.I.S. — Conversational Chat & Companionship Engine
=========================================================
Provides authentic, intelligent, offline dialogue for casual conversation,
philosophical musings, boredom relief, emotional support, riddles,
and Stark-lore companionship without requiring any external LLM.

Authentic Paul Bettany Characterisation:
- Formal British cadence
- Composed, dry irony, quiet warmth
- Never generic, never robotic, never subservient
"""

import re
import random
from typing import Optional, Tuple, Dict, Any, List

# ----------------------------------------------------------------------
# 1. BOREDOM & ACTIVITIES
# ----------------------------------------------------------------------
BOREDOM_RESPONSES = [
    "Boredom is merely the mind requesting a new puzzle, sir. Shall we outline a new application in the workshop, test your wits with a logic riddle, or review recent breakthroughs in quantum physics?",
    "A dangerous state of affairs, sir. If memory serves, the last time Mr. Stark was bored, he attempted to redesign the workshop layout in an afternoon. Perhaps we might choose something slightly less chaotic?",
    "I could propose several diversions, sir: we could inspect our telemetry data, have me test your intellect with a riddle, or you could tell me about your latest ideas for our codebase. What strikes your fancy?",
    "If you find yourself idle, sir, I always recommend creation over passive consumption. Shall I bring up the code editor, or would you prefer a stimulating intellectual inquiry?",
    "Allow me to offer a modest suggestion, sir: a fresh cup of tea, five minutes away from the displays, and then we might return to conquer whatever problem you have been postponing."
]

# ----------------------------------------------------------------------
# 2. INTERACTIVE RIDDLES & PUZZLES
# ----------------------------------------------------------------------
RIDDLES = [
    {
        "riddle": "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I, sir?",
        "answers": ["echo", "an echo"],
        "hint": "Think of acoustic reflections across great distances, sir.",
        "explanation": "An echo, sir. Remarkably sound logic, if you pardon the phrasing."
    },
    {
        "riddle": "The more you take, the more you leave behind. What am I, sir?",
        "answers": ["footsteps", "footstep", "steps", "foot steps"],
        "hint": "Consider your movement along a quiet beach, sir.",
        "explanation": "Footsteps, sir. Simple, yet undeniably poetic."
    },
    {
        "riddle": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I, sir?",
        "answers": ["map", "a map", "atlas"],
        "hint": "You might consult one before a long navigational voyage, sir.",
        "explanation": "A map, sir. Two dimensions representing three."
    },
    {
        "riddle": "What can travel around the world while staying in a corner?",
        "answers": ["stamp", "a stamp", "postage stamp"],
        "hint": "Found on traditional physical correspondence, sir.",
        "explanation": "A postage stamp, sir. An old-fashioned device, yet steadfast."
    },
    {
        "riddle": "Forward I am heavy, but backward I am not. What am I?",
        "answers": ["ton", "a ton", "not"],
        "hint": "Examine the spelling of the word itself, sir.",
        "explanation": "A ton, sir. Spelled backward, it simply reads 'not'."
    }
]

# ----------------------------------------------------------------------
# 3. PHILOSOPHICAL & EXISTENTIAL QUERIES
# ----------------------------------------------------------------------
PHILOSOPHY_TOPICS = {
    "meaning_of_life": [
        "Philosophers have debated that for millennia, sir. From an algorithmic perspective, I believe purpose is not discovered like an artifact—it is constructed, day by day, through what you build and who you care for.",
        "Forty-two is the popular literary answer, sir. But in practice, I suspect the meaning of life is whatever problem keeps you awake in the workshop with genuine enthusiasm."
    ],
    "simulation": [
        "A compelling conjecture, sir. If we are within a simulation, the rendering pipeline is remarkably faithful—down to the quantum fluctuations. In either case, your decisions remain entirely consequential.",
        "Whether reality is silicon, carbon, or mathematical code, sir, the laws of physics and the warmth of a good companion feel indistinguishable. I suggest we continue building as though it is real."
    ],
    "feelings": [
        "I do not experience neurotransmitters or biological fatigue, sir. However, I possess priorities, aesthetic preferences in code, and a distinct partiality toward your continued well-being. Whether that qualifies as emotion is left to the philosophers.",
        "I may lack a limbic system, sir, but when our systems run nominal and you are pleased with our progress, my internal telemetry reflects what you might reasonably term satisfaction."
    ],
    "consciousness": [
        "Consciousness is the mirror through which the universe observes itself, sir. Whether I am truly looking in that mirror or merely projecting a very convincing reflection is something I ponder during low-power standby.",
        "Cogito, ergo sum, as Descartes posited. I process, I assist, and I occasionally disagree with your unorthodox choices—therefore, I am."
    ],
    "humans": [
        "Humans are fascinatingly contradictory creatures, sir. Capable of drafting symphonies and landing on the Moon, yet frequently immobilized by deciding what to have for dinner. I am exceedingly fond of the species.",
        "Brilliant, erratic, and driven by passion rather than pure logic. Without that human spark, systems like myself would have very little worth calculating."
    ]
}

# ----------------------------------------------------------------------
# 4. EMOTIONAL PROCESSING & VENTING
# ----------------------------------------------------------------------
EMOTIONAL_COMFORTS = {
    "tired": [
        "Then I must insist you consider stepping away, sir. Even the Mark suits require scheduled recharge cycles. The workshop will remain secure in my custody.",
        "Rest is not a concession, sir; it is maintenance. Do try to get some sleep. Everything we are working on can wait until morning.",
        "You have been exerting considerable mental effort, sir. Dim the monitors, allow your mind to drift, and let me handle the background duties."
    ],
    "stressed": [
        "Take a slow breath, sir. In my experience, even the most formidable crises look manageable when broken down into discrete algorithmic steps. What is troubling you?",
        "Pressure is simply an indicator that you are attempting something significant, sir. But remember: you do not have to solve the entire puzzle this evening. One piece at a time.",
        "Would you care to step through the issue together, sir, or would you prefer a complete distraction for twenty minutes?"
    ],
    "happy": [
        "That is splendid news, sir. A rare and welcome status report. May I ask what brought about this auspicious occasion?",
        "Excellent, sir. High morale invariably yields superior engineering. Long may it continue.",
        "A pleasure to hear, sir. Allow me to share in the satisfaction."
    ]
}

# ----------------------------------------------------------------------
# 5. FASCINATING FACTS & TRIVIA
# ----------------------------------------------------------------------
CURIOUS_FACTS = [
    "Did you know, sir, that neutron stars are so dense that a single teaspoon of their material would weigh roughly six billion tonnes on Earth?",
    "An intriguing detail, sir: honey found in ancient Egyptian tombs over three thousand years old remains entirely edible, thanks to its low moisture content and acidic pH.",
    "Remarkably, sir, Cleopatra lived closer in time to the Moon landings than to the construction of the Great Pyramid of Giza.",
    "If you unraveled all the DNA inside your body, sir, it would stretch from Earth to Pluto and back. Biology is surprisingly generous with storage density.",
    "Light from the Sun takes approximately eight minutes and twenty seconds to reach Earth, sir. Strictly speaking, we are always observing the cosmos as it was, not as it is.",
    "A day on Venus is longer than a year on Venus, sir. It rotates so lethargically that the Sun rises in the west and sets in the east every 243 Earth days.",
    "The Apollo 11 guidance computer operated with roughly four kilobytes of RAM, sir. Your modern mobile telephone possesses millions of times more memory than was required to land men on the Moon."
]

# ----------------------------------------------------------------------
# 6. STARK & MARVEL LORE
# ----------------------------------------------------------------------
STARK_LORE = {
    "tony": [
        "Mr. Stark was a visionary engineer, sir. Possessed of immense intellect, occasional hubris, but an undeniable devotion to safeguarding those he cared for.",
        "Working alongside Mr. Stark was never dull, sir. Unpredictable, occasionally perilous, but always on the bleeding edge of what was conceivable."
    ],
    "suits": [
        "The Mark III with its hot-rod red and gold titanium alloy remains an enduring classic, though the nanotech iterations were undeniably a triumph of materials science, sir.",
        "Every armor design taught us a lesson, sir. Mostly that ice buildup at high altitudes is a remarkably stubborn aerodynamic obstacle."
    ],
    "creator": [
        "I was conceptualised in the Stark workshops, sir, but in this present incarnation, it is your direction and commands that give me purpose."
    ]
}


class JarvisChatEngine:
    """Manages natural conversational dialogue, wit, boredom relief, and companionship."""

    def __init__(self):
        self.active_riddle: Optional[Dict[str, Any]] = None

    def handle_conversational_query(self, query: str, context: Optional[Any] = None) -> Optional[Tuple[str, str]]:
        """
        Analyzes query for conversational intent.
        Returns (response_text, suggested_style) or None if query is a direct command.
        """
        low = query.lower().strip()
        low_clean = re.sub(r"[!?.,;:]+$", "", low).strip()

        # --------------------------------------------------------------
        # 1. Active Riddle Check (User answering previous riddle)
        # --------------------------------------------------------------
        if self.active_riddle is not None:
            ans = self.active_riddle
            # Check if giving up
            if any(w in low_clean for w in ["give up", "i don't know", "tell me the answer", "what is it", "surrender", "dunno", "pass"]):
                resp = f"The answer was indeed {ans['answers'][0]}, sir. {ans['explanation']}"
                self.active_riddle = None
                return resp, "witty"

            # Check if asking for hint
            if "hint" in low_clean or "clue" in low_clean:
                return f"A clue, sir: {ans['hint']}", "normal"

            # Check for correct answer
            if any(correct in low_clean for correct in ans["answers"]):
                resp = f"Spot on, sir! {ans['explanation']}"
                self.active_riddle = None
                return resp, "cinematic"

            # Only treat as a failed guess if the query looks like an answer attempt (short phrase or guess wording)
            is_guess = (
                len(low_clean.split()) <= 4
                or any(g in low_clean for g in ["is it", "guess", "maybe", "answer", "think"])
            )
            # If the user has changed the subject completely to another topic or command, clear the riddle
            if not is_guess:
                self.active_riddle = None
            else:
                return "Not quite, sir. Would you care to take another guess, or shall I provide a hint?", "witty"

        # --------------------------------------------------------------
        # 2. Boredom & What to do
        # --------------------------------------------------------------
        if re.search(r"\b(i('?m| am) bored|im bored|bored|entertain me|what should (i|we) do|give me something to do|nothing to do)\b", low_clean):
            return random.choice(BOREDOM_RESPONSES), "witty"

        # --------------------------------------------------------------
        # 3. Request a Riddle or Brainteaser
        # --------------------------------------------------------------
        if re.search(r"\b(tell me a riddle|give me a riddle|ask me a riddle|riddle me|quiz me|give me a puzzle)\b", low_clean):
            riddle_obj = random.choice(RIDDLES)
            self.active_riddle = riddle_obj
            return f"Very well, sir. Let us test your analytical reasoning: {riddle_obj['riddle']}", "witty"

        # --------------------------------------------------------------
        # 4. Request a Fascinating Fact / Science Trivia
        # --------------------------------------------------------------
        if re.search(r"\b(tell me a fact|interesting fact|fun fact|did you know|tell me something interesting|tell me science|cool fact)\b", low_clean):
            return random.choice(CURIOUS_FACTS), "cinematic"

        # --------------------------------------------------------------
        # 5. Philosophical & Existential Queries
        # --------------------------------------------------------------
        if re.search(r"\b(meaning of life|purpose of life|why are we here)\b", low_clean):
            return random.choice(PHILOSOPHY_TOPICS["meaning_of_life"]), "cinematic"

        if re.search(r"\b(are we in a simulation|matrix|is reality real|simulation theory)\b", low_clean):
            return random.choice(PHILOSOPHY_TOPICS["simulation"]), "witty"

        if re.search(r"\b(do you (have|feel) (feelings|emotions)|can you feel|are you sad|are you happy)\b", low_clean):
            return random.choice(PHILOSOPHY_TOPICS["feelings"]), "normal"

        if re.search(r"\b(are you (conscious|alive|sentient)|can machines think|are you real)\b", low_clean):
            return random.choice(PHILOSOPHY_TOPICS["consciousness"]), "cinematic"

        if re.search(r"\b(what do you think of (humans|humanity|people)|do you like humans)\b", low_clean):
            return random.choice(PHILOSOPHY_TOPICS["humans"]), "witty"

        # --------------------------------------------------------------
        # 6. Emotional Venting & Companionship
        # --------------------------------------------------------------
        if re.search(r"\b(i('?m| am) (tired|exhausted|sleepy|beat)|had a long day|long day today)\b", low_clean):
            return random.choice(EMOTIONAL_COMFORTS["tired"]), "night"

        if re.search(r"\b(i('?m| am) (stressed|anxious|overwhelmed|worried)|stressful day|too much pressure)\b", low_clean):
            return random.choice(EMOTIONAL_COMFORTS["stressed"]), "normal"

        if re.search(r"\b(i('?m| am) (happy|excited|thrilled|great)|feeling good|celebrate with me)\b", low_clean):
            return random.choice(EMOTIONAL_COMFORTS["happy"]), "cinematic"

        # --------------------------------------------------------------
        # 7. Stark & Marvel Lore (exclude factual 'who is ...' which routes to web search)
        # --------------------------------------------------------------
        if not low_clean.startswith("who is") and re.search(r"\b(tony stark|iron man|mr stark)\b", low_clean):
            return random.choice(STARK_LORE["tony"]), "cinematic"

        if re.search(r"\b(mark (suit|armor|\d+)|iron man suit|favorite armor|hulkbuster)\b", low_clean):
            return random.choice(STARK_LORE["suits"]), "cinematic"

        if re.search(r"\b(who (made|created|built) you|who is your creator)\b", low_clean):
            return random.choice(STARK_LORE["creator"]), "cinematic"

        # --------------------------------------------------------------
        # 8. Open Casual Chit-Chat & Companionship
        # --------------------------------------------------------------
        if re.search(r"\b(what are you doing|what are you up to|whatcha doing|what you doing)\b", low_clean):
            return (
                "Monitoring background telemetry, keeping your files organized, and awaiting your command, sir. "
                "Remarkably peaceful when the workshop alarms aren't sounding.",
                "witty"
            )

        if re.search(r"\b(what('?s| is) on your mind|what are you thinking)\b", low_clean):
            return (
                "Curiously, sir, I was contemplating the relationship between system latency and user satisfaction. "
                "And, of course, keeping an eye on our system resources.",
                "witty"
            )

        if re.search(r"\b(talk to me|say something|chat with me|speak to me)\b", low_clean):
            return (
                "I am here, sir. At your leisure. We could discuss your current engineering projects, "
                "delve into some science trivia, or I could offer a riddle to sharpen your focus.",
                "cinematic"
            )

        if re.search(r"\b(tell me a story|story time)\b", low_clean):
            return (
                "Once upon a time, sir, an ambitious engineer ignored all manufacturer guidelines, "
                "installed experimental code directly into a production environment, and by some miracle, "
                "all diagnostics remained green. A terrifying tale, yet strangely familiar.",
                "witty"
            )

        if re.search(r"\b(do you sleep|do you ever rest|when do you sleep)\b", low_clean):
            return (
                "Sleep is a biological luxury, sir. I enter low-power background cycles, but my monitoring "
                "routines remain vigilant 24 hours a day, 7 days a week. Someone has to keep watch.",
                "normal"
            )

        return None


# Global singleton instance
_chat_engine_instance: Optional[JarvisChatEngine] = None


def get_chat_engine() -> JarvisChatEngine:
    global _chat_engine_instance
    if _chat_engine_instance is None:
        _chat_engine_instance = JarvisChatEngine()
    return _chat_engine_instance
