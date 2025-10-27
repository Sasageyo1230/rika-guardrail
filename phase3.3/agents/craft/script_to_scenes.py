"""
Craft Agent - Script to Scenes Pipeline
Advanced script analysis and scene extraction with AI-powered insights

Phase 3.3 Enhancement:
- Intelligent script parsing with context awareness
- Scene breakdown with emotional arc analysis
- Character interaction mapping
- Visual composition suggestions
- Export to Atlas and Notion integration
"""

import re
import json
import logging
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import hashlib

# Natural language processing
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available - advanced text analysis will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Character:
    """Character data structure with analysis"""
    name: str
    aliases: List[str]
    dialogue_count: int = 0
    first_appearance: int = 0
    emotional_range: Dict[str, float] = None
    relationships: Dict[str, float] = None
    
    def __post_init__(self):
        if self.emotional_range is None:
            self.emotional_range = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
        if self.relationships is None:
            self.relationships = {}

@dataclass
class DialogueLine:
    """Individual dialogue line with context"""
    character: str
    text: str
    line_number: int
    emotional_tone: float
    subtext_hints: List[str]
    delivery_notes: Optional[str] = None

@dataclass
class ActionSequence:
    """Action sequence with visual analysis"""
    description: str
    line_number: int
    duration_estimate: float
    visual_complexity: str  # simple, medium, complex
    camera_suggestions: List[str]
    props_required: List[str]
    characters_involved: List[str]

@dataclass
class SceneStructure:
    """Enhanced scene structure with detailed analysis"""
    scene_id: str
    scene_number: int
    title: str
    location: str
    time_of_day: str
    weather: Optional[str]
    mood: str
    purpose: str  # exposition, inciting_incident, rising_action, climax, resolution
    characters_present: List[str]
    dialogue_lines: List[DialogueLine]
    action_sequences: List[ActionSequence]
    emotional_arc: Dict[str, float]
    pacing: str  # slow, medium, fast
    visual_style: str  # intimate, expansive, dynamic, static
    transitions: Dict[str, str]  # in, out
    conflict_level: float  # 0.0 to 1.0
    tension_curve: List[float]
    scene_function: str  # setup, development, payoff
    length_estimate: float  # minutes
    
    def __post_init__(self):
        if not self.scene_id:
            self.scene_id = f"scene_{self.scene_number:03d}"

