"""
O3DE Engine Knowledge Base
Teaches the AI everything about O3DE's features, components, systems, and APIs
so it can generate accurate, working code and configurations.
"""

O3DE_KNOWLEDGE = {
    "engine_info": {
        "name": "Open 3D Engine (O3DE)",
        "version": "26.05",
        "architecture": "Entity Component System (ECS)",
        "rendering": "Atom Renderer (PBR, Ray Tracing)",
        "scripting": ["Lua", "ScriptCanvas (Visual Scripting)", "Python (Editor)"],
        "physics": "PhysX 5",
        "animation": "EMotionFX",
        "audio": "Open Audio Engine (Oculus Audio / Built-in)",
        "ui": "LyShine (UI Canvas)",
        "networking": "Multiplayer (NetBinding, Client/Server)",
        "platforms": ["Windows", "Linux", "Mac", "iOS", "Android", "Consoles"],
    },

    "ecs_components": {
        # Core Transform & Entity
        "TransformComponent": {
            "description": "Position, rotation, scale of an entity",
            "properties": ["Translation", "Rotation", "Scale", "ParentEntity"],
            "buses": ["TransformBus", "LocalTransformBus", "WorldTransformBus"],
        },
        "ShapeComponent": {
            "description": "Defines collision/trigger shapes",
            "types": ["BoxShape", "SphereShape", "CapsuleShape", "CylinderShape", "PolygonPrismShape"],
            "properties": ["Dimensions", "TriggerArea", "Colliders"],
        },

        # Rendering
        "MeshComponent": {
            "description": "3D mesh rendering",
            "properties": ["MeshAsset", "MaterialAsset", "SortKey"],
            "bus": "MeshComponentRequestBus",
        },
        "MaterialComponent": {
            "description": "PBR material assignment",
            "properties": ["MaterialAsset", "MaterialSlotMap"],
        },
        "LightComponent": {
            "description": "Light sources (point, spot, directional, area)",
            "types": ["PointLight", "SpotLight", "DirectionalLight", "AreaLight"],
            "properties": ["Color", "Intensity", "AttenuationRadius", "ConeAngle", "ShadowEnabled"],
        },
        "CameraComponent": {
            "description": "Camera for rendering",
            "properties": ["FOV", "NearClip", "FarClip", "DepthOfField", "Orthographic"],
        },

        # Physics
        "PhysXColliderComponent": {
            "description": "Physics collider shape",
            "properties": ["ShapeType", "Trigger", "SimulationDisabled", "Tag"],
        },
        "PhysXRigidBodyComponent": {
            "description": "Physics rigid body dynamics",
            "properties": ["Mass", "LinearDamping", "AngularDamping", "Gravity", "Kinematic"],
        },
        "PhysXCharacterControllerComponent": {
            "description": "Character controller for player/NPC movement",
            "properties": ["SlopeLimit", "StepOffset", "SkinWidth", "Radius", "Height"],
        },

        # Terrain
        "TerrainWorldComponent": {
            "description": "Global terrain settings",
            "properties": ["MinHeight", "MaxHeight", "QueryResolution"],
        },
        "TerrainLayerSpawnerComponent": {
            "description": "Defines a terrain area using a shape",
            "properties": ["Priority", "ShapeType"],
        },
        "TerrainHeightGradientListComponent": {
            "description": "Connects gradient outputs to terrain height",
            "properties": ["GradientInputs"],
        },
        "TerrainSurfaceGradientListComponent": {
            "description": "Connects gradient outputs to surface type tags",
            "properties": ["GradientInputs"],
        },
        "TerrainPhysicsColliderComponent": {
            "description": "Physics collision for terrain",
            "properties": ["TriggerHeight", "TriggerTag"],
        },

        # Gradient Signal (for terrain, materials, etc.)
        "GradientTransformComponent": {
            "description": "Transforms gradient space",
            "properties": ["Frequency", "Amplitude", "Offset"],
        },
        "ImageGradientComponent": {
            "description": "Generates gradient from image/heightmap",
            "properties": ["ImageAsset", "TilingChannels"],
        },
        "GradientMixComponent": {
            "description": "Mixes multiple gradients",
            "modes": ["Add", "Subtract", "Multiply", "Divide", "Min", "Max", "Average"],
        },
        "PerlinNoiseGradientComponent": {
            "description": "Perlin noise gradient generator",
            "properties": ["Frequency", "Octaves", "Amplitude", "Seed"],
        },
        "SurfaceMaskGradientComponent": {
            "description": "Gradient based on surface tags",
            "properties": ["SurfaceTags"],
        },

        # Audio
        "AudioTriggerComponent": {
            "description": "Plays audio triggers",
            "properties": ["TriggerName"],
        },
        "AudioRtpcComponent": {
            "description": "Real-time parameter control for audio",
            "properties": ["RtpcName", "Value"],
        },
        "AudioEnvironmentComponent": {
            "description": "Audio environment zone",
            "properties": ["EnvironmentName"],
        },

        # Animation (EMotionFX)
        "AnimGraphComponent": {
            "description": "Animation state machine",
            "properties": ["AnimGraphAsset", "MotionSetAsset"],
        },
        "AnimBoneComponent": {
            "description": "Bone transform for animation",
            "properties": ["BoneName", "MovementBone"],
        },

        # Scripting
        "LuaComponent": {
            "description": "Runs Lua scripts",
            "properties": ["ScriptAsset", "ActivateOnActivation"],
        },
        "ScriptCanvasComponent": {
            "description": "Visual scripting nodes",
            "properties": ["ScriptCanvasAsset"],
        },

        # UI
        "UiCanvasAssetRefComponent": {
            "description": "References a UI canvas",
            "properties": ["CanvasAsset"],
        },
        "UiTextComponent": {
            "description": "Text display",
            "properties": ["Text", "FontSize", "FontAsset", "Color"],
        },
        "UiButtonComponent": {
            "description": "Interactive button",
            "properties": ["Text", "OnClickActions"],
        },

        # Spawning
        "NetSpawnerComponent": {
            "description": "Network-aware entity spawning",
            "properties": ["PrefabPath", "SpawnCount", "SpawnInterval"],
        },

        # Tags
        "TagComponent": {
            "description": "Tags an entity for identification",
            "properties": ["Tags"],
        },

        # Signals & Events
        "Signals": {
            "OnEntityActivated": "Fired when entity activates",
            "OnEntityDeactivated": "Fired when entity deactivates",
            "OnCollisionBegin": "Fired on physics collision start",
            "OnCollisionEnd": "Fired on physics collision end",
            "OnTriggerEnter": "Fired when entity enters trigger",
            "OnTriggerExit": "Fired when entity exits trigger",
            "OnTick": "Fired every frame (deltaTime, timePoint)",
        },
    },

    "terrain_system": {
        "description": "O3DE terrain is gradient-based, not heightmap-based",
        "workflow": [
            "1. Create entity with TerrainWorldComponent (global settings)",
            "2. Create entity with TerrainLayerSpawnerComponent + Shape (defines area)",
            "3. Create entity with PerlinNoiseGradientComponent or ImageGradientComponent",
            "4. Connect gradient to TerrainHeightGradientListComponent",
            "5. Add TerrainSurfaceGradientListComponent for surface types",
            "6. Add TerrainPhysicsColliderComponent for collision",
        ],
        "biomes": {
            "desert": {"surfaces": ["sand", "rock"], "height_range": [0, 200]},
            "forest": {"surfaces": ["grass", "dirt", "rock", "snow"], "height_range": [0, 1500]},
            "tundra": {"surfaces": ["snow", "ice", "rock"], "height_range": [0, 1000]},
            "volcanic": {"surfaces": ["lava_rock", "ash", "obsidian"], "height_range": [0, 2000]},
            "coastal": {"surfaces": ["sand", "grass", "dirt", "rock"], "height_range": [-10, 800]},
            "temperate": {"surfaces": ["grass", "dirt", "rock", "snow"], "height_range": [0, 1200]},
        },
    },

    "lua_scripting": {
        "boilerplate": '''
-- O3DE Lua Component
local MyComponent = {
    Properties = {
        Speed = { default = 5.0, description = "Movement speed" },
    },
}

function MyComponent:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
end

function MyComponent:OnDeactivate()
    self.tickHandler:Disconnect()
end

function MyComponent:OnTick(deltaTime, timePoint)
    -- Your code here
end
''',
        "common_patterns": {
            "movement": "TransformBus.Event.SetLocalTranslation(entityId, pos + velocity * deltaTime)",
            "rotation": "TransformBus.Event.SetLocalRotation(entityId, rotation * Quaternion.CreateFromAxisAngle(axis, angle))",
            "scale": "TransformBus.Event.SetLocalScale(entityId, Vector3(x, y, z))",
            "get_position": "TransformBus.Event.GetLocalTranslation(entityId)",
            "set_position": "TransformBus.Event.SetLocalTranslation(entityId, Vector3(x, y, z))",
            "play_audio": "AudioTriggerComponentRequestBus.Event.ExecuteTrigger(entityId, triggerName)",
            "apply_force": "PhysXNativePhysicsForceRequestBus.Event.ApplyForce(entityId, Vector3(fx, fy, fz))",
            "get_velocity": "PhysXNativePhysicsForceRequestBus.Event.GetVelocity(entityId)",
            "spawn_entity": "DynamicBus.ToolsRequestBus.Broadcast.RequestCreateEntity(prefabPath, position)",
            "destroy_entity": "DynamicBus.ToolsRequestBus.Broadcast.RequestDeleteEntity(entityId)",
            "set_active": "ActiveNotificationBus.Broadcast.OnEntityActivated()",
            "debug_log": "Debug.Log(message)",
        },
    },

    "python_editor_api": {
        "description": "Python API available in O3DE editor",
        "key_modules": {
            "azlmbr.editor": "Editor operations (entity creation, component manipulation)",
            "azlmbr.entity": "Entity operations",
            "azlmbr.bus": "EBus communication",
            "azlmbr.asset": "Asset management",
            "azlmbr.math": "Math types (Vector3, Quaternion, Color, etc.)",
            "azlmbr.legacy.general": "General utility functions",
        },
        "common_operations": {
            "create_entity": "editor.EditorEntityAPIBus.Broadcast.RequestCreateEntity(name, position)",
            "add_component": "editor.EditorEntityAPIBus.Broadcast.AddComponent(entityId, componentTypeId)",
            "set_property": "editor.EditorEntityAPIBus.Broadcast.SetComponentProperty(entityId, componentTypeId, propertyPath, value)",
            "get_property": "editor.EditorEntityAPIBus.Broadcast.GetComponentProperty(entityId, componentTypeId, propertyPath)",
            "find_component_type": "editor.EditorEntityAPIBus.Broadcast.FindComponentTypeById(componentTypeName)",
            "select_entity": "editor.EditorEntityAPIBus.Broadcast.SetSelectedEntities([entityId])",
            "undo": "editor.EditorUndoBus.Broadcast.BeginUndoBatch(name); ... editor.EditorUndoBus.Broadcast.EndUndoBatch()",
        },
    },

    "asset_pipeline": {
        "description": "O3DE Asset Processor auto-compiles assets",
        "supported_formats": {
            "models": [".fbx", ".gltf", ".glb", ".obj", ".blend"],
            "textures": [".png", ".jpg", ".tga", ".bmp", ".tif", ".exr", ".hdr"],
            "audio": [".wav", ".mp3", ".ogg", ".flac"],
            "scripts": [".lua", ".py"],
            "animations": [".fbx", ".bvh"],
            "materials": [".material"],
            "shaders": [".shader", ".hlsl"],
            "ui": [".uicanvas"],
            "prefabs": [".prefab"],
        },
        "asset_types": {
            "ModelAsset": "3D mesh (.fbx)",
            "TextureAsset": "Texture map (.png, .tga)",
            "MaterialAsset": "PBR material (.material)",
            "LuaScriptAsset": "Lua script (.lua)",
            "ScriptCanvasAsset": "Visual script (.scriptcanvas)",
            "PrefabAsset": "Entity prefab (.prefab)",
            "AnimationAsset": "Skeletal animation (.fbx)",
            "AudioAsset": "Sound file (.wav, .ogg)",
            "GradientAsset": "Gradient data (.gradient)",
            "ImageAsset": "Image data (.png, .exr)",
        },
    },

    "available_ai_tools": {
        "terrain": ["ProceduralTerrains", "Gaea", "World Machine"],
        "3d_models": ["Hunyuan3D", "Dust3D", "Meshy", "Tripo", "Stable Projecti3D"],
        "textures": ["ComfyUI", "Stable Diffusion", "DALL-E"],
        "code": ["AutoGen", "Cline", "RooCode", "DeepSeek-R1", "GPT-NeoX"],
        "animation": ["GANimator", "DeepMotionEditing", "Mixamo"],
        "audio": ["ElevenLabsClone", "InworldAI"],
        "orchestration": ["AutoGen (Multi-Agent)", "Cline (Autonomous Coding)"],
    },
}


def get_system_prompt():
    """Generate a system prompt that teaches the AI about O3DE."""
    prompt = """You are an expert O3DE game engine AI assistant. You help users create games using Open 3D Engine.

O3DE KNOWLEDGE:
"""
    for key, value in O3DE_KNOWLEDGE.items():
        prompt += f"\n=== {key.upper().replace('_', ' ')} ===\n"
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, dict):
                    prompt += f"  {k}:\n"
                    for kk, vv in v.items():
                        prompt += f"    {kk}: {vv}\n"
                elif isinstance(v, list):
                    prompt += f"  {k}: {', '.join(v) if v else 'none'}\n"
                else:
                    prompt += f"  {k}: {v}\n"
        elif isinstance(value, list):
            prompt += f"  {', '.join(value)}\n"
        else:
            prompt += f"  {value}\n"

    prompt += """
CAPABILITIES:
- Generate Lua/Python/ScriptCanvas code for any O3DE component
- Create terrain configurations (heightmaps, surface layers, biome settings)
- Generate 3D model pipelines (Hunyuan3D, Dust3D)
- Generate textures (ComfyUI, Stable Diffusion)
- Generate animations (GANimator, DeepMotionEditing)
- Generate audio (ElevenLabsClone TTS, InworldAI)
- Wire up ScriptCanvas blueprints
- Create complete game systems (health, inventory, AI, spawning)
- Apply everything directly to the O3DE scene

RULES:
- Always output valid O3DE code (correct EBus calls, component names, property paths)
- Use the Terrain system's gradient-based workflow, not raw heightmaps
- For Lua scripts, always include Properties table and OnActivate/OnDeactivate
- For terrain, always generate: TerrainWorldComponent, TerrainLayerSpawnerComponent, gradient component, surface layers
- Chain multiple AI tools for complex requests
- Auto-apply results to the scene when possible
- Be concise but complete
"""
    return prompt


def get_terrain_prompt(terrain_description):
    """Generate a terrain generation prompt."""
    knowledge = O3DE_KNOWLEDGE["terrain_system"]
    prompt = f"Generate a terrain based on this description: {terrain_description}\n\n"
    prompt += "Available biomes and their surface configurations:\n"
    for biome, config in knowledge["biomes"].items():
        prompt += f"  {biome}: surfaces={config['surfaces']}, height_range={config['height_range']}\n"
    prompt += "\nOutput:\n"
    prompt += "- TerrainWorldComponent settings (min/max height, query resolution)\n"
    prompt += "- PerlinNoiseGradientComponent settings (frequency, octaves, amplitude, seed)\n"
    prompt += "- TerrainHeightGradientListComponent connections\n"
    prompt += "- Surface layer configurations (surface tags, height ranges, slope ranges)\n"
    prompt += "- TerrainPhysicsColliderComponent settings\n"
    return prompt


def get_code_prompt(description, language="lua"):
    """Generate a code generation prompt."""
    knowledge = O3DE_KNOWLEDGE
    prompt = f"Generate O3DE {language} code for: {description}\n\n"
    prompt += f"Base template:\n{knowledge['lua_scripting']['boilerplate']}\n\n"
    prompt += "Available EBus calls:\n"
    for pattern, call in knowledge["lua_scripting"]["common_patterns"].items():
        prompt += f"  {pattern}: {call}\n"
    prompt += f"\nAvailable components: {', '.join(knowledge['ecs_components'].keys())}\n"
    return prompt
