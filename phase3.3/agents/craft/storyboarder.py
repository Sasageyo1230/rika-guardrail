"""
Craft Agent - Storyboard Generator
Advanced storyboard creation with image panels and visual narrative tools

Phase 3.3 Enhancement:
- Automated storyboard panel generation
- Script analysis and scene breakdown
- Visual composition templates
- Export to Notion, PDF, and web formats
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import base64
from io import BytesIO

# PIL for image processing
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - image generation will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StoryboardPanel:
    """Individual storyboard panel data structure"""
    panel_id: str
    scene_number: int
    shot_type: str  # wide, medium, close-up, extreme-close-up, establishing
    camera_angle: str  # eye-level, high, low, dutch, overhead
    action_description: str
    dialogue: Optional[str] = None
    notes: Optional[str] = None
    duration: Optional[float] = None  # seconds
    transition: Optional[str] = None  # cut, fade, dissolve, wipe
    composition_notes: Optional[str] = None
    lighting_notes: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class Storyboard:
    """Complete storyboard data structure"""
    project_name: str
    title: str
    description: str
    panels: List[StoryboardPanel]
    metadata: Dict[str, Any]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class StoryboardVisualizer:
    """Generate visual storyboard panels with composition templates"""
    
    def __init__(self, panel_width: int = 800, panel_height: int = 450):
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.aspect_ratio = panel_width / panel_height
        
        # Load default font if available
        self.font_path = self._find_system_font()
        
    def _find_system_font(self) -> Optional[str]:
        """Find available system font for text rendering"""
        common_fonts = [
            "arial.ttf", "Arial.ttf",
            "calibri.ttf", "Calibri.ttf", 
            "tahoma.ttf", "Tahoma.ttf",
            "segoeui.ttf", "SegoeUI.ttf"
        ]
        
        for font_name in common_fonts:
            font_path = os.path.join("C:/Windows/Fonts", font_name)
            if os.path.exists(font_path):
                return font_path
        return None

    def create_panel_template(self, panel: StoryboardPanel) -> Image.Image:
        """Create a visual template for a storyboard panel"""
        if not PIL_AVAILABLE:
            logger.error("PIL not available - cannot generate panel images")
            return None
            
        # Create base image
        img = Image.new('RGB', (self.panel_width, self.panel_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype(self.font_path, 24) if self.font_path else ImageFont.load_default()
            text_font = ImageFont.truetype(self.font_path, 16) if self.font_path else ImageFont.load_default()
            small_font = ImageFont.truetype(self.font_path, 12) if self.font_path else ImageFont.load_default()
        except:
            title_font = text_font = small_font = ImageFont.load_default()
        
        # Draw panel border
        border_color = '#333333'
        draw.rectangle([5, 5, self.panel_width-5, self.panel_height-5], outline=border_color, width=3)
        
        # Draw composition guidelines based on shot type
        self._draw_composition_guides(draw, panel.shot_type, panel.camera_angle)
        
        # Add panel header
        header_height = 60
        draw.rectangle([10, 10, self.panel_width-10, header_height], fill='#f0f0f0', outline=border_color)
        
        # Panel number and shot info
        header_text = f"Panel {panel.panel_id} | Scene {panel.scene_number} | {panel.shot_type.upper()}"
        draw.text((20, 25), header_text, fill='black', font=title_font)
        
        # Action description area
        action_area_top = header_height + 20
        action_area_height = self.panel_height - header_height - 120
        
        # Draw main composition area
        draw.rectangle([20, action_area_top, self.panel_width-20, action_area_top + action_area_height], 
                      outline='#cccccc', width=2)
        
        # Add action description
        action_text = self._wrap_text(panel.action_description, self.panel_width - 60, text_font)
        text_y = action_area_top + 20
        for line in action_text:
            draw.text((30, text_y), line, fill='#333333', font=text_font)
            text_y += 25
        
        # Add dialogue if present
        if panel.dialogue:
            dialogue_area_top = action_area_top + action_area_height + 10
            draw.rectangle([20, dialogue_area_top, self.panel_width-20, self.panel_height-20], 
                          fill='#ffffcc', outline='#cccccc')
            
            dialogue_text = f'"{panel.dialogue}"'
            wrapped_dialogue = self._wrap_text(dialogue_text, self.panel_width - 60, text_font)
            dialogue_y = dialogue_area_top + 10
            for line in wrapped_dialogue:
                draw.text((30, dialogue_y), line, fill='#333333', font=text_font)
                dialogue_y += 20
        
        # Add metadata in corners
        # Duration
        if panel.duration:
            duration_text = f"{panel.duration}s"
            draw.text((self.panel_width - 80, 15), duration_text, fill='#666666', font=small_font)
        
        # Camera angle
        angle_text = f"Angle: {panel.camera_angle}"
        draw.text((self.panel_width - 150, self.panel_height - 25), angle_text, fill='#666666', font=small_font)
        
        return img

    def _draw_composition_guides(self, draw: ImageDraw.Draw, shot_type: str, camera_angle: str):
        """Draw composition guidelines based on shot type and angle"""
        guide_color = '#dddddd'
        
        # Rule of thirds lines
        third_x1 = self.panel_width // 3
        third_x2 = (self.panel_width * 2) // 3
        third_y1 = self.panel_height // 3
        third_y2 = (self.panel_height * 2) // 3
        
        # Draw rule of thirds grid
        draw.line([(third_x1, 70), (third_x1, self.panel_height - 50)], fill=guide_color, width=1)
        draw.line([(third_x2, 70), (third_x2, self.panel_height - 50)], fill=guide_color, width=1)
        draw.line([(20, third_y1), (self.panel_width - 20, third_y1)], fill=guide_color, width=1)
        draw.line([(20, third_y2), (self.panel_width - 20, third_y2)], fill=guide_color, width=1)
        
        # Shot-specific composition guides
        center_x = self.panel_width // 2
        center_y = self.panel_height // 2
        
        if shot_type == "close-up":
            # Face/head area guide
            face_width = 200
            face_height = 250
            draw.ellipse([center_x - face_width//2, center_y - face_height//2 - 50, 
                         center_x + face_width//2, center_y + face_height//2 - 50], 
                        outline='#ffcccc', width=2)
                        
        elif shot_type == "wide" or shot_type == "establishing":
            # Horizon line
            horizon_y = center_y + 50
            draw.line([(20, horizon_y), (self.panel_width - 20, horizon_y)], fill='#ccffcc', width=2)
            
        elif shot_type == "medium":
            # Character positioning guide
            char_width = 150
            draw.rectangle([center_x - char_width//2, third_y1, 
                           center_x + char_width//2, self.panel_height - 50], 
                          outline='#ccccff', width=2)

    def _wrap_text(self, text: str, max_width: int, font: ImageFont.ImageFont) -> List[str]:
        """Wrap text to fit within specified width"""
        if not PIL_AVAILABLE:
            return [text]
            
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            try:
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(test_line) * 8  # Fallback estimation
                
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def generate_panel_image(self, panel: StoryboardPanel, output_path: str) -> bool:
        """Generate and save a panel image"""
        try:
            img = self.create_panel_template(panel)
            if img:
                img.save(output_path, 'PNG', quality=95)
                logger.info(f"Generated panel image: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to generate panel image: {e}")
        return False

class ScriptAnalyzer:
    """Analyze scripts and extract scenes for storyboarding"""
    
    def __init__(self):
        self.scene_markers = [
            "FADE IN:", "FADE OUT:", "CUT TO:", "DISSOLVE TO:",
            "INT.", "EXT.", "SCENE", "SEQUENCE"
        ]
        self.character_markers = [
            "(V.O.)", "(O.S.)", "(CONT'D)"
        ]

    def parse_script(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse script content and extract scenes"""
        lines = script_content.split('\n')
        scenes = []
        current_scene = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check for scene headers
            if self._is_scene_header(line):
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = {
                    'scene_number': len(scenes) + 1,
                    'header': line,
                    'location': self._extract_location(line),
                    'time': self._extract_time(line),
                    'action': [],
                    'dialogue': [],
                    'line_number': i + 1
                }
            
            elif current_scene:
                if self._is_character_line(line):
                    # Next line should be dialogue
                    if i + 1 < len(lines):
                        dialogue_line = lines[i + 1].strip()
                        current_scene['dialogue'].append({
                            'character': line.rstrip(':'),
                            'text': dialogue_line
                        })
                elif self._is_action_line(line):
                    current_scene['action'].append(line)
        
        # Add final scene
        if current_scene:
            scenes.append(current_scene)
        
        logger.info(f"Parsed {len(scenes)} scenes from script")
        return scenes

    def _is_scene_header(self, line: str) -> bool:
        """Check if line is a scene header"""
        upper_line = line.upper()
        return any(marker in upper_line for marker in self.scene_markers[:4]) or \
               (upper_line.startswith(('INT.', 'EXT.')))

    def _is_character_line(self, line: str) -> bool:
        """Check if line is a character speaking"""
        return line.isupper() and line.endswith(':') and len(line.split()) <= 3

    def _is_action_line(self, line: str) -> bool:
        """Check if line is action/description"""
        return not (line.isupper() and line.endswith(':')) and not line.startswith('(')

    def _extract_location(self, header: str) -> str:
        """Extract location from scene header"""
        parts = header.split(' - ')
        if len(parts) > 1:
            return parts[0].replace('INT.', '').replace('EXT.', '').strip()
        return "UNKNOWN"

    def _extract_time(self, header: str) -> str:
        """Extract time of day from scene header"""
        time_keywords = ['DAY', 'NIGHT', 'DAWN', 'DUSK', 'MORNING', 'EVENING']
        for keyword in time_keywords:
            if keyword in header.upper():
                return keyword
        return "UNSPECIFIED"

    def generate_storyboard_from_scenes(self, scenes: List[Dict[str, Any]], project_name: str) -> Storyboard:
        """Convert parsed scenes into storyboard panels"""
        panels = []
        
        for scene in scenes:
            # Create establishing shot panel
            establishing_panel = StoryboardPanel(
                panel_id=f"S{scene['scene_number']:02d}P01",
                scene_number=scene['scene_number'],
                shot_type="establishing",
                camera_angle="eye-level",
                action_description=f"Establishing shot: {scene['location']} - {scene['time']}",
                notes=f"Location: {scene['location']}, Time: {scene['time']}"
            )
            panels.append(establishing_panel)
            
            panel_count = 2
            
            # Create panels for action sequences
            for action in scene['action']:
                if len(action) > 10:  # Only significant actions
                    shot_type = self._determine_shot_type(action)
                    camera_angle = self._determine_camera_angle(action)
                    
                    action_panel = StoryboardPanel(
                        panel_id=f"S{scene['scene_number']:02d}P{panel_count:02d}",
                        scene_number=scene['scene_number'],
                        shot_type=shot_type,
                        camera_angle=camera_angle,
                        action_description=action,
                        duration=self._estimate_duration(action)
                    )
                    panels.append(action_panel)
                    panel_count += 1
            
            # Create panels for dialogue
            for dialogue in scene['dialogue']:
                dialogue_panel = StoryboardPanel(
                    panel_id=f"S{scene['scene_number']:02d}P{panel_count:02d}",
                    scene_number=scene['scene_number'],
                    shot_type="medium",
                    camera_angle="eye-level",
                    action_description=f"{dialogue['character']} speaking",
                    dialogue=dialogue['text'],
                    duration=len(dialogue['text'].split()) * 0.5  # Rough speech timing
                )
                panels.append(dialogue_panel)
                panel_count += 1
        
        # Create storyboard
        storyboard = Storyboard(
            project_name=project_name,
            title=f"{project_name} - Storyboard",
            description=f"Auto-generated storyboard from script analysis ({len(scenes)} scenes, {len(panels)} panels)",
            panels=panels,
            metadata={
                "total_scenes": len(scenes),
                "total_panels": len(panels),
                "estimated_duration": sum(p.duration or 0 for p in panels),
                "generation_method": "script_analysis"
            }
        )
        
        logger.info(f"Generated storyboard: {len(panels)} panels from {len(scenes)} scenes")
        return storyboard

    def _determine_shot_type(self, action: str) -> str:
        """Determine appropriate shot type from action description"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['face', 'eyes', 'expression', 'smile', 'frown']):
            return "close-up"
        elif any(word in action_lower for word in ['room', 'building', 'landscape', 'wide', 'overview']):
            return "wide"
        elif any(word in action_lower for word in ['walks', 'moves', 'stands', 'sits']):
            return "medium"
        else:
            return "medium"

    def _determine_camera_angle(self, action: str) -> str:
        """Determine camera angle from action description"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['above', 'overhead', 'bird']):
            return "overhead"
        elif any(word in action_lower for word in ['below', 'up at', 'towering']):
            return "low"
        elif any(word in action_lower for word in ['down at', 'looking down']):
            return "high"
        else:
            return "eye-level"

    def _estimate_duration(self, action: str) -> float:
        """Estimate shot duration based on action complexity"""
        word_count = len(action.split())
        
        if word_count < 5:
            return 2.0  # Quick action
        elif word_count < 15:
            return 4.0  # Normal action
        else:
            return 6.0  # Complex action

class StoryboardExporter:
    """Export storyboards to various formats"""
    
    def __init__(self, visualizer: StoryboardVisualizer):
        self.visualizer = visualizer

    def export_to_json(self, storyboard: Storyboard, output_path: str):
        """Export storyboard data to JSON"""
        data = asdict(storyboard)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported storyboard to JSON: {output_path}")

    def export_to_html(self, storyboard: Storyboard, output_dir: str):
        """Export storyboard as interactive HTML"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate panel images
        panel_images = []
        images_dir = os.path.join(output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        for panel in storyboard.panels:
            image_filename = f"panel_{panel.panel_id}.png"
            image_path = os.path.join(images_dir, image_filename)
            
            if self.visualizer.generate_panel_image(panel, image_path):
                panel_images.append(image_filename)
            else:
                panel_images.append(None)
        
        # Generate HTML
        html_content = self._generate_html_template(storyboard, panel_images)
        
        html_path = os.path.join(output_dir, 'storyboard.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Exported storyboard to HTML: {html_path}")

    def _generate_html_template(self, storyboard: Storyboard, panel_images: List[str]) -> str:
        """Generate HTML template for storyboard"""
        panels_html = ""
        
        for i, panel in enumerate(storyboard.panels):
            image_src = f"images/{panel_images[i]}" if panel_images[i] else ""
            
            panels_html += f"""
            <div class="panel" id="panel-{panel.panel_id}">
                <div class="panel-header">
                    <h3>Panel {panel.panel_id} - Scene {panel.scene_number}</h3>
                    <span class="shot-info">{panel.shot_type} | {panel.camera_angle}</span>
                    {f'<span class="duration">{panel.duration}s</span>' if panel.duration else ''}
                </div>
                <div class="panel-content">
                    {'<img src="' + image_src + '" alt="Panel ' + panel.panel_id + '" class="panel-image">' if image_src else '<div class="panel-placeholder">Image not available</div>'}
                    <div class="panel-description">
                        <p><strong>Action:</strong> {panel.action_description}</p>
                        {f'<p><strong>Dialogue:</strong> "{panel.dialogue}"</p>' if panel.dialogue else ''}
                        {f'<p><strong>Notes:</strong> {panel.notes}</p>' if panel.notes else ''}
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{storyboard.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header h1 {{ margin: 0; color: #333; }}
                .header .meta {{ color: #666; margin-top: 10px; }}
                .panels {{ display: grid; gap: 20px; }}
                .panel {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .panel-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
                .panel-header h3 {{ margin: 0; color: #333; }}
                .shot-info {{ background: #007acc; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
                .duration {{ background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
                .panel-content {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }}
                .panel-image {{ width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
                .panel-placeholder {{ width: 100%; height: 200px; background: #f8f9fa; border: 2px dashed #dee2e6; display: flex; align-items: center; justify-content: center; color: #6c757d; border-radius: 4px; }}
                .panel-description p {{ margin: 10px 0; }}
                .panel-description strong {{ color: #555; }}
                @media (max-width: 768px) {{
                    .panel-content {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{storyboard.title}</h1>
                <div class="meta">
                    <p>{storyboard.description}</p>
                    <p><strong>Created:</strong> {storyboard.created_at}</p>
                    <p><strong>Total Panels:</strong> {len(storyboard.panels)} | <strong>Estimated Duration:</strong> {storyboard.metadata.get('estimated_duration', 'N/A')}s</p>
                </div>
            </div>
            <div class="panels">
                {panels_html}
            </div>
        </body>
        </html>
        """

class CraftStoryboardManager:
    """Main manager class for Craft storyboard operations"""
    
    def __init__(self, output_dir: str = "storyboards"):
        self.output_dir = output_dir
        self.visualizer = StoryboardVisualizer()
        self.analyzer = ScriptAnalyzer()
        self.exporter = StoryboardExporter(self.visualizer)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def create_storyboard_from_script(self, script_path: str, project_name: str) -> Storyboard:
        """Complete workflow: script -> scenes -> storyboard"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Parse script into scenes
            scenes = self.analyzer.parse_script(script_content)
            
            # Generate storyboard
            storyboard = self.analyzer.generate_storyboard_from_scenes(scenes, project_name)
            
            return storyboard
            
        except Exception as e:
            logger.error(f"Failed to create storyboard from script: {e}")
            raise

    def export_storyboard(self, storyboard: Storyboard, formats: List[str] = ['html', 'json']):
        """Export storyboard in specified formats"""
        project_dir = os.path.join(self.output_dir, storyboard.project_name)
        
        for format_type in formats:
            if format_type == 'html':
                self.exporter.export_to_html(storyboard, project_dir)
            elif format_type == 'json':
                json_path = os.path.join(project_dir, f"{storyboard.project_name}_storyboard.json")
                self.exporter.export_to_json(storyboard, json_path)
        
        logger.info(f"Exported storyboard in {formats} formats to {project_dir}")

def main():
    """Example usage of the Craft Storyboard system"""
    # Initialize the manager
    manager = CraftStoryboardManager("output/storyboards")
    
    # Example script content
    example_script = """
    FADE IN:
    
    EXT. FOREST - DAY
    
    A mysterious fog rolls through ancient trees. Sunlight filters through the canopy.
    
    MAYA walks cautiously along a narrow path, her camera ready.
    
    MAYA:
    The locals warned me about this place.
    
    She pauses, hearing a strange sound in the distance.
    
    MAYA: (CONT'D)
    But I have to document what's happening here.
    
    CUT TO:
    
    INT. ABANDONED CABIN - DAY
    
    Maya pushes open a creaking door. Dust particles dance in the light.
    
    MAYA:
    Hello? Anyone here?
    
    The floorboards groan under her feet as she explores.
    
    FADE OUT.
    """
    
    # Create a temporary script file
    script_path = os.path.join(manager.output_dir, "example_script.txt")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(example_script)
    
    # Generate storyboard
    storyboard = manager.create_storyboard_from_script(script_path, "Mystery_Forest")
    
    # Export in multiple formats
    manager.export_storyboard(storyboard, ['html', 'json'])
    
    logger.info("Storyboard generation completed!")

if __name__ == "__main__":
    main()