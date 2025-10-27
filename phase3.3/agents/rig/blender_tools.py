"""
Rig Agent - Blender Tools Integration
Advanced Blender Python API helpers for modeling, rigging, and automation

Phase 3.3 Enhancement:
- Modeling shortcuts and templates
- Rigging automation with preset configurations
- Node setup templates for materials and geometry
- Export/import utilities for game engines
"""

import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion
from typing import Dict, List, Tuple, Optional, Any
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlenderModelingTools:
    """Advanced modeling shortcuts and templates"""
    
    @staticmethod
    def create_base_mesh(mesh_type: str = "cube", location: Vector = Vector((0, 0, 0))) -> bpy.types.Object:
        """Create common base meshes with standard naming"""
        mesh_templates = {
            "cube": lambda: bpy.ops.mesh.primitive_cube_add(location=location),
            "sphere": lambda: bpy.ops.mesh.primitive_uv_sphere_add(location=location),
            "cylinder": lambda: bpy.ops.mesh.primitive_cylinder_add(location=location),
            "plane": lambda: bpy.ops.mesh.primitive_plane_add(location=location),
            "torus": lambda: bpy.ops.mesh.primitive_torus_add(location=location),
            "suzanne": lambda: bpy.ops.mesh.primitive_monkey_add(location=location)
        }
        
        if mesh_type not in mesh_templates:
            raise ValueError(f"Unknown mesh type: {mesh_type}")
        
        # Clear selection and create mesh
        bpy.ops.object.select_all(action='DESELECT')
        mesh_templates[mesh_type]()
        
        obj = bpy.context.active_object
        obj.name = f"RigBase_{mesh_type.title()}"
        logger.info(f"Created base mesh: {obj.name}")
        return obj

    @staticmethod
    def apply_subdivision_workflow(obj: bpy.types.Object, levels: int = 2, render_levels: int = 3):
        """Apply subdivision surface with proper workflow settings"""
        bpy.context.view_layer.objects.active = obj
        
        # Add subdivision modifier
        subdiv = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
        subdiv.levels = levels
        subdiv.render_levels = render_levels
        subdiv.use_limit_surface = True
        
        # Add edge split for hard edges
        edge_split = obj.modifiers.new(name="EdgeSplit", type='EDGE_SPLIT')
        edge_split.split_angle = 0.523599  # 30 degrees
        edge_split.use_edge_angle = True
        
        logger.info(f"Applied subdivision workflow to {obj.name}")

    @staticmethod
    def create_detail_geometry(obj: bpy.types.Object, detail_type: str = "bevel"):
        """Add common detail geometry operations"""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        if detail_type == "bevel":
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bevel(offset=0.1, segments=3)
        elif detail_type == "inset":
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.inset_faces(thickness=0.05)
        elif detail_type == "loop_cut":
            bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts": 2})
        
        bpy.ops.object.mode_set(mode='OBJECT')
        logger.info(f"Added {detail_type} detail to {obj.name}")

class BlenderRiggingTools:
    """Advanced rigging automation and templates"""
    
    @staticmethod
    def create_basic_armature(name: str = "RigArmature") -> bpy.types.Object:
        """Create a basic armature with standard settings"""
        bpy.ops.object.armature_add(location=(0, 0, 0))
        armature = bpy.context.active_object
        armature.name = name
        
        # Configure armature settings
        armature.data.display_type = 'STICK'
        armature.show_in_front = True
        
        logger.info(f"Created armature: {name}")
        return armature

    @staticmethod
    def setup_ik_chain(armature: bpy.types.Object, bone_names: List[str], target_name: str):
        """Setup IK chain with target and pole"""
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        
        # Create IK constraint on last bone
        if bone_names:
            last_bone = armature.pose.bones[bone_names[-1]]
            ik_constraint = last_bone.constraints.new('IK')
            ik_constraint.target = bpy.data.objects.get(target_name)
            ik_constraint.chain_count = len(bone_names)
            
            logger.info(f"Setup IK chain: {bone_names} -> {target_name}")
        
        bpy.ops.object.mode_set(mode='OBJECT')

    @staticmethod
    def create_control_shapes(armature: bpy.types.Object):
        """Create custom bone shapes for rig controls"""
        shapes_to_create = [
            ("Circle", "CIRCLE"),
            ("Square", "CUBE"),
            ("Arrow", "ARROW"),
            ("Sphere", "UV_SPHERE")
        ]
        
        for shape_name, primitive in shapes_to_create:
            # Create shape object
            if primitive == "CIRCLE":
                bpy.ops.mesh.primitive_circle_add(radius=1)
            elif primitive == "CUBE":
                bpy.ops.mesh.primitive_cube_add(size=2)
            elif primitive == "ARROW":
                bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2)
            elif primitive == "UV_SPHERE":
                bpy.ops.mesh.primitive_uv_sphere_add(radius=1)
            
            shape_obj = bpy.context.active_object
            shape_obj.name = f"Control_{shape_name}"
            
            # Hide from render and viewport
            shape_obj.hide_render = True
            shape_obj.hide_set(True)
        
        logger.info("Created control shapes")

class BlenderNodeTools:
    """Material and geometry node setup templates"""
    
    @staticmethod
    def create_pbr_material(name: str = "RigPBR", base_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)) -> bpy.types.Material:
        """Create a standard PBR material setup"""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        nodes.clear()
        
        # Add essential nodes
        output = nodes.new(type='ShaderNodeOutputMaterial')
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        
        # Position nodes
        output.location = (300, 0)
        principled.location = (0, 0)
        
        # Connect nodes
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        # Set base color
        principled.inputs['Base Color'].default_value = (*base_color, 1.0)
        
        logger.info(f"Created PBR material: {name}")
        return mat

    @staticmethod
    def setup_texture_coordinates(material: bpy.types.Material):
        """Add proper texture coordinate setup"""
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Add texture coordinate and mapping nodes
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        mapping = nodes.new(type='ShaderNodeMapping')
        
        # Position nodes
        tex_coord.location = (-600, 0)
        mapping.location = (-400, 0)
        
        # Connect UV output to mapping
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        
        logger.info(f"Added texture coordinates to {material.name}")

    @staticmethod
    def create_geometry_nodes_modifier(obj: bpy.types.Object, modifier_name: str = "GeometryNodes"):
        """Add geometry nodes modifier with basic setup"""
        bpy.context.view_layer.objects.active = obj
        
        # Add geometry nodes modifier
        geo_modifier = obj.modifiers.new(name=modifier_name, type='NODES')
        
        # Create new geometry nodes group
        node_group = bpy.data.node_groups.new(name=f"{obj.name}_GeoNodes", type='GeometryNodeTree')
        geo_modifier.node_group = node_group
        
        # Add input and output nodes
        input_node = node_group.nodes.new(type='NodeGroupInput')
        output_node = node_group.nodes.new(type='NodeGroupOutput')
        
        # Position nodes
        input_node.location = (-200, 0)
        output_node.location = (200, 0)
        
        # Create geometry sockets
        node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
        # Connect input to output (passthrough)
        node_group.links.new(input_node.outputs['Geometry'], output_node.inputs['Geometry'])
        
        logger.info(f"Added geometry nodes to {obj.name}")
        return geo_modifier

class BlenderExportTools:
    """Export utilities for game engines and external tools"""
    
    @staticmethod
    def export_fbx_game_ready(filepath: str, objects: List[bpy.types.Object] = None):
        """Export FBX with game-ready settings"""
        if objects is None:
            objects = [obj for obj in bpy.context.selected_objects]
        
        # Select target objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        
        # Export with game-ready settings
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            use_active_collection=False,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            use_space_transform=True,
            bake_space_transform=False,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            use_mesh_modifiers_render=True,
            mesh_smooth_type='OFF',
            use_subsurf=False,
            use_mesh_edges=False,
            use_tspace=False,
            use_armature_deform_only=True,
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            armature_nodetype='NULL',
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=True,
            bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=1.0,
        )
        
        logger.info(f"Exported FBX to {filepath}")

    @staticmethod
    def export_gltf_web_ready(filepath: str, objects: List[bpy.types.Object] = None):
        """Export glTF with web-ready settings"""
        if objects is None:
            objects = [obj for obj in bpy.context.selected_objects]
        
        # Select target objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        
        # Export with web-ready settings
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_selection=True,
            export_format='GLTF_SEPARATE',
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_materials='EXPORT',
            export_colors=True,
            use_mesh_edges=False,
            use_mesh_vertices=False,
            export_cameras=False,
            export_extras=False,
            export_yup=True,
            export_apply=False,
            export_animations=True,
            export_frame_range=True,
            export_frame_step=1,
            export_force_sampling=True,
            export_nla_strips=True,
            export_def_bones=False,
            optimize_animation_size=True,
            export_current_frame=False,
            export_skins=True,
            export_all_influences=False,
            export_morph=True,
            export_morph_normal=True,
            export_morph_tangent=False,
            export_lights=False,
        )
        
        logger.info(f"Exported glTF to {filepath}")

class RigWorkflowManager:
    """High-level workflow management for Rig agent"""
    
    def __init__(self):
        self.modeling = BlenderModelingTools()
        self.rigging = BlenderRiggingTools()
        self.nodes = BlenderNodeTools()
        self.export = BlenderExportTools()

    def create_character_base(self, character_name: str) -> Dict[str, bpy.types.Object]:
        """Complete character creation workflow"""
        results = {}
        
        # Create base mesh
        body_mesh = self.modeling.create_base_mesh("cube", Vector((0, 0, 1)))
        body_mesh.name = f"{character_name}_Body"
        self.modeling.apply_subdivision_workflow(body_mesh)
        results['body'] = body_mesh
        
        # Create head
        head_mesh = self.modeling.create_base_mesh("sphere", Vector((0, 0, 2.5)))
        head_mesh.name = f"{character_name}_Head"
        results['head'] = head_mesh
        
        # Create armature
        armature = self.rigging.create_basic_armature(f"{character_name}_Rig")
        self.rigging.create_control_shapes(armature)
        results['armature'] = armature
        
        # Create materials
        body_mat = self.nodes.create_pbr_material(f"{character_name}_Body_Mat", (0.7, 0.5, 0.3))
        self.nodes.setup_texture_coordinates(body_mat)
        body_mesh.data.materials.append(body_mat)
        
        head_mat = self.nodes.create_pbr_material(f"{character_name}_Head_Mat", (0.8, 0.6, 0.4))
        head_mesh.data.materials.append(head_mat)
        
        logger.info(f"Created character base for {character_name}")
        return results

    def setup_environment_asset(self, asset_name: str, asset_type: str = "building") -> bpy.types.Object:
        """Create environment assets with proper setup"""
        base_meshes = {
            "building": "cube",
            "tree": "cylinder", 
            "rock": "sphere",
            "platform": "plane"
        }
        
        mesh_type = base_meshes.get(asset_type, "cube")
        asset_obj = self.modeling.create_base_mesh(mesh_type)
        asset_obj.name = f"{asset_name}_{asset_type.title()}"
        
        # Add geometry nodes for procedural details
        if asset_type in ["tree", "rock"]:
            self.nodes.create_geometry_nodes_modifier(asset_obj)
        
        # Create environment material
        env_mat = self.nodes.create_pbr_material(f"{asset_name}_Mat", (0.5, 0.5, 0.5))
        asset_obj.data.materials.append(env_mat)
        
        logger.info(f"Created environment asset: {asset_name}")
        return asset_obj

    def batch_export_for_game(self, export_dir: str, project_name: str):
        """Batch export all relevant objects for game engine"""
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Export characters
        characters = [obj for obj in bpy.data.objects if "Body" in obj.name]
        if characters:
            fbx_path = os.path.join(export_dir, f"{project_name}_Characters.fbx")
            self.export.export_fbx_game_ready(fbx_path, characters)
        
        # Export environment
        environment = [obj for obj in bpy.data.objects if any(env_type in obj.name.lower() 
                      for env_type in ["building", "tree", "rock", "platform"])]
        if environment:
            gltf_path = os.path.join(export_dir, f"{project_name}_Environment.gltf")
            self.export.export_gltf_web_ready(gltf_path, environment)
        
        logger.info(f"Batch export completed to {export_dir}")

# Example usage functions for integration
def initialize_rig_workspace():
    """Initialize Rig agent workspace in Blender"""
    # Set up workspace for rigging
    bpy.context.workspace.name = "Rig_Workspace"
    
    # Configure viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces[0]
            space.shading.type = 'MATERIAL'
            space.overlay.show_wireframes = True
            space.overlay.wireframe_threshold = 0.5

def create_project_template(project_name: str, project_type: str = "character"):
    """Create a complete project template"""
    workflow = RigWorkflowManager()
    
    if project_type == "character":
        return workflow.create_character_base(project_name)
    elif project_type == "environment":
        return workflow.setup_environment_asset(project_name, "building")
    
    logger.info(f"Created {project_type} project: {project_name}")

if __name__ == "__main__":
    # Example: Create a character template
    initialize_rig_workspace()
    character_objects = create_project_template("RigCharacter", "character")
    logger.info(f"Created character with objects: {list(character_objects.keys())}")