# NISABA: Conlang Assistant

NISABA takes its name from the Sumerian goddess of language and writing, properly 𒀭𒉀 (U+1202D, U+12240 in unicode).


NISABA: Conlang Assistant is a desktop application built with Python and Tkinter to help language creators (conlangers) design, manage, and test their constructed languages. It provides a unified environment for editing phonologies, dictionaries, grammar rules, fonts, numerals, and translations, with built‑in comparison tools across multiple languages.


It is entirely open source*, and will be improved upon as time goes by.


*It uses the Unlicense, which means anyone can use it, and even make a version that they could sell. Sure, you can do that, but shame on you.

------------------------------------------------------------
Features
------------------------------------------------------------

Import / Export
	- Create new languages, load existing ones, and export/import them as .zip archives for sharing.

Phonology & Spelling
- Manage consonant and vowel inventories with in‑place editing.
- Define syllable structures and spelling rules.
- Type classification is enforced with dropdowns (consonant, vowel, diphthong) to avoid misclassification.

Fonts
- Map symbols to custom glyph images (PNG/SVG).
- Preview glyphs and export mappings to a working .ttf font using the make_font_gpos.py pipeline.
- Supports thumbnails and large previews.

Dictionary
- Store words with fields for English gloss, conlang form, part of speech, gender, definition, pronunciation (IPA), and loanword status.
- Automatic consistency checks against phonology and spelling rules.
- Play IPA pronunciations using audio files stored in the ipa_audio folder.

Grammar
- Sub‑tabs for prefixes, suffixes, nouns, pronouns, possession, verbs, conjugations, and transforms.
- Rich text notes and auto‑generated summaries.
- Conjugations saved both in grammar text and as CSV for use in translation.

Numbers (Numerology)
- Define number words with pronunciation and symbol.
- Built‑in base conversion tool (e.g., decimal → base‑4).

Compare
- Side‑by‑side comparison of two languages across dictionary, phonology, grammar, numbers, and fonts.
- Visual font comparison with glyph thumbnails.

Translation Tool
- Translate English → Conlang and Conlang → English using the dictionary.
- Apply grammar rules (prefixes, suffixes, transforms, conjugations) to modify words.
- Display pronunciation and play it back using IPA audio files.
- Render translations as glyphs using the selected font mapping.

------------------------------------------------------------
How Translation Works
------------------------------------------------------------

Translation is powered by the dictionary and grammar rules:

1. Dictionary Lookup
   - Each English word is looked up in the dictionary (dictionary.csv).
   - If found, its conlang equivalent is retrieved.
   - If not found, the word is bracketed (e.g., [word]) to indicate a missing entry.

2. Grammar Rules
   - Transforms: Phrase‑level regex replacements defined in grammar.txt are applied first (e.g., “I am” → “I+be”).
   - Conjugations: Verb forms are inflected using the conjugation table (conjugations.csv).
   - Prefixes & Suffixes: If a part of speech has defined affixes, they are applied to the conlang word.
   - Word‑level rules: Pronunciations and spelling rules are checked for consistency.

3. Pronunciation
   - The IPA pronunciation is displayed for the translated phrase.
   - Audio playback is supported if matching .mp3 or .wav files exist in Languages/<lang>/ipa_audio/.

4. Glyph Rendering
   - The translated conlang text is rendered on a canvas using the first available font mapping (fonts/<fontname>/mapping.csv).
   - Each symbol is matched to its glyph image and drawn in sequence, producing a visual preview of the conlang script.

------------------------------------------------------------
Project Structure
------------------------------------------------------------

Languages/
  <LanguageName>/
    dictionary.csv
    phonology.csv
    grammar.txt
    conjugations.csv
    numbers.csv
    fonts/
      <FontName>/
        mapping.csv
        glyphs.png/svg
ipa_audio/
  a.mp3, ʃ.mp3, ...

- dictionary.csv – Core lexicon with English → Conlang mappings.
- phonology.csv – Consonant and vowel inventories.
- grammar.txt – Prefixes, suffixes, transforms, and notes.
- conjugations.csv – Verb conjugation table.
- numbers.csv – Numeral system definitions.
- fonts/ – Glyph mappings for custom scripts.
- ipa_audio/ – Audio files for IPA symbols.

------------------------------------------------------------
Getting Started
------------------------------------------------------------

===PYTHON (FOR DEVELOPERS)===

1. Install dependencies:
   pip install pillow fonttools svgpathtools numpy scikit-image pydub playsound

2. Run the app:
   python __main__.py

3. Create a new language in the Import/Export tab and start building your conlang.

===.rar, EXE (FOR USERS)===

1. Extract the rar that contains the .exe, a Languages folder, and the ipa_audio folder.

2. Run the .exe.

------------------------------------------------------------
Walkthrough Example: Translating "I eat"
------------------------------------------------------------

Suppose we want to translate the English phrase:

    I eat

Step 1: Dictionary Lookup
-------------------------
- The dictionary (`dictionary.csv`) contains entries like:
    english: "I"       → conlang: "mi", pos: pronoun, pronunciation: "mi"
    english: "eat"     → conlang: "kala", pos: verb, pronunciation: "kala"
- The program finds both words and retrieves their conlang equivalents.

Step 2: Grammar Rules
---------------------
- The grammar file (`grammar.txt`) may define transforms such as:
    "I am" => "I+be"
- In this case, no transform applies, so we continue.
- Conjugation rules in `conjugations.csv` might specify that the verb "eat"
  in present tense becomes "kalan".
- The program applies this, producing "mi kalan".

Step 3: Prefixes and Suffixes
-----------------------------
- If the grammar specifies that pronouns take a prefix (e.g., "na-"),
  the program would modify "mi" → "nami".
- If verbs take a suffix for present tense (e.g., "-u"),
  "kalan" → "kalanu".
- The resulting phrase might be "nami kalanu".

Step 4: Pronunciation
---------------------
- The IPA pronunciation fields are collected:
    "mi" → [mi]
    "kalanu" → [kalanu]
- The label in the Translation tab shows the combined pronunciation string.
- If audio files exist in `Languages/<lang>/ipa_audio/`, each IPA symbol
  is played in sequence when the user clicks "Play Pronunciation".

Step 5: Glyph Rendering
-----------------------
- The program looks up the font mapping in `fonts/<fontname>/mapping.csv`.
- Each symbol (m, i, k, a, l, a, n, u) is matched to a glyph image.
- The Translation tab’s canvas renders the glyphs in order, producing a
  visual preview of the phrase in the conlang’s custom script.

Final Output
------------
- Textual conlang translation: "nami kalanu"
- Pronunciation: [mi kalanu]
- Audio playback: plays each IPA symbol’s sound file
- Glyph preview: shows the phrase in the conlang’s script



SOURCES:

IPA Sounds Were Shortened from: https://github.com/matthmr/IPA-Sounds