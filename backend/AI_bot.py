import PyPDF2
import spacy
import re

nlp = spacy.load("en_core_web_sm")

# Extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

# Find the speaker by looking for names or phrases before speech verbs
def find_speaker_before_speech_verb(text, dialogue_pos):
    # Look at more context before the dialogue
    pre_text = text[max(0, dialogue_pos - 300):dialogue_pos].strip()
    
    # Define speech verbs pattern
    speech_verbs_pattern = (
        r'(?:said|replied|asked|whispered|shouted|exclaimed|called|responded|'
        r'continued|muttered|explained|remarked|added|noted|answered|interrupted|'
        r'began|started|murmured|yelled|spoke|declared|announced|stated|mentioned|'
        r'inquired|questioned|wondered|thought)'
    )
    
    # Enhanced patterns for detecting speakers
    name_pattern = r'(?:[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*|(?:the\s+)?(?:man|woman|boy|girl|child|stranger|figure|voice|person))'
    
    # Look for explicit speaker identification in narration with expanded patterns
    narration_patterns = [
        rf'({name_pattern})\s+(?:{speech_verbs_pattern})',  # "Samuel continued"
        rf'({name_pattern})\s*,\s*(?:{speech_verbs_pattern})',  # "Samuel, said"
        rf'(?:said|replied|asked)\s+({name_pattern})',  # "said Samuel"
        rf'(?:the\s+)?({name_pattern})\s+(?:{speech_verbs_pattern})',  # "the stranger said"
        rf'(?:turning\s+to|looking\s+at)\s+({name_pattern})',  # "turning to Samuel"
        rf'({name_pattern})(?:\s*[,\.])?\s+(?:{speech_verbs_pattern})',  # "Samuel. said" or "Samuel, whispered"
    ]

    # Try each pattern
    for pattern in narration_patterns:
        matches = list(re.finditer(pattern, pre_text, re.IGNORECASE))
        if matches:
            speaker = matches[-1].group(1).strip()
            # Clean up the speaker name
            speaker = re.sub(r'^the\s+', '', speaker, flags=re.IGNORECASE)
            # Capitalize first letter of each word
            speaker = ' '.join(word.capitalize() for word in speaker.split())
            return speaker

    # Look for quotes with clear attribution
    quote_attribution = re.finditer(
        rf'"[^"]+"\s*,?\s*({name_pattern})\s+(?:{speech_verbs_pattern})',
        pre_text,
        re.IGNORECASE
    )
    matches = list(quote_attribution)
    if matches:
        speaker = matches[-1].group(1).strip()
        return ' '.join(word.capitalize() for word in speaker.split())

    return "UNKNOWN"

# Resolve pronouns to their referenced speaker
def resolve_pronoun(text, dialogue_pos, last_speaker, nlp):
    # Look at more context before the dialogue
    pre_text = text[max(0, dialogue_pos - 500):dialogue_pos].strip()
    doc = nlp(pre_text)
    
    # Look for character introductions with expanded patterns
    intro_patterns = [
        r"My name is ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)",
        r"I am ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)",
        r"Call me ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)",
        r"known as ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)"
    ]
    
    for pattern in intro_patterns:
        intro_match = re.search(pattern, pre_text)
        if intro_match:
            return intro_match.group(1)

    # Look for the most recent named entity
    named_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if named_entities:
        return named_entities[-1]

    # Look for capitalized names not caught by spaCy
    name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
    names = re.findall(name_pattern, pre_text)
    if names:
        # Filter out common words that might be capitalized
        common_words = {'I', 'The', 'A', 'An', 'But', 'And', 'Or', 'If', 'Then', 'However'}
        valid_names = [name for name in names if name not in common_words]
        if valid_names:
            return valid_names[-1]

    return last_speaker if last_speaker else "UNKNOWN"

# Check if a word is a pronoun
def is_pronoun(word):
    pronouns = {
        'he', 'she', 'they', 'his', 'her', 'their', 'him', 'himself', 'herself', 
        'the stranger', 'the man', 'the woman', 'the boy', 'the girl', 'the person',
        'the figure', 'the voice', 'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'
    }
    return word.lower() in pronouns

# Convert story text to script format with improved speaker detection
def convert_to_script(text):
    script = []
    dialogue_pattern = re.compile(r'"([^"]*)"')
    last_speaker = None
    current_pos = 0
    character_map = {}  # To track character name changes

    # Pre-process to find all character names
    all_speakers = set()
    for match in dialogue_pattern.finditer(text):
        speaker = find_speaker_before_speech_verb(text, match.start())
        if speaker != "UNKNOWN":
            all_speakers.add(speaker)

    # Add narration before dialogue
    for match in dialogue_pattern.finditer(text):
        narration = text[current_pos:match.start()].strip()
        if narration:
            script.append(f"[NARRATION] {narration}")

        dialogue = match.group(1)
        speaker = find_speaker_before_speech_verb(text, match.start())

        # Check for character introductions
        intro_match = re.search(r"(?:My name is|I am|Call me) ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)", dialogue)
        if intro_match:
            new_name = intro_match.group(1)
            if last_speaker:
                character_map[last_speaker] = new_name
                speaker = new_name
                all_speakers.add(new_name)

        # Handle pronoun resolution
        if speaker == "UNKNOWN" or is_pronoun(speaker):
            resolved_speaker = resolve_pronoun(text, match.start(), last_speaker, nlp)
            if resolved_speaker != "UNKNOWN":
                speaker = resolved_speaker

        # Use character mapping if available
        if speaker in character_map:
            speaker = character_map[speaker]

        # Fallback to the last speaker if still unknown and context suggests same speaker
        if speaker == "UNKNOWN":
            # Look for continued dialogue markers
            pre_text = text[max(0, match.start() - 50):match.start()].lower()
            continued_markers = ['continued', 'went on', 'added', 'persisted']
            if any(marker in pre_text for marker in continued_markers) and last_speaker:
                speaker = last_speaker
            elif last_speaker and not any(punct in pre_text[-20:] for punct in '.!?'):
                speaker = last_speaker

        # Update the last speaker only if it's not UNKNOWN
        if speaker != "UNKNOWN":
            last_speaker = speaker
            all_speakers.add(speaker)

        # Add the dialogue with the speaker
        script.append(f"{speaker}: {dialogue}")
        current_pos = match.end()

    # Add any remaining narration
    if current_pos < len(text):
        remaining = text[current_pos:].strip()
        if remaining:
            script.append(f"[NARRATION] {remaining}")

    return "\n".join(script)

def main():
    pdf_path = "test.pdf"
    
    try:
        print("Extracting text from PDF...")
        story_text = extract_text_from_pdf(pdf_path)
        
        print("Converting to script format...")
        script = convert_to_script(story_text)
        
        output_path = "result.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        print(f"Script has been saved to {output_path}")
        
    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()