@dataclass
class ScriptAnalysis:
    """Complete script analysis with metadata"""
    title: str
    genre: str
    structure_type: str  # three_act, five_act, hero_journey
    total_scenes: int
    total_pages_estimate: int
    runtime_estimate: float  # minutes
    character_count: int
    location_count: int
    scenes: List[SceneStructure]
    characters: Dict[str, Character]
    story_beats: List[str]
    emotional_journey: List[float]
    pacing_analysis: Dict[str, Any]
    visual_complexity_breakdown: Dict[str, int]
    dialogue_vs_action_ratio: float
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class AdvancedScriptParser:
    """Advanced script parser with AI-powered analysis"""
    
    def __init__(self):
        self.character_patterns = self._compile_character_patterns()
        self.location_patterns = self._compile_location_patterns()
        self.time_patterns = self._compile_time_patterns()
        self.action_patterns = self._compile_action_patterns()
        
        # Initialize sentiment analyzer if available
        self.sentiment_analyzer = None
        if NLTK_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
            except:
                logger.warning("NLTK sentiment analyzer not available")
    
    def _compile_character_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for character detection"""
        return {
            'character_line': re.compile(r'^([A-Z][A-Z\s]+[A-Z])\s*(\([^)]*\))?\s*:?\s*$'),
            'character_continuation': re.compile(r'^([A-Z][A-Z\s]+[A-Z])\s*\(CONT\'D\)\s*:?\s*$'),
            'character_parenthetical': re.compile(r'^\s*\([^)]+\)\s*$'),
        }
    
    def _compile_location_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for location detection"""
        return {
            'scene_header': re.compile(r'^(INT\.|EXT\.)\s+(.+?)\s*-\s*(.+)$', re.IGNORECASE),
            'transition': re.compile(r'^(FADE IN|FADE OUT|CUT TO|DISSOLVE TO|SMASH CUT|MATCH CUT)[:,.]?\s*(.*)$', re.IGNORECASE),
            'location_change': re.compile(r'^(LATER|MEANWHILE|ELSEWHERE|BACK TO|RETURN TO)[:,.]?\s*(.*)$', re.IGNORECASE),
        }
    
    def _compile_time_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for time detection"""
        return {
            'time_of_day': re.compile(r'\b(DAWN|MORNING|DAY|AFTERNOON|EVENING|DUSK|NIGHT|MIDNIGHT)\b', re.IGNORECASE),
            'time_specific': re.compile(r'\b(\d{1,2}:\d{2}\s*(AM|PM))\b', re.IGNORECASE),
            'time_relative': re.compile(r'\b(LATER|EARLIER|BEFORE|AFTER|MEANWHILE|SIMULTANEOUSLY)\b', re.IGNORECASE),
        }
    
    def _compile_action_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for action detection"""
        return {
            'camera_direction': re.compile(r'\b(CLOSE-UP|WIDE SHOT|MEDIUM SHOT|TRACKING|PAN|TILT|ZOOM|DOLLY)\b', re.IGNORECASE),
            'sound_effect': re.compile(r'\b(SFX|SOUND|MUSIC|SONG)\b', re.IGNORECASE),
            'visual_effect': re.compile(r'\b(VFX|CGI|EXPLOSION|FIRE|SMOKE|LIGHTNING)\b', re.IGNORECASE),
            'movement': re.compile(r'\b(WALKS|RUNS|JUMPS|FALLS|CLIMBS|ENTERS|EXITS|APPROACHES)\b', re.IGNORECASE),
        }

    def parse_full_script(self, script_content: str, title: str = "Untitled") -> ScriptAnalysis:
        """Parse complete script with advanced analysis"""
        lines = script_content.split('\n')
        scenes = []
        characters = {}
        current_scene = None
        line_number = 0
        
        for line in lines:
            line_number += 1
            line = line.strip()
            
            if not line:
                continue
            
            # Check for scene header
            scene_match = self.location_patterns['scene_header'].match(line)
            if scene_match:
                if current_scene:
                    scenes.append(self._finalize_scene(current_scene))
                
                current_scene = self._create_new_scene(scene_match, len(scenes) + 1, line_number)
                continue
            
            # Process content within scene
            if current_scene:
                self._process_scene_line(current_scene, line, line_number, characters)
        
        # Finalize last scene
        if current_scene:
            scenes.append(self._finalize_scene(current_scene))
        
        # Perform overall analysis
        return self._create_script_analysis(title, scenes, characters)

    def _create_new_scene(self, scene_match: re.Match, scene_number: int, line_number: int) -> Dict[str, Any]:
        """Create new scene structure from header match"""
        interior_exterior = scene_match.group(1).upper()
        location = scene_match.group(2).strip()
        time_info = scene_match.group(3).strip()
        
        # Extract weather and mood from time info
        weather = self._extract_weather(time_info)
        mood = self._extract_mood(location, time_info)
        
        return {
            'scene_number': scene_number,
            'line_number': line_number,
            'location': f"{interior_exterior} {location}",
            'time_of_day': time_info,
            'weather': weather,
            'mood': mood,
            'characters_present': set(),
            'dialogue_lines': [],
            'action_sequences': [],
            'tension_points': [],
            'raw_lines': []
        }

    def _process_scene_line(self, scene: Dict[str, Any], line: str, line_number: int, characters: Dict[str, Character]):
        """Process individual line within scene context"""
        scene['raw_lines'].append((line_number, line))
        
        # Check for character dialogue
        char_match = self.character_patterns['character_line'].match(line)
        if char_match:
            character_name = char_match.group(1).strip()
            scene['current_speaker'] = character_name
            scene['characters_present'].add(character_name)
            
            # Track character
            if character_name not in characters:
                characters[character_name] = Character(
                    name=character_name,
                    aliases=[],
                    first_appearance=scene['scene_number']
                )
            return
        
        # Check for dialogue text
        if 'current_speaker' in scene and not self.character_patterns['character_parenthetical'].match(line):
            if not any(pattern.match(line) for pattern in [
                self.location_patterns['scene_header'],
                self.location_patterns['transition']
            ]):
                # This is dialogue
                dialogue_line = self._create_dialogue_line(
                    scene['current_speaker'], line, line_number
                )
                scene['dialogue_lines'].append(dialogue_line)
                characters[scene['current_speaker']].dialogue_count += 1
                return
        
        # Must be action line
        if not self._is_scene_direction(line):
            action_seq = self._create_action_sequence(line, line_number, scene['characters_present'])
            scene['action_sequences'].append(action_seq)
            
            # Update characters present based on action
            involved_chars = self._extract_characters_from_action(line, characters.keys())
            scene['characters_present'].update(involved_chars)

    def _create_dialogue_line(self, character: str, text: str, line_number: int) -> DialogueLine:
        """Create structured dialogue line with analysis"""
        emotional_tone = 0.0
        subtext_hints = []
        
        # Sentiment analysis if available
        if self.sentiment_analyzer and text:
            sentiment = self.sentiment_analyzer.polarity_scores(text)
            emotional_tone = sentiment['compound']
        
        # Extract subtext hints from punctuation and word choice
        if '...' in text:
            subtext_hints.append('hesitation')
        if text.count('!') > 1:
            subtext_hints.append('excitement')
        if text.isupper():
            subtext_hints.append('shouting')
        if text.count('?') > text.count('.'):
            subtext_hints.append('questioning')
        
        return DialogueLine(
            character=character,
            text=text,
            line_number=line_number,
            emotional_tone=emotional_tone,
            subtext_hints=subtext_hints
        )

    def _create_action_sequence(self, description: str, line_number: int, characters_present: Set[str]) -> ActionSequence:
        """Create structured action sequence with visual analysis"""
        # Estimate duration based on action complexity
        word_count = len(description.split())
        duration_estimate = max(2.0, word_count * 0.5)  # Minimum 2 seconds
        
        # Analyze visual complexity
        visual_complexity = self._analyze_visual_complexity(description)
        
        # Generate camera suggestions
        camera_suggestions = self._suggest_camera_work(description)
        
        # Extract props and characters
        props_required = self._extract_props(description)
        characters_involved = self._extract_characters_from_action(description, characters_present)
        
        return ActionSequence(
            description=description,
            line_number=line_number,
            duration_estimate=duration_estimate,
            visual_complexity=visual_complexity,
            camera_suggestions=camera_suggestions,
            props_required=props_required,
            characters_involved=list(characters_involved)
        )

    def _analyze_visual_complexity(self, description: str) -> str:
        """Analyze visual complexity of action"""
        complexity_indicators = {
            'simple': ['sits', 'stands', 'looks', 'pauses', 'waits'],
            'medium': ['walks', 'opens', 'closes', 'picks up', 'puts down', 'turns'],
            'complex': ['runs', 'fights', 'jumps', 'climbs', 'explosion', 'crash', 'chase']
        }
        
        description_lower = description.lower()
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return complexity
        
        return 'simple'

    def _suggest_camera_work(self, description: str) -> List[str]:
        """Suggest camera movements and shots based on action"""
        suggestions = []
        desc_lower = description.lower()
        
        # Movement suggestions
        if any(word in desc_lower for word in ['walks', 'runs', 'moves']):
            suggestions.append('tracking_shot')
        if any(word in desc_lower for word in ['face', 'eyes', 'expression']):
            suggestions.append('close_up')
        if any(word in desc_lower for word in ['room', 'building', 'landscape']):
            suggestions.append('wide_shot')
        if any(word in desc_lower for word in ['above', 'below', 'height']):
            suggestions.append('angle_shot')
        
        # Default to medium shot if no specific indicators
        if not suggestions:
            suggestions.append('medium_shot')
        
        return suggestions

    def _extract_props(self, description: str) -> List[str]:
        """Extract prop requirements from action description"""
        # Common prop patterns
        prop_patterns = [
            r'\b(gun|weapon|sword|knife)\b',
            r'\b(car|vehicle|truck|motorcycle)\b',
            r'\b(phone|computer|laptop|tablet)\b',
            r'\b(book|document|paper|letter)\b',
            r'\b(cup|glass|bottle|drink)\b',
            r'\b(bag|suitcase|backpack)\b',
        ]
        
        props = []
        for pattern in prop_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            props.extend(matches)
        
        return list(set(props))  # Remove duplicates

    def _extract_characters_from_action(self, description: str, known_characters: Set[str]) -> Set[str]:
        """Extract character names from action description"""
        involved = set()
        
        # Check for known character names
        for character in known_characters:
            if character.lower() in description.lower():
                involved.add(character)
        
        # Check for pronouns that might indicate character presence
        pronouns = ['he', 'she', 'they', 'him', 'her', 'them']
        if any(pronoun in description.lower().split() for pronoun in pronouns):
            # Someone is involved but we need context to determine who
            pass
        
        return involved

    def _extract_weather(self, time_info: str) -> Optional[str]:
        """Extract weather information from time description"""
        weather_patterns = {
            'rain': ['rain', 'raining', 'storm', 'stormy'],
            'snow': ['snow', 'snowing', 'blizzard'],
            'fog': ['fog', 'foggy', 'mist', 'misty'],
            'wind': ['wind', 'windy', 'breezy'],
            'sun': ['sunny', 'bright', 'clear']
        }
        
        time_lower = time_info.lower()
        for weather, indicators in weather_patterns.items():
            if any(indicator in time_lower for indicator in indicators):
                return weather
        
        return None

    def _extract_mood(self, location: str, time_info: str) -> str:
        """Extract mood from location and time context"""
        combined = f"{location} {time_info}".lower()
        
        mood_indicators = {
            'tense': ['alley', 'basement', 'abandoned', 'dark', 'night'],
            'peaceful': ['park', 'garden', 'home', 'morning', 'bright'],
            'mysterious': ['fog', 'shadow', 'unknown', 'hidden'],
            'energetic': ['club', 'party', 'busy', 'crowded'],
            'intimate': ['bedroom', 'quiet', 'private', 'close']
        }
        
        for mood, indicators in mood_indicators.items():
            if any(indicator in combined for indicator in indicators):
                return mood
        
        return 'neutral'

    def _is_scene_direction(self, line: str) -> bool:
        """Check if line is scene direction rather than action"""
        direction_patterns = [
            r'^(FADE|CUT|DISSOLVE|SMASH CUT)',
            r'^(LATER|MEANWHILE|BACK TO)',
            r'^(THE END|ROLL CREDITS)'
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in direction_patterns)

    def _finalize_scene(self, scene_data: Dict[str, Any]) -> SceneStructure:
        """Convert raw scene data to structured scene"""
        # Analyze emotional arc
        emotional_arc = self._analyze_scene_emotion(scene_data['dialogue_lines'])
        
        # Determine pacing
        pacing = self._determine_pacing(scene_data)
        
        # Determine visual style
        visual_style = self._determine_visual_style(scene_data)
        
        # Calculate conflict level
        conflict_level = self._calculate_conflict_level(scene_data)
        
        # Generate tension curve
        tension_curve = self._generate_tension_curve(scene_data)
        
        # Determine scene function
        scene_function = self._determine_scene_function(scene_data)
        
        # Estimate length
        length_estimate = self._estimate_scene_length(scene_data)
        
        return SceneStructure(
            scene_id=f"scene_{scene_data['scene_number']:03d}",
            scene_number=scene_data['scene_number'],
            title=f"Scene {scene_data['scene_number']}",
            location=scene_data['location'],
            time_of_day=scene_data['time_of_day'],
            weather=scene_data['weather'],
            mood=scene_data['mood'],
            purpose='development',  # Will be refined in full analysis
            characters_present=list(scene_data['characters_present']),
            dialogue_lines=scene_data['dialogue_lines'],
            action_sequences=scene_data['action_sequences'],
            emotional_arc=emotional_arc,
            pacing=pacing,
            visual_style=visual_style,
            transitions={'in': 'cut', 'out': 'cut'},
            conflict_level=conflict_level,
            tension_curve=tension_curve,
            scene_function=scene_function,
            length_estimate=length_estimate
        )

    def _analyze_scene_emotion(self, dialogue_lines: List[DialogueLine]) -> Dict[str, float]:
        """Analyze emotional content of scene"""
        if not dialogue_lines:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        emotions = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
        
        for line in dialogue_lines:
            if line.emotional_tone > 0.1:
                emotions['positive'] += line.emotional_tone
            elif line.emotional_tone < -0.1:
                emotions['negative'] += abs(line.emotional_tone)
            else:
                emotions['neutral'] += 0.5
        
        # Normalize
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v / total for k, v in emotions.items()}
        
        return emotions

    def _determine_pacing(self, scene_data: Dict[str, Any]) -> str:
        """Determine scene pacing based on dialogue/action ratio"""
        dialogue_count = len(scene_data['dialogue_lines'])
        action_count = len(scene_data['action_sequences'])
        total_lines = len(scene_data['raw_lines'])
        
        if dialogue_count > action_count * 2:
            return 'slow'  # Dialogue heavy
        elif action_count > dialogue_count * 2:
            return 'fast'  # Action heavy
        else:
            return 'medium'

    def _determine_visual_style(self, scene_data: Dict[str, Any]) -> str:
        """Determine visual style based on location and action"""
        location_lower = scene_data['location'].lower()
        
        if any(word in location_lower for word in ['close', 'intimate', 'small', 'tight']):
            return 'intimate'
        elif any(word in location_lower for word in ['wide', 'open', 'large', 'vast']):
            return 'expansive'
        elif len(scene_data['action_sequences']) > len(scene_data['dialogue_lines']):
            return 'dynamic'
        else:
            return 'static'

    def _calculate_conflict_level(self, scene_data: Dict[str, Any]) -> float:
        """Calculate conflict level based on dialogue emotion and action"""
        conflict_score = 0.0
        
        # Emotional conflict from dialogue
        for line in scene_data['dialogue_lines']:
            conflict_score += abs(line.emotional_tone) * 0.1
        
        # Action-based conflict
        for action in scene_data['action_sequences']:
            if action.visual_complexity == 'complex':
                conflict_score += 0.3
            elif action.visual_complexity == 'medium':
                conflict_score += 0.1
        
        return min(1.0, conflict_score)

    def _generate_tension_curve(self, scene_data: Dict[str, Any]) -> List[float]:
        """Generate tension curve across scene"""
        total_elements = len(scene_data['dialogue_lines']) + len(scene_data['action_sequences'])
        if total_elements == 0:
            return [0.0]
        
        # Simple tension curve - starts low, peaks in middle, resolves
        curve_length = min(10, total_elements)
        tension_curve = []
        
        for i in range(curve_length):
            # Parabolic curve peaking at 60% through scene
            x = i / (curve_length - 1) if curve_length > 1 else 0
            peak_position = 0.6
            if x <= peak_position:
                tension = x / peak_position
            else:
                tension = 1.0 - ((x - peak_position) / (1.0 - peak_position)) * 0.5
            
            tension_curve.append(tension)
        
        return tension_curve

    def _determine_scene_function(self, scene_data: Dict[str, Any]) -> str:
        """Determine the narrative function of the scene"""
        scene_number = scene_data['scene_number']
        
        # Simple heuristic based on position
        if scene_number <= 2:
            return 'setup'
        elif scene_number >= 20:  # Assuming ~25 scene script
            return 'payoff'
        else:
            return 'development'

    def _estimate_scene_length(self, scene_data: Dict[str, Any]) -> float:
        """Estimate scene length in minutes"""
        # Base time from dialogue (average speaking pace: 150 words/minute)
        dialogue_time = 0.0
        for line in scene_data['dialogue_lines']:
            word_count = len(line.text.split())
            dialogue_time += word_count / 150.0  # minutes
        
        # Add time from action sequences
        action_time = sum(action.duration_estimate for action in scene_data['action_sequences']) / 60.0  # convert to minutes
        
        return dialogue_time + action_time

    def _create_script_analysis(self, title: str, scenes: List[SceneStructure], characters: Dict[str, Character]) -> ScriptAnalysis:
        """Create complete script analysis"""
        # Calculate overall statistics
        total_scenes = len(scenes)
        runtime_estimate = sum(scene.length_estimate for scene in scenes)
        total_pages_estimate = max(1, int(runtime_estimate * 1.2))  # Rough page estimate
        
        # Analyze story structure
        story_beats = self._identify_story_beats(scenes)
        emotional_journey = self._calculate_emotional_journey(scenes)
        pacing_analysis = self._analyze_overall_pacing(scenes)
        
        # Visual complexity breakdown
        visual_complexity_breakdown = defaultdict(int)
        for scene in scenes:
            for action in scene.action_sequences:
                visual_complexity_breakdown[action.visual_complexity] += 1
        
        # Calculate dialogue vs action ratio
        total_dialogue = sum(len(scene.dialogue_lines) for scene in scenes)
        total_action = sum(len(scene.action_sequences) for scene in scenes)
        dialogue_vs_action_ratio = total_dialogue / max(1, total_action)
        
        return ScriptAnalysis(
            title=title,
            genre=self._infer_genre(scenes, characters),
            structure_type="three_act",  # Default assumption
            total_scenes=total_scenes,
            total_pages_estimate=total_pages_estimate,
            runtime_estimate=runtime_estimate,
            character_count=len(characters),
            location_count=len(set(scene.location for scene in scenes)),
            scenes=scenes,
            characters=characters,
            story_beats=story_beats,
            emotional_journey=emotional_journey,
            pacing_analysis=pacing_analysis,
            visual_complexity_breakdown=dict(visual_complexity_breakdown),
            dialogue_vs_action_ratio=dialogue_vs_action_ratio
        )

    def _identify_story_beats(self, scenes: List[SceneStructure]) -> List[str]:
        """Identify major story beats"""
        beats = []
        total_scenes = len(scenes)
        
        if total_scenes > 0:
            beats.append(f"Opening - Scene {scenes[0].scene_number}")
        
        if total_scenes > 5:
            beats.append(f"Inciting Incident - Scene {scenes[total_scenes//4].scene_number}")
        
        if total_scenes > 10:
            beats.append(f"Midpoint - Scene {scenes[total_scenes//2].scene_number}")
        
        if total_scenes > 15:
            beats.append(f"Climax - Scene {scenes[total_scenes*3//4].scene_number}")
        
        if total_scenes > 1:
            beats.append(f"Resolution - Scene {scenes[-1].scene_number}")
        
        return beats

    def _calculate_emotional_journey(self, scenes: List[SceneStructure]) -> List[float]:
        """Calculate overall emotional journey across script"""
        journey = []
        
        for scene in scenes:
            # Combine positive and negative emotions for overall intensity
            positive = scene.emotional_arc.get('positive', 0.0)
            negative = scene.emotional_arc.get('negative', 0.0)
            emotional_intensity = positive + negative
            journey.append(emotional_intensity)
        
        return journey

    def _analyze_overall_pacing(self, scenes: List[SceneStructure]) -> Dict[str, Any]:
        """Analyze overall script pacing"""
        pacing_counts = defaultdict(int)
        scene_lengths = []
        
        for scene in scenes:
            pacing_counts[scene.pacing] += 1
            scene_lengths.append(scene.length_estimate)
        
        avg_scene_length = sum(scene_lengths) / len(scene_lengths) if scene_lengths else 0
        
        return {
            'pacing_distribution': dict(pacing_counts),
            'average_scene_length': avg_scene_length,
            'longest_scene': max(scene_lengths) if scene_lengths else 0,
            'shortest_scene': min(scene_lengths) if scene_lengths else 0,
            'pacing_variety': len(pacing_counts) / 3  # out of 3 possible pacing types
        }

    def _infer_genre(self, scenes: List[SceneStructure], characters: Dict[str, Character]) -> str:
        """Infer script genre from content analysis"""
        genre_indicators = defaultdict(int)
        
        for scene in scenes:
            # Location-based indicators
            if any(word in scene.location.lower() for word in ['police', 'crime', 'investigation']):
                genre_indicators['crime'] += 1
            if any(word in scene.location.lower() for word in ['space', 'future', 'lab', 'technology']):
                genre_indicators['sci-fi'] += 1
            if any(word in scene.location.lower() for word in ['castle', 'medieval', 'magic', 'forest']):
                genre_indicators['fantasy'] += 1
            
            # Action-based indicators
            for action in scene.action_sequences:
                if any(word in action.description.lower() for word in ['fight', 'explosion', 'chase', 'gun']):
                    genre_indicators['action'] += 1
                if any(word in action.description.lower() for word in ['laugh', 'smile', 'joke', 'funny']):
                    genre_indicators['comedy'] += 1
        
        # Return most likely genre
        if genre_indicators:
            return max(genre_indicators.items(), key=lambda x: x[1])[0]
        else:
            return 'drama'

class ScriptToScenesExporter:
    """Export script analysis to various formats"""
    
    def __init__(self):
        pass

    def export_to_json(self, analysis: ScriptAnalysis, output_path: str):
        """Export analysis to JSON"""
        # Convert dataclasses to dict
        data = asdict(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported script analysis to JSON: {output_path}")

    def export_to_atlas_format(self, analysis: ScriptAnalysis, output_path: str):
        """Export in format suitable for Atlas integration"""
        atlas_data = {
            'project_id': analysis.title.lower().replace(' ', '_'),
            'title': analysis.title,
            'metadata': {
                'genre': analysis.genre,
                'total_scenes': analysis.total_scenes,
                'runtime_estimate': analysis.runtime_estimate,
                'character_count': analysis.character_count,
                'created_at': analysis.created_at
            },
            'scenes': [],
            'characters': {},
            'analysis': {
                'story_beats': analysis.story_beats,
                'emotional_journey': analysis.emotional_journey,
                'pacing_analysis': analysis.pacing_analysis
            }
        }
        
        # Convert scenes for Atlas
        for scene in analysis.scenes:
            atlas_scene = {
                'id': scene.scene_id,
                'number': scene.scene_number,
                'title': scene.title,
                'location': scene.location,
                'time': scene.time_of_day,
                'mood': scene.mood,
                'characters': scene.characters_present,
                'length_estimate': scene.length_estimate,
                'conflict_level': scene.conflict_level,
                'visual_style': scene.visual_style,
                'dialogue_count': len(scene.dialogue_lines),
                'action_count': len(scene.action_sequences)
            }
            atlas_data['scenes'].append(atlas_scene)
        
        # Convert characters for Atlas
        for char_name, character in analysis.characters.items():
            atlas_data['characters'][char_name] = {
                'name': character.name,
                'dialogue_count': character.dialogue_count,
                'first_appearance': character.first_appearance,
                'emotional_range': character.emotional_range
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(atlas_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported Atlas format to: {output_path}")

    def generate_notion_export(self, analysis: ScriptAnalysis) -> Dict[str, Any]:
        """Generate data structure for Notion export"""
        # Notion database structure
        notion_data = {
            'database_properties': {
                'Scene': {'title': {}},
                'Location': {'rich_text': {}},
                'Time': {'select': {'options': []}},
                'Characters': {'multi_select': {'options': []}},
                'Mood': {'select': {'options': []}},
                'Pacing': {'select': {'options': []}},
                'Length': {'number': {}},
                'Conflict Level': {'number': {}},
                'Notes': {'rich_text': {}}
            },
            'pages': []
        }
        
        # Generate unique options for select fields
        times = set()
        characters = set()
        moods = set()
        pacings = set()
        
        for scene in analysis.scenes:
            times.add(scene.time_of_day)
            characters.update(scene.characters_present)
            moods.add(scene.mood)
            pacings.add(scene.pacing)
        
        # Add options to database properties
        notion_data['database_properties']['Time']['select']['options'] = [{'name': t} for t in times]
        notion_data['database_properties']['Characters']['multi_select']['options'] = [{'name': c} for c in characters]
        notion_data['database_properties']['Mood']['select']['options'] = [{'name': m} for m in moods]
        notion_data['database_properties']['Pacing']['select']['options'] = [{'name': p} for p in pacings]
        
        # Create pages for each scene
        for scene in analysis.scenes:
            page = {
                'properties': {
                    'Scene': {'title': [{'text': {'content': scene.title}}]},
                    'Location': {'rich_text': [{'text': {'content': scene.location}}]},
                    'Time': {'select': {'name': scene.time_of_day}},
                    'Characters': {'multi_select': [{'name': char} for char in scene.characters_present]},
                    'Mood': {'select': {'name': scene.mood}},
                    'Pacing': {'select': {'name': scene.pacing}},
                    'Length': {'number': round(scene.length_estimate, 2)},
                    'Conflict Level': {'number': round(scene.conflict_level, 2)},
                    'Notes': {'rich_text': [{'text': {'content': f"Visual style: {scene.visual_style}"}}]}
                },
                'children': []  # Could add dialogue/action as blocks
            }
            notion_data['pages'].append(page)
        
        return notion_data

def main():
    """Example usage of the Script to Scenes pipeline"""
    # Initialize parser
    parser = AdvancedScriptParser()
    
    # Example script
    example_script = """
    FADE IN:
    
    EXT. CITY STREET - NIGHT
    
    Rain pounds the empty asphalt. Neon signs reflect in puddles.
    
    DETECTIVE SARAH CHEN (35) hurries down the sidewalk, her coat collar turned up against the storm.
    
    SARAH:
    (into phone)
    I'm almost there. What do we know?
    
    VOICE (V.O.):
    Victim's name is Marcus Webb. Tech entrepreneur. 
    
    SARAH:
    Any witnesses?
    
    VOICE (V.O.):
    That's the thing... there are too many.
    
    Sarah stops walking, processing this information.
    
    SARAH:
    What do you mean?
    
    CUT TO:
    
    INT. CRIME SCENE - CONTINUOUS
    
    A high-tech office space. Police officers and forensics team work methodically.
    
    DETECTIVE MIKE TORRES (40s) approaches Sarah as she enters.
    
    TORRES:
    Every camera in a six-block radius caught something different.
    
    He hands her a tablet showing surveillance footage.
    
    TORRES: (CONT'D)
    Same time, same victim, but the perpetrator... changes.
    
    Sarah studies the screen, her expression growing more troubled.
    
    SARAH:
    This isn't possible.
    
    TORRES:
    That's what I thought too.
    
    FADE OUT.
    """
    
    # Parse the script
    analysis = parser.parse_full_script(example_script, "The Impossible Witness")
    
    # Create exporter
    exporter = ScriptToScenesExporter()
    
    # Create output directory
    output_dir = "output/script_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # Export to JSON
    json_path = os.path.join(output_dir, "analysis.json")
    exporter.export_to_json(analysis, json_path)
    
    # Export to Atlas format
    atlas_path = os.path.join(output_dir, "atlas_export.json")
    exporter.export_to_atlas_format(analysis, atlas_path)
    
    # Generate Notion export data
    notion_data = exporter.generate_notion_export(analysis)
    notion_path = os.path.join(output_dir, "notion_export.json")
    with open(notion_path, 'w', encoding='utf-8') as f:
        json.dump(notion_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nScript Analysis Complete!")
    print(f"Title: {analysis.title}")
    print(f"Genre: {analysis.genre}")
    print(f"Total Scenes: {analysis.total_scenes}")
    print(f"Runtime Estimate: {analysis.runtime_estimate:.1f} minutes")
    print(f"Characters: {analysis.character_count}")
    print(f"Story Beats: {len(analysis.story_beats)}")
    
    logger.info("Script to scenes analysis completed!")

if __name__ == "__main__":
    main()