"""
AI Design Studio - O3DE Editor Sidebar Panel
A vibe-coding AI assistant for terrain, assets, code, and animation generation.
"""

import azlmbr
import azlmbr.bus
import azlmbr.editor as editor
import azlmbr.asset as asset

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTextEdit,
    QPushButton, QLabel, QLineEdit, QTabWidget, QWidget,
    QComboBox, QProgressBar, QFrame, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QPlainTextEdit, QToolButton, QSizePolicy, QApplication
)
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon
import json
import os
import sys
import time
import threading
import subprocess
import traceback

# ============================================================
# AI Backend Configuration
# ============================================================

AI_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AIProject")
ASSETS_DIR = os.path.join(AI_PROJECT_ROOT, "Assets")
TERRAINS_DIR = os.path.join(ASSETS_DIR, "Terrains")
CODE_DIR = os.path.join(ASSETS_DIR, "Code")
MODELS_DIR = os.path.join(ASSETS_DIR, "Models")
TEXTURES_DIR = os.path.join(ASSETS_DIR, "Textures")
AUDIO_DIR = os.path.join(ASSETS_DIR, "Audio")
ANIMATIONS_DIR = os.path.join(ASSETS_DIR, "Animations")

AI_TOOLS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Import full game orchestrator
try:
    from full_game_orchestrator import FullGameOrchestrator
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False

# ============================================================
# Live LLM Connection - OpenRouter Free Models
# ============================================================

import urllib.request
import urllib.error

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

FREE_MODELS = {
    "auto": "openrouter/free",
    "nemotron-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-super": "nvidia/nemotron-3-super-120b-a12b:free",
    "gemma-4": "google/gemma-4-31b-it:free",
    "gpt-oss": "openai/gpt-oss-20b:free",
    "llama-3.3": "meta-llama/llama-3.3-70b-instruct:free",
    "dots3": "dots-studio/dots-3-note-preview:free",
    "laguna-s": "poolside/laguna-s-2.1:free",
}

def call_openrouter(prompt, system_prompt="", model="openrouter/free", max_tokens=4096):
    """Call OpenRouter API with free models."""
    api_key = OPENROUTER_API_KEY
    if not api_key:
        return {"error": "No API key set. Add your OpenRouter API key to the Settings tab or set OPENROUTER_API_KEY environment variable."}

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/aghosh-mv/o3de-ai-studio",
            "X-Title": "O3DE AI Design Studio",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"content": content, "model": data.get("model", model), "usage": data.get("usage", {})}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# AI Backend - Connects to various AI services
# ============================================================

class AIBackend:
    """Orchestrates calls to multiple AI tools for content generation."""

    def __init__(self):
        self.tools = {
            "terrain": TerrainGenerator(),
            "model_3d": Model3DGenerator(),
            "texture": TextureGenerator(),
            "code": CodeGenerator(),
            "animation": AnimationGenerator(),
            "audio": AudioGenerator(),
            "blueprint": BlueprintGenerator(),
        }

    def generate(self, tool_name, prompt, params=None):
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        return self.tools[tool_name].generate(prompt, params or {})


class TerrainGenerator:
    """Generates terrain heightmaps and configurations."""

    def generate(self, prompt, params):
        seed = params.get("seed", int(time.time()) % 100000)
        size = params.get("size", 2048)
        resolution = params.get("resolution", "high")

        prompt_lower = prompt.lower()
        terrain_config = {
            "name": f"ai_terrain_{seed}",
            "prompt": prompt,
            "seed": seed,
            "size": size,
            "height_range": self._guess_height_range(prompt_lower),
            "erosion": self._guess_erosion(prompt_lower),
            "biome": self._guess_biome(prompt_lower),
            "features": self._extract_features(prompt_lower),
            "o3de_config": self._generate_o3de_terrain_config(prompt_lower, seed, size),
        }

        output_path = os.path.join(TERRAINS_DIR, f"{terrain_config['name']}.json")
        os.makedirs(TERRAINS_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(terrain_config, f, indent=2)

        terrain_config["output_path"] = output_path
        terrain_config["status"] = "generated"
        return terrain_config

    def _guess_height_range(self, prompt):
        if any(w in prompt for w in ["mountain", "alpine", "canyon", "cliff"]):
            return {"min": -50, "max": 2000}
        elif any(w in prompt for w in ["hill", "rolling", "meadow"]):
            return {"min": -20, "max": 500}
        elif any(w in prompt for w in ["flat", "plain", "desert"]):
            return {"min": -10, "max": 100}
        return {"min": -50, "max": 1000}

    def _guess_erosion(self, prompt):
        if any(w in prompt for w in ["eroded", "canyon", "river", "valley"]):
            return {"iterations": 80, "strength": 0.7}
        elif any(w in prompt for w in ["sharp", "peak", "jagged"]):
            return {"iterations": 20, "strength": 0.3}
        return {"iterations": 50, "strength": 0.5}

    def _guess_biome(self, prompt):
        if any(w in prompt for w in ["desert", "sand", "arid"]):
            return "desert"
        elif any(w in prompt for w in ["forest", "jungle", "tree"]):
            return "forest"
        elif any(w in prompt for w in ["snow", "ice", "arctic", "frozen"]):
            return "tundra"
        elif any(w in prompt for w in ["volcano", "lava", "fire"]):
            return "volcanic"
        elif any(w in prompt for w in ["ocean", "island", "coast", "beach"]):
            return "coastal"
        return "temperate"

    def _extract_features(self, prompt):
        features = []
        feature_keywords = {
            "river": "river", "lake": "lake", "waterfall": "waterfall",
            "cave": "cave", "cliff": "cliff", "plateau": "plateau",
            "valley": "valley", "crater": "crater", "bridge": "bridge_path",
            "village": "village_site", "road": "road_path", "ruins": "ruins_site",
        }
        for keyword, feature in feature_keywords.items():
            if keyword in prompt:
                features.append(feature)
        return features

    def _generate_o3de_terrain_config(self, prompt, seed, size):
        height_range = self._guess_height_range(prompt)
        erosion = self._guess_erosion(prompt)
        return {
            "terrain_world": {
                "min_height": height_range["min"],
                "max_height": height_range["max"],
                "query_resolution": 1.0,
            },
            "gradient_stack": {
                "seed": seed,
                "layers": [
                    {"type": "perlin", "frequency": 0.001, "octaves": 6, "amplitude": 1.0},
                    {"type": "perlin", "frequency": 0.005, "octaves": 4, "amplitude": 0.5, "blend": "add"},
                    {"type": "perlin", "frequency": 0.02, "octaves": 2, "amplitude": 0.2, "blend": "add"},
                ],
                "erosion": {
                    "iterations": erosion["iterations"],
                    "strength": erosion["strength"],
                    " sediment_capacity": 0.01,
                    "evaporation_rate": 0.01,
                },
            },
            "surface_layers": self._generate_surface_layers(prompt),
        }

    def _generate_surface_layers(self, prompt):
        biome = self._guess_biome(prompt)
        layer_presets = {
            "desert": [
                {"name": "Sand", "tag": "sand", "min_height": 0, "max_height": 9999, "min_slope": 0, "max_slope": 90},
                {"name": "Rock", "tag": "rock", "min_height": 0, "max_height": 9999, "min_slope": 45, "max_slope": 90},
            ],
            "forest": [
                {"name": "Grass", "tag": "grass", "min_height": 0, "max_height": 800, "min_slope": 0, "max_slope": 30},
                {"name": "Dirt", "tag": "dirt", "min_height": 0, "max_height": 9999, "min_slope": 20, "max_slope": 50},
                {"name": "Rock", "tag": "rock", "min_height": 500, "max_height": 9999, "min_slope": 40, "max_slope": 90},
                {"name": "Snow", "tag": "snow", "min_height": 1200, "max_height": 9999, "min_slope": 0, "max_slope": 60},
            ],
            "tundra": [
                {"name": "Snow", "tag": "snow", "min_height": 0, "max_height": 9999, "min_slope": 0, "max_slope": 40},
                {"name": "Ice", "tag": "ice", "min_height": 0, "max_height": 9999, "min_slope": 30, "max_slope": 90},
                {"name": "Rock", "tag": "rock", "min_height": 800, "max_height": 9999, "min_slope": 50, "max_slope": 90},
            ],
            "volcanic": [
                {"name": "Lava Rock", "tag": "lava_rock", "min_height": 0, "max_height": 9999, "min_slope": 0, "max_slope": 90},
                {"name": "Ash", "tag": "ash", "min_height": 0, "max_height": 400, "min_slope": 0, "max_slope": 20},
                {"name": "Obsidian", "tag": "obsidian", "min_height": 400, "max_height": 9999, "min_slope": 30, "max_slope": 90},
            ],
            "coastal": [
                {"name": "Sand", "tag": "sand", "min_height": -10, "max_height": 30, "min_slope": 0, "max_slope": 15},
                {"name": "Grass", "tag": "grass", "min_height": 30, "max_height": 400, "min_slope": 0, "max_slope": 30},
                {"name": "Dirt", "tag": "dirt", "min_height": 100, "max_height": 9999, "min_slope": 15, "max_slope": 45},
                {"name": "Rock", "tag": "rock", "min_height": 300, "max_height": 9999, "min_slope": 35, "max_slope": 90},
            ],
            "temperate": [
                {"name": "Grass", "tag": "grass", "min_height": 0, "max_height": 600, "min_slope": 0, "max_slope": 25},
                {"name": "Dirt", "tag": "dirt", "min_height": 200, "max_height": 9999, "min_slope": 15, "max_slope": 45},
                {"name": "Rock", "tag": "rock", "min_height": 500, "max_height": 9999, "min_slope": 40, "max_slope": 90},
                {"name": "Snow", "tag": "snow", "min_height": 1000, "max_height": 9999, "min_slope": 0, "max_slope": 50},
            ],
        }
        return layer_presets.get(biome, layer_presets["temperate"])


class Model3DGenerator:
    """Generates 3D models using various AI backends."""

    def generate(self, prompt, params):
        style = params.get("style", "realistic")
        poly_count = params.get("poly_count", "medium")

        result = {
            "prompt": prompt,
            "style": style,
            "poly_count": poly_count,
            "format": "fbx",
            "pipeline": [],
            "output_path": None,
        }

        hunyuan_path = os.path.join(AI_TOOLS_ROOT, "Hunyuan3D")
        dust3d_path = os.path.join(AI_TOOLS_ROOT, "Dust3D")

        if os.path.exists(hunyuan_path):
            result["pipeline"].append({
                "tool": "Hunyuan3D",
                "method": "text_to_3d",
                "config": {
                    "prompt": prompt,
                    "style": style,
                    "output_format": "fbx",
                    "texture_resolution": 1024,
                    "pbr_materials": True,
                }
            })

        if os.path.exists(dust3d_path):
            result["pipeline"].append({
                "tool": "Dust3D",
                "method": "mesh_generation",
                "config": {
                    "prompt": prompt,
                    "smooth": True,
                    "triangulate": True,
                }
            })

        result["pipeline"].append({
            "tool": "O3DE_AssetProcessor",
            "method": "auto_import",
            "config": {
                "destination": MODELS_DIR,
                "auto_compile": True,
            }
        })

        name = prompt.replace(" ", "_")[:50]
        output_path = os.path.join(MODELS_DIR, f"{name}.json")
        os.makedirs(MODELS_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        result["output_path"] = output_path
        result["status"] = "pipeline_configured"
        return result


class TextureGenerator:
    """Generates textures using AI."""

    def generate(self, prompt, params):
        texture_type = params.get("type", "diffuse")
        resolution = params.get("resolution", 1024)
        tileable = params.get("tileable", True)

        result = {
            "prompt": prompt,
            "type": texture_type,
            "resolution": resolution,
            "tileable": tileable,
            "maps": {
                "diffuse": True,
                "normal": True,
                "roughness": True,
                "metallic": False,
                "height": False,
                "ambient_occlusion": False,
            },
            "output_path": None,
        }

        comfyui_path = os.path.join(AI_TOOLS_ROOT, "ComfyUI")
        if os.path.exists(comfyui_path):
            result["pipeline"] = {
                "tool": "ComfyUI",
                "workflow": "texture_generation",
                "config": {
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, seamless artifact",
                    "resolution": f"{resolution}x{resolution}",
                    "tileable": tileable,
                    "denoise": 0.7,
                }
            }

        name = prompt.replace(" ", "_")[:50]
        output_path = os.path.join(TEXTURES_DIR, f"{name}.json")
        os.makedirs(TEXTURES_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        result["output_path"] = output_path
        result["status"] = "configured"
        return result


class CodeGenerator:
    """Generates Lua/Python gameplay code for O3DE using live LLM or templates."""

    O3DE_SYSTEM_PROMPT = """You are an O3DE game engine code assistant. Generate Lua or Python code for O3DE.
O3DE uses:
- Entity Component System (ECS) architecture
- Lua scripting via ScriptCanvas or Lua Component
- EBus for inter-component communication (e.g., TransformBus, PhysXBus, etc.)
- azlmbr Python bindings for editor scripting
- GradientSignal for terrain/heightmap generation
- Terrain system with TerrainWorldComponent, TerrainLayerSpawnerComponent

O3DE Lua Component Template:
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

Common EBus calls:
- TransformBus.Event.SetLocalTranslation(entityId, Vector3(x, y, z))
- TransformBus.Event.GetLocalTranslation(entityId)
- TransformBus.Event.SetLocalRotation(entityId, rotation)
- Debug.Log(message)
- InputDevice.IsKeyDown("keyboard_w")
- PhysXNativePhysicsForceRequestBus.Event.ApplyForce(entityId, force)

Always output complete, working O3DE Lua code. Include the full component structure with Properties, OnActivate, OnDeactivate, and OnTick."""

    def generate(self, prompt, params):
        language = params.get("language", "lua")
        category = params.get("category", "gameplay")

        result = {
            "prompt": prompt,
            "language": language,
            "category": category,
            "code": "",
            "instructions": "",
            "output_path": None,
            "source": "template",
        }

        # Try live LLM first
        llm_result = call_openrouter(
            prompt=f"Generate O3DE {language} code for: {prompt}\n\nRequirements:\n- Complete, working O3DE component\n- Include Properties table\n- Include OnActivate/OnDeactivate/OnTick\n- Use proper EBus calls\n- Output ONLY the code, no explanations",
            system_prompt=self.O3DE_SYSTEM_PROMPT,
            model=FREE_MODELS.get("auto", "openrouter/free"),
            max_tokens=4096,
        )

        if llm_result and "content" in llm_result and not llm_result.get("error"):
            result["code"] = llm_result["content"]
            result["source"] = f"llm ({llm_result.get('model', 'unknown')})"
            result["instructions"] = f"AI-generated {language} code from live LLM."
        else:
            # Fallback to templates
            code_templates = self._get_templates()
            prompt_lower = prompt.lower()
            if any(w in prompt_lower for w in ["move", "walk", "run", "character"]):
                result["code"] = code_templates["character_movement"]
                result["instructions"] = "Character movement controller."
            elif any(w in prompt_lower for w in ["health", "hp", "damage", "hit"]):
                result["code"] = code_templates["health_system"]
                result["instructions"] = "Health system with damage and healing."
            elif any(w in prompt_lower for w in ["spawn", "instance", "create entity"]):
                result["code"] = code_templates["entity_spawner"]
                result["instructions"] = "Entity spawner."
            elif any(w in prompt_lower for w in ["ai", "enemy", "npc", "patrol", "chase"]):
                result["code"] = code_templates["ai_patrol"]
                result["instructions"] = "AI patrol/chase state machine."
            elif any(w in prompt_lower for w in ["inventory", "item", "pickup"]):
                result["code"] = code_templates["inventory_system"]
                result["instructions"] = "Inventory system."
            else:
                result["code"] = code_templates["basic_component"]
                result["instructions"] = "Basic O3DE component template."

        name = prompt.replace(" ", "_")[:30]
        ext = ".lua" if language == "lua" else ".py"
        output_path = os.path.join(CODE_DIR, f"{name}{ext}")
        os.makedirs(CODE_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(result["code"])

        result["output_path"] = output_path
        result["status"] = "generated"
        return result

    def _get_templates(self):
        return {
            "character_movement": '''-- O3DE Character Movement Component
-- Attach to entity with PhysX CharacterController

local CharacterMovement = {
    Properties = {
        Speed = { default = 5.0, description = "Movement speed" },
        SprintMultiplier = { default = 1.5, description = "Sprint speed multiplier" },
        JumpForce = { default = 8.0, description = "Jump force" },
        Gravity = { default = -9.81, description = "Gravity" },
    },
}

function CharacterMovement:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    self.tickCount = 0
    self.velocity = Vector3(0, 0, 0)
    self.isGrounded = true
    self.isSprinting = false
end

function CharacterMovement:OnDeactivate()
    self.tickHandler:Disconnect()
end

function CharacterMovement:OnTick(deltaTime, timePoint)
    self.tickCount = self.tickCount + 1
    local moveInput = Vector3(0, 0, 0)

    if InputDevice.IsKeyDown("keyboard_w") then moveInput = moveInput + Vector3(0, 1, 0) end
    if InputDevice.IsKeyDown("keyboard_s") then moveInput = moveInput + Vector3(0, -1, 0) end
    if InputDevice.IsKeyDown("keyboard_a") then moveInput = moveInput + Vector3(-1, 0, 0) end
    if InputDevice.IsKeyDown("keyboard_d") then moveInput = moveInput + Vector3(1, 0, 0) end

    self.isSprinting = InputDevice.IsKeyDown("keyboard_lshift")

    if moveInput:GetLength() > 0 then
        moveInput = moveInput:GetNormalized()
    end

    local speed = self.Properties.Speed
    if self.isSprinting then
        speed = speed * self.Properties.SprintMultiplier
    end

    self.velocity = Vector3(moveInput.x * speed, moveInput.y * speed, self.velocity.z)

    if not self.isGrounded then
        self.velocity = Vector3(self.velocity.x, self.velocity.y, self.velocity.z + self.Properties.Gravity * deltaTime)
    end

    if InputDevice.IsKeyDown("keyboard_space") and self.isGrounded then
        self.velocity = Vector3(self.velocity.x, self.velocity.y, self.Properties.JumpForce)
        self.isGrounded = false
    end

    TransformBus.Event.SetLocalTranslation(self.entityId, TransformBus.Event.GetLocalTranslation(self.entityId) + self.velocity * deltaTime)
end
''',
            "health_system": '''-- O3DE Health System Component

local HealthSystem = {
    Properties = {
        MaxHealth = { default = 100.0, description = "Maximum health" },
        RegenRate = { default = 0.0, description = "Health regen per second" },
        InvincibilityTime = { default = 0.5, description = "Seconds of invincibility after hit" },
    },
}

function HealthSystem:OnActivate()
    self.currentHealth = self.Properties.MaxHealth
    self.isAlive = true
    self.lastDamageTime = 0
    self.tickHandler = TickBus.Connect(self, 0)

    self.tickBusHandler = TickBus.Connect(self, 0)
end

function HealthSystem:OnDeactivate()
    self.tickHandler:Disconnect()
    self.tickBusHandler:Disconnect()
end

function HealthSystem:OnTick(deltaTime, timePoint)
    if self.isAlive and self.Properties.RegenRate > 0 then
        self:Heal(self.Properties.RegenRate * deltaTime)
    end
end

function HealthSystem:TakeDamage(amount, source)
    if not self.isAlive then return end

    local currentTime = TickBus.GetTimeAtTick(TickBus.GetTickCount())
    if currentTime - self.lastDamageTime < self.Properties.InvincibilityTime then
        return
    end

    self.currentHealth = math.max(0, self.currentHealth - amount)
    self.lastDamageTime = currentTime

    Debug.Log("Entity took " .. amount .. " damage. Health: " .. self.currentHealth)

    if self.currentHealth <= 0 then
        self.isAlive = false
        Debug.Log("Entity died!")
    end
end

function HealthSystem:Heal(amount)
    if not self.isAlive then return end
    self.currentHealth = math.min(self.Properties.MaxHealth, self.currentHealth + amount)
end

function HealthSystem:GetHealth()
    return self.currentHealth
end

function HealthSystem:GetHealthPercent()
    return self.currentHealth / self.Properties.MaxHealth
end
''',
            "entity_spawner": '''-- O3DE Entity Spawner Component

local EntitySpawner = {
    Properties = {
        PrefabPath = { default = "", description = "Path to prefab asset" },
        SpawnInterval = { default = 1.0, description = "Seconds between spawns" },
        MaxSpawns = { default = 10, description = "Maximum entities to spawn" },
        SpawnRadius = { default = 10.0, description = "Radius around spawn point" },
    },
}

function EntitySpawner:OnActivate()
    self.spawnCount = 0
    self.spawnedEntities = {}
    self.tickHandler = TickBus.Connect(self, 0)
    self.timeSinceLastSpawn = 0
end

function EntitySpawner:OnDeactivate()
    self.tickHandler:Disconnect()
    for _, entityId in ipairs(self.spawnedEntities) do
        if entityId and entityId:IsValid() then
            DynamicBus.ToolsRequestBus.Broadcast.RequestDeleteEntity(entityId)
        end
    end
end

function EntitySpawner:OnTick(deltaTime, timePoint)
    self.timeSinceLastSpawn = self.timeSinceLastSpawn + deltaTime

    if self.timeSinceLastSpawn >= self.Properties.SpawnInterval and self.spawnCount < self.Properties.MaxSpawns then
        self:SpawnEntity()
        self.timeSinceLastSpawn = 0
    end
end

function EntitySpawner:SpawnEntity()
    if self.Properties.PrefabPath == "" then
        Debug.Log("No prefab path set!")
        return nil
    end

    local spawnPos = TransformBus.Event.GetWorldTranslation(self.entityId)
    local offset = Vector3(
        math.random() * self.Properties.SpawnRadius * 2 - self.Properties.SpawnRadius,
        math.random() * self.Properties.SpawnRadius * 2 - self.Properties.SpawnRadius,
        0
    )
    local finalPos = spawnPos + offset

    local entityId = DynamicBus.ToolsRequestBus.Broadcast.RequestCreateEntity(self.Properties.PrefabPath, finalPos)

    if entityId and entityId:IsValid() then
        self.spawnCount = self.spawnCount + 1
        table.insert(self.spawnedEntities, entityId)
        Debug.Log("Spawned entity #" .. self.spawnCount .. " at " .. tostring(finalPos))
    end

    return entityId
end
''',
            "ai_patrol": '''-- O3DE AI Patrol/Chase State Machine

local AIPatrol = {
    Properties = {
        PatrolPoints = { default = {}, description = "List of patrol waypoints" },
        PatrolSpeed = { default = 3.0, description = "Patrol movement speed" },
        ChaseSpeed = { default = 6.0, description = "Chase movement speed" },
        DetectionRange = { default = 20.0, description = "Range to detect player" },
        LoseRange = { default = 30.0, description = "Range to lose player" },
        PatrolWaitTime = { default = 2.0, description = "Seconds to wait at each point" },
    },
}

function AIPatrol:OnActivate()
    self.state = "patrol"
    self.currentPatrolIndex = 1
    self.waitTimer = 0
    self.isWaiting = false
    self.targetEntityId = nil
    self.tickHandler = TickBus.Connect(self, 0)
end

function AIPatrol:OnDeactivate()
    self.tickHandler:Disconnect()
end

function AIPatrol:OnTick(deltaTime, timePoint)
    local myPos = TransformBus.Event.GetWorldTranslation(self.entityId)

    if self.state == "patrol" then
        self:PatrolTick(deltaTime, myPos)
        if self:DetectPlayer(myPos) then
            self.state = "chase"
            Debug.Log("AI: Player detected! Switching to chase.")
        end
    elseif self.state == "chase" then
        self:ChaseTick(deltaTime, myPos)
        if not self:DetectPlayer(myPos) then
            self.state = "patrol"
            Debug.Log("AI: Player lost. Returning to patrol.")
        end
    end
end

function AIPatrol:PatrolTick(deltaTime, myPos)
    if #self.Properties.PatrolPoints == 0 then return end

    if self.isWaiting then
        self.waitTimer = self.waitTimer - deltaTime
        if self.waitTimer <= 0 then
            self.isWaiting = false
            self.currentPatrolIndex = (self.currentPatrolIndex % #self.Properties.PatrolPoints) + 1
        end
        return
    end

    local target = self.Properties.PatrolPoints[self.currentPatrolIndex]
    local targetVec = Vector3(target.x, target.y, target.z)
    local direction = (targetVec - myPos):GetNormalized()
    local newPos = myPos + direction * self.Properties.PatrolSpeed * deltaTime

    TransformBus.Event.SetWorldTranslation(self.entityId, newPos)

    if (targetVec - myPos):GetLength() < 1.0 then
        self.isWaiting = true
        self.waitTimer = self.Properties.PatrolWaitTime
    end
end

function AIPatrol:ChaseTick(deltaTime, myPos)
    if not self.targetEntityId or not self.targetEntityId:IsValid() then return end

    local targetPos = TransformBus.Event.GetWorldTranslation(self.targetEntityId)
    local direction = (targetPos - myPos):GetNormalized()
    local newPos = myPos + direction * self.Properties.ChaseSpeed * deltaTime

    TransformBus.Event.SetWorldTranslation(self.entityId, newPos)
end

function AIPatrol:DetectPlayer(myPos)
    local playerEntities = TagGlobalRequestBus.Connect(self, "Player")
    if playerEntities then
        for _, playerId in ipairs(playerEntities) do
            if playerId and playerId:IsValid() then
                local playerPos = TransformBus.Event.GetWorldTranslation(playerId)
                local dist = (playerPos - myPos):GetLength()
                if dist < self.Properties.DetectionRange then
                    self.targetEntityId = playerId
                    return true
                end
            end
        end
    end
    return false
end
''',
            "inventory_system": '''-- O3DE Inventory System Component

local InventorySystem = {
    Properties = {
        MaxSlots = { default = 20, description = "Maximum inventory slots" },
    },
}

function InventorySystem:OnActivate()
    self.items = {}
    self.itemCount = 0
end

function InventorySystem:OnDeactivate()
end

function InventorySystem:AddItem(itemData)
    if self.itemCount >= self.Properties.MaxSlots then
        Debug.Log("Inventory full!")
        return false
    end

    for i, existing in ipairs(self.items) do
        if existing.id == itemData.id and existing.stackable then
            existing.count = existing.count + (itemData.count or 1)
            Debug.Log("Stacked " .. itemData.name .. " x" .. existing.count)
            return true
        end
    end

    itemData.count = itemData.count or 1
    table.insert(self.items, itemData)
    self.itemCount = self.itemCount + 1
    Debug.Log("Added " .. itemData.name .. " to inventory")
    return true
end

function InventorySystem:RemoveItem(itemId, count)
    count = count or 1
    for i, item in ipairs(self.items) do
        if item.id == itemId then
            item.count = item.count - count
            if item.count <= 0 then
                table.remove(self.items, i)
                self.itemCount = self.itemCount - 1
            end
            Debug.Log("Removed " .. item.name .. " x" .. count)
            return true
        end
    end
    return false
end

function InventorySystem:HasItem(itemId, count)
    count = count or 1
    for _, item in ipairs(self.items) do
        if item.id == itemId and item.count >= count then
            return true
        end
    end
    return false
end

function InventorySystem:GetItems()
    return self.items
end

function InventorySystem:GetItemCount()
    return self.itemCount
end
''',
            "basic_component": '''-- O3DE Basic Component Template

local BasicComponent = {
    Properties = {
        Enabled = { default = true, description = "Enable/disable this component" },
    },
}

function BasicComponent:OnActivate()
    Debug.Log("BasicComponent activated on entity: " .. tostring(self.entityId))
    self.tickHandler = TickBus.Connect(self, 0)
end

function BasicComponent:OnDeactivate()
    if self.tickHandler then
        self.tickHandler:Disconnect()
    end
end

function BasicComponent:OnTick(deltaTime, timePoint)
    if not self.Properties.Enabled then return end
end
''',
        }


class AnimationGenerator:
    """Generates animations using AI tools."""

    def generate(self, prompt, params):
        anim_type = params.get("type", "motion")

        result = {
            "prompt": prompt,
            "type": anim_type,
            "pipeline": [],
            "output_path": None,
        }

        ganimator_path = os.path.join(AI_TOOLS_ROOT, "GANimator")
        deepmotion_path = os.path.join(AI_TOOLS_ROOT, "DeepMotionEditing")

        if os.path.exists(ganimator_path):
            result["pipeline"].append({
                "tool": "GANimator",
                "method": "motion_synthesis",
                "config": {
                    "prompt": prompt,
                    "input_sequence": params.get("input_bvh", ""),
                    "applications": ["novel_motion", "style_transfer", "interactive"],
                }
            })

        if os.path.exists(deepmotion_path):
            result["pipeline"].append({
                "tool": "DeepMotionEditing",
                "method": "retargeting",
                "config": {
                    "prompt": prompt,
                    "source_skeleton": params.get("source_skeleton", "mixamo"),
                    "target_skeleton": params.get("target_skeleton", "mixamo"),
                    "foot_skate_cleanup": True,
                }
            })

        name = prompt.replace(" ", "_")[:30]
        output_path = os.path.join(ANIMATIONS_DIR, f"{name}.json")
        os.makedirs(ANIMATIONS_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        result["output_path"] = output_path
        result["status"] = "configured"
        return result


class AudioGenerator:
    """Generates audio using AI tools."""

    def generate(self, prompt, params):
        audio_type = params.get("type", "tts")

        result = {
            "prompt": prompt,
            "type": audio_type,
            "pipeline": [],
            "output_path": None,
        }

        elevenlabs_path = os.path.join(AI_TOOLS_ROOT, "ElevenLabsClone")
        inworld_path = os.path.join(AI_TOOLS_ROOT, "InworldAI")

        if os.path.exists(elevenlabs_path):
            result["pipeline"].append({
                "tool": "ElevenLabsClone",
                "method": audio_type,
                "config": {
                    "text": prompt,
                    "voice": params.get("voice", "default"),
                    "speed": params.get("speed", 1.0),
                }
            })

        if os.path.exists(inworld_path):
            result["pipeline"].append({
                "tool": "InworldAI",
                "method": "realtime_speech",
                "config": {
                    "text": prompt,
                    "language": params.get("language", "en"),
                }
            })

        name = prompt.replace(" ", "_")[:30]
        output_path = os.path.join(AUDIO_DIR, f"{name}.json")
        os.makedirs(AUDIO_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        result["output_path"] = output_path
        result["status"] = "configured"
        return result


class BlueprintGenerator:
    """Generates ScriptCanvas/Node-based blueprints."""

    def generate(self, prompt, params):
        bp_type = params.get("type", "script_canvas")

        result = {
            "prompt": prompt,
            "type": bp_type,
            "nodes": [],
            "connections": [],
            "output_path": None,
        }

        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["door", "gate", "open", "close"]):
            result["nodes"] = [
                {"id": 1, "type": "TriggerArea", "name": "PlayerDetector", "position": [0, 0]},
                {"id": 2, "type": "ScriptCanvas", "name": "DoorLogic", "position": [300, 0]},
                {"id": 3, "type": "Transform", "name": "DoorMove", "position": [600, 0]},
                {"id": 4, "type": "Audio", "name": "DoorSound", "position": [600, 200]},
            ]
            result["connections"] = [
                {"from": 1, "fromOutput": "OnEntityEntered", "to": 2, "toInput": "Open"},
                {"from": 2, "fromOutput": "IsOpen", "to": 3, "toInput": "SetTranslation"},
                {"from": 2, "fromOutput": "IsOpen", "to": 4, "toInput": "Play"},
            ]
        elif any(w in prompt_lower for w in ["light", "lamp", "flicker"]):
            result["nodes"] = [
                {"id": 1, "type": "ScriptCanvas", "name": "FlickerTimer", "position": [0, 0]},
                {"id": 2, "type": "Light", "name": "PointLight", "position": [300, 0]},
                {"id": 3, "type": "ScriptCanvas", "name": "RandomIntensity", "position": [300, 200]},
            ]
            result["connections"] = [
                {"from": 1, "fromOutput": "OnTick", "to": 3, "toInput": "Calculate"},
                {"from": 3, "fromOutput": "Intensity", "to": 2, "toInput": "SetIntensity"},
            ]
        else:
            result["nodes"] = [
                {"id": 1, "type": "ScriptCanvas", "name": "InputNode", "position": [0, 0]},
                {"id": 2, "type": "ScriptCanvas", "name": "LogicNode", "position": [300, 0]},
                {"id": 3, "type": "Output", "name": "OutputNode", "position": [600, 0]},
            ]
            result["connections"] = [
                {"from": 1, "fromOutput": "OnActivate", "to": 2, "toInput": "Process"},
                {"from": 2, "fromOutput": "Result", "to": 3, "toInput": "Set"},
            ]

        name = prompt.replace(" ", "_")[:30]
        output_path = os.path.join(CODE_DIR, f"{name}_blueprint.json")
        os.makedirs(CODE_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        result["output_path"] = output_path
        result["status"] = "generated"
        return result


# ============================================================
# Worker Thread for AI Generation
# ============================================================

class AIGenerationWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, backend, tool_name, prompt, params=None):
        super().__init__()
        self.backend = backend
        self.tool_name = tool_name
        self.prompt = prompt
        self.params = params or {}

    def run(self):
        try:
            self.progress.emit(f"Generating {self.tool_name}...")
            result = self.backend.generate(self.tool_name, self.prompt, self.params)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"Error: {str(e)}\n{traceback.format_exc()}")


# ============================================================
# O3DE Integration - Apply AI results to the engine
# ============================================================

class O3DEIntegration:
    """Applies AI-generated content directly into the O3DE editor."""

    @staticmethod
    def apply_terrain(terrain_config):
        try:
            entity_id = DynamicBus.ToolsRequestBus.Broadcast.RequestCreateEntity("AI_Terrain_" + terrain_config.get("name", "unknown"))
            if entity_id and entity_id.IsValid():
                editor.EditorEntityAPIBus.Broadcast.AddComponent(entity_id, "TerrainWorldComponent")
                editor.EditorEntityAPIBus.Broadcast.AddComponent(entity_id, "TerrainLayerSpawnerComponent")
                editor.EditorEntityAPIBus.Broadcast.AddComponent(entity_id, "TerrainHeightGradientListComponent")

                config = terrain_config.get("o3de_config", {})
                terrain_world = config.get("terrain_world", {})
                if terrain_world:
                    component_id = editor.EditorEntityAPIBus.Broadcast.FindComponentTypeById("TerrainWorldComponent")
                    if component_id:
                        editor.EditorEntityAPIBus.Broadcast.SetComponentProperty(
                            entity_id, component_id, "Configuration|Min Height",
                            terrain_world.get("min_height", -50)
                        )
                        editor.EditorEntityAPIBus.Broadcast.SetComponentProperty(
                            entity_id, component_id, "Configuration|Max Height",
                            terrain_world.get("max_height", 1000)
                        )

                return {"status": "applied", "entity_id": str(entity_id)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "error", "error": "Failed to create entity"}

    @staticmethod
    def apply_model(model_config):
        try:
            path = model_config.get("output_path", "")
            if path and os.path.exists(path):
                return {"status": "ready", "message": f"Model pipeline configured. Assets will be auto-processed to: {MODELS_DIR}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "error", "error": "No output path"}

    @staticmethod
    def apply_code(code_config):
        try:
            path = code_config.get("output_path", "")
            if path and os.path.exists(path):
                with open(path, "r") as f:
                    code = f.read()
                return {"status": "ready", "code": code, "path": path}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "error", "error": "No code generated"}


# ============================================================
# Chat History Widget
# ============================================================

class ChatMessage(QFrame):
    def __init__(self, role, text, parent=None):
        super().__init__(parent)
        self.role = role

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        if role == "user":
            self.setStyleSheet("ChatMessage { background-color: #2b2b3d; border-radius: 8px; margin: 2px 40px 2px 4px; }")
        else:
            self.setStyleSheet("ChatMessage { background-color: #1e3a1e; border-radius: 8px; margin: 2px 4px 2px 40px; }")

        role_label = QLabel("You" if role == "user" else "AI")
        role_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        role_label.setFixedWidth(30)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #ddd; font-size: 12px;")
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(role_label)
        layout.addWidget(text_label, 1)


# ============================================================
# Main AI Sidebar Panel
# ============================================================

class AISidebarPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Design Studio")
        self.setMinimumSize(420, 600)
        self.resize(450, 700)

        self.backend = AIBackend()
        self.integration = O3DEIntegration()
        self.orchestrator = FullGameOrchestrator() if HAS_ORCHESTRATOR else None
        self.current_worker = None
        self.chat_history = []

        self._setup_ui()
        self._apply_stylesheet()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self._create_header()
        main_layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.tabs.addTab(self._create_chat_tab(), "Chat")
        self.tabs.addTab(self._create_terrain_tab(), "Terrain")
        self.tabs.addTab(self._create_assets_tab(), "Assets")
        self.tabs.addTab(self._create_code_tab(), "Code")
        self.tabs.addTab(self._create_animation_tab(), "Anim")
        self.tabs.addTab(self._create_audio_tab(), "Audio")
        self.tabs.addTab(self._create_settings_tab(), "Settings")

        main_layout.addWidget(self.tabs, 1)

        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #1a1a2e; border-bottom: 2px solid #0f3460; padding: 8px; }")
        layout = QHBoxLayout(header)

        title = QLabel("AI Design Studio")
        title.setStyleSheet("color: #e94560; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(title)

        subtitle = QLabel("| Vibe Code Your Game")
        subtitle.setStyleSheet("color: #888; font-size: 11px; border: none;")
        layout.addWidget(subtitle)
        layout.addStretch()

        return header

    def _create_chat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        self.chat_area = QVBoxLayout()
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; background-color: #16162a; }")
        self.chat_container = QWidget()
        self.chat_container.setLayout(self.chat_area)
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-top: 1px solid #333; padding: 4px; }")
        input_layout = QHBoxLayout(input_frame)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Describe what you want to create... (Enter to send, Shift+Enter for new line)")
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setStyleSheet("QTextEdit { background-color: #2b2b3d; color: #fff; border: 1px solid #444; border-radius: 6px; padding: 6px; }")
        self.chat_input.installEventFilter(self)
        input_layout.addWidget(self.chat_input, 1)

        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(60)
        send_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        send_btn.clicked.connect(self._on_send_chat)
        input_layout.addWidget(send_btn)

        layout.addWidget(input_frame)

        # Full Game Generation Button
        full_game_frame = QFrame()
        full_game_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-top: 1px solid #333; padding: 4px; }")
        full_game_layout = QHBoxLayout(full_game_frame)
        full_game_layout.setContentsMargins(4, 2, 4, 2)

        full_game_btn = QPushButton("FULL GAME - One Prompt")
        full_game_btn.setFixedHeight(36)
        full_game_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e94560, stop:1 #9b59b6);
                color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b81, stop:1 #af6acd); }
        """)
        full_game_btn.clicked.connect(self._on_full_game_generate)
        full_game_layout.addWidget(full_game_btn)

        layout.addWidget(full_game_frame)

        quick_actions = QFrame()
        quick_layout = QHBoxLayout(quick_actions)
        quick_layout.setContentsMargins(4, 2, 4, 2)

        for text, slot in [
            ("Mountain", lambda: self._quick_prompt("Create a mountain terrain with snow peaks and forest valleys")),
            ("Forest", lambda: self._quick_prompt("Generate a dense forest terrain with rivers and clearings")),
            ("Desert", lambda: self._quick_prompt("Create a vast desert terrain with sand dunes and oases")),
            ("City", lambda: self._quick_prompt("Generate a flat terrain suitable for a city with roads")),
            ("Island", lambda: self._quick_prompt("Create a volcanic island terrain with beaches and jungle")),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(24)
            btn.setStyleSheet("QPushButton { background-color: #0f3460; color: #aaa; border: none; border-radius: 4px; font-size: 10px; } QPushButton:hover { background-color: #16213e; color: #fff; }")
            btn.clicked.connect(slot)
            quick_layout.addWidget(btn)

        layout.addWidget(quick_actions)

        return widget

    def _create_terrain_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Terrain Generation")
        group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        form = QFormLayout()

        self.terrain_prompt = QTextEdit()
        self.terrain_prompt.setPlaceholderText("Describe your terrain... e.g., 'volcanic island with lava rivers and obsidian cliffs'")
        self.terrain_prompt.setMaximumHeight(80)
        form.addRow("Description:", self.terrain_prompt)

        self.terrain_size = QComboBox()
        self.terrain_size.addItems(["512x512", "1024x1024", "2048x2048", "4096x4096"])
        self.terrain_size.setCurrentIndex(2)
        form.addRow("Resolution:", self.terrain_size)

        self.terrain_seed = QLineEdit(str(int(time.time()) % 100000))
        form.addRow("Seed:", self.terrain_seed)

        generate_terrain_btn = QPushButton("Generate Terrain")
        generate_terrain_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        generate_terrain_btn.clicked.connect(self._on_generate_terrain)
        form.addRow(generate_terrain_btn)

        apply_terrain_btn = QPushButton("Apply to Scene")
        apply_terrain_btn.setStyleSheet("QPushButton { background-color: #0f3460; color: white; padding: 8px; border-radius: 6px; } QPushButton:hover { background-color: #16213e; }")
        apply_terrain_btn.clicked.connect(self._on_apply_terrain)
        form.addRow(apply_terrain_btn)

        group.setLayout(form)
        layout.addWidget(group)

        self.terrain_preview = QLabel("Terrain preview will appear here")
        self.terrain_preview.setAlignment(Qt.AlignCenter)
        self.terrain_preview.setMinimumHeight(150)
        self.terrain_preview.setStyleSheet("QLabel { background-color: #16162a; border: 1px dashed #444; color: #666; border-radius: 6px; }")
        layout.addWidget(self.terrain_preview)

        layout.addStretch()
        return widget

    def _create_assets_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("3D Asset Generation")
        group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        form = QFormLayout()

        self.asset_prompt = QTextEdit()
        self.asset_prompt.setPlaceholderText("Describe the 3D model... e.g., 'rusty medieval sword with gem inlay'")
        self.asset_prompt.setMaximumHeight(80)
        form.addRow("Description:", self.asset_prompt)

        self.asset_type = QComboBox()
        self.asset_type.addItems(["Character", "Prop", "Vehicle", "Building", "Nature", "Weapon", "Armor", "Furniture"])
        form.addRow("Type:", self.asset_type)

        self.asset_style = QComboBox()
        self.asset_style.addItems(["Realistic", "Stylized", "Low Poly", "Cartoon", "Sci-Fi", "Fantasy"])
        form.addRow("Style:", self.asset_style)

        self.texture_res = QComboBox()
        self.texture_res.addItems(["256", "512", "1024", "2048", "4096"])
        self.texture_res.setCurrentIndex(2)
        form.addRow("Texture Res:", self.texture_res)

        gen_asset_btn = QPushButton("Generate 3D Asset")
        gen_asset_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        gen_asset_btn.clicked.connect(self._on_generate_asset)
        form.addRow(gen_asset_btn)

        group.setLayout(form)
        layout.addWidget(group)

        tex_group = QGroupBox("Texture Generation")
        tex_group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        tex_form = QFormLayout()

        self.tex_prompt = QTextEdit()
        self.tex_prompt.setPlaceholderText("Describe the texture... e.g., 'weathered stone brick with moss'")
        self.tex_prompt.setMaximumHeight(60)
        tex_form.addRow("Description:", self.tex_prompt)

        self.tex_type = QComboBox()
        self.tex_type.addItems(["Diffuse", "Normal", "Roughness", "PBR Set", "Height Map"])
        tex_form.addRow("Type:", self.tex_type)

        self.tex_tileable = QtWidgets.QCheckBox("Tileable")
        self.tex_tileable.setChecked(True)
        tex_form.addRow("", self.tex_tileable)

        gen_tex_btn = QPushButton("Generate Texture")
        gen_tex_btn.setStyleSheet("QPushButton { background-color: #0f3460; color: white; padding: 8px; border-radius: 6px; } QPushButton:hover { background-color: #16213e; }")
        gen_tex_btn.clicked.connect(self._on_generate_texture)
        tex_form.addRow(gen_tex_btn)

        tex_group.setLayout(tex_form)
        layout.addWidget(tex_group)

        layout.addStretch()
        return widget

    def _create_code_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Code Generation")
        group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        form = QFormLayout()

        self.code_prompt = QTextEdit()
        self.code_prompt.setPlaceholderText("Describe what you need... e.g., 'create a health system with damage and regen'")
        self.code_prompt.setMaximumHeight(80)
        form.addRow("Description:", self.code_prompt)

        self.code_lang = QComboBox()
        self.code_lang.addItems(["Lua", "Python", "ScriptCanvas"])
        form.addRow("Language:", self.code_lang)

        self.code_category = QComboBox()
        self.code_category.addItems(["Gameplay", "AI", "UI", "Physics", "Audio", "Network", "Custom"])
        form.addRow("Category:", self.code_category)

        gen_code_btn = QPushButton("Generate Code")
        gen_code_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        gen_code_btn.clicked.connect(self._on_generate_code)
        form.addRow(gen_code_btn)

        bp_gen_btn = QPushButton("Generate Blueprint")
        bp_gen_btn.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #af6acd; }")
        bp_gen_btn.clicked.connect(self._on_generate_blueprint)
        form.addRow(bp_gen_btn)

        group.setLayout(form)
        layout.addWidget(group)

        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setStyleSheet("QPlainTextEdit { background-color: #1e1e2e; color: #a6e3a1; border: 1px solid #333; border-radius: 6px; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }")
        self.code_preview.setPlaceholderText("Generated code will appear here...")
        layout.addWidget(self.code_preview, 1)

        return widget

    def _create_animation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Animation Generation")
        group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        form = QFormLayout()

        self.anim_prompt = QTextEdit()
        self.anim_prompt.setPlaceholderText("Describe the animation... e.g., 'character walking cycle with weapon drawn'")
        self.anim_prompt.setMaximumHeight(80)
        form.addRow("Description:", self.anim_prompt)

        self.anim_type = QComboBox()
        self.anim_type.addItems(["Motion Synthesis", "Style Transfer", "Retargeting", "Keyframe Edit", "Procedural"])
        form.addRow("Type:", self.anim_type)

        gen_anim_btn = QPushButton("Generate Animation")
        gen_anim_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        gen_anim_btn.clicked.connect(self._on_generate_animation)
        form.addRow(gen_anim_btn)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        return widget

    def _create_audio_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Audio Generation")
        group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        form = QFormLayout()

        self.audio_prompt = QTextEdit()
        self.audio_prompt.setPlaceholderText("Describe the audio... e.g., 'narrator voice saying: Welcome to the dungeon'")
        self.audio_prompt.setMaximumHeight(80)
        form.addRow("Description:", self.audio_prompt)

        self.audio_type = QComboBox()
        self.audio_type.addItems(["Text-to-Speech", "Voice Conversion", "Sound Effect", "Music", "Ambient"])
        form.addRow("Type:", self.audio_type)

        gen_audio_btn = QPushButton("Generate Audio")
        gen_audio_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        gen_audio_btn.clicked.connect(self._on_generate_audio)
        form.addRow(gen_audio_btn)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        return widget

    def _create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # OpenRouter Free Models Group
        llm_group = QGroupBox("LLM Settings (OpenRouter Free Models)")
        llm_group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        llm_form = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-... (OpenRouter API key)")
        current_key = os.environ.get("OPENROUTER_API_KEY", "")
        if current_key:
            self.api_key_input.setText(current_key)
        llm_form.addRow("API Key:", self.api_key_input)

        self.model_selector = QComboBox()
        for name, model_id in FREE_MODELS.items():
            self.model_selector.addItem(f"{name} ({model_id})", model_id)
        llm_form.addRow("Free Model:", self.model_selector)

        self.auto_apply = QtWidgets.QCheckBox("Auto-apply generated content to scene")
        self.auto_apply.setChecked(False)
        llm_form.addRow("", self.auto_apply)

        save_llm_btn = QPushButton("Save LLM Settings")
        save_llm_btn.setStyleSheet("QPushButton { background-color: #e94560; color: white; padding: 8px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #ff6b81; }")
        save_llm_btn.clicked.connect(self._on_save_llm_settings)
        llm_form.addRow(save_llm_btn)

        llm_group.setLayout(llm_form)
        layout.addWidget(llm_group)

        # AI Tools Group
        tools_group = QGroupBox("AI Generation Tools")
        tools_group.setStyleSheet("QGroupBox { color: #e94560; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 16px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        tools_form = QFormLayout()

        self.terrain_tool = QComboBox()
        self.terrain_tool.addItems(["ProceduralTerrains (Local)", "Gaea API", "World Machine API", "Custom Script"])
        tools_form.addRow("Terrain Tool:", self.terrain_tool)

        self.model_tool = QComboBox()
        self.model_tool.addItems(["Hunyuan3D", "Dust3D", "Meshy API", "Tripo API", "Custom"])
        tools_form.addRow("3D Model Tool:", self.model_tool)

        self.texture_tool = QComboBox()
        self.texture_tool.addItems(["ComfyUI (Local)", "Stable Diffusion", "DALL-E API", "Custom"])
        tools_form.addRow("Texture Tool:", self.texture_tool)

        self.anim_tool = QComboBox()
        self.anim_tool.addItems(["GANimator", "DeepMotionEditing", "Mixamo API", "Custom"])
        tools_form.addRow("Animation Tool:", self.anim_tool)

        save_tools_btn = QPushButton("Save Tool Settings")
        save_tools_btn.setStyleSheet("QPushButton { background-color: #0f3460; color: white; padding: 8px; border-radius: 6px; } QPushButton:hover { background-color: #16213e; }")
        save_tools_btn.clicked.connect(self._on_save_settings)
        tools_form.addRow(save_tools_btn)

        tools_group.setLayout(tools_form)
        layout.addWidget(tools_group)

        # Status info
        info_label = QLabel("Free models: 20 req/min, 50 req/day (1000 with $10 credits). Models: auto, nemotron-ultra, gemma-4, gpt-oss, llama-3.3, dots3, laguna-s")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 8px;")
        layout.addWidget(info_label)

        layout.addStretch()
        return widget

    def _create_status_bar(self):
        status = QFrame()
        status.setStyleSheet("QFrame { background-color: #1a1a2e; border-top: 1px solid #333; padding: 4px; }")
        layout = QHBoxLayout(status)
        layout.setContentsMargins(8, 2, 8, 2)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #333; border-radius: 4px; background-color: #16162a; } QProgressBar::chunk { background-color: #e94560; border-radius: 3px; }")
        layout.addWidget(self.progress_bar)

        tools_label = QLabel("Tools: " + ", ".join([
            "ProceduralTerrains", "Hunyuan3D", "Dust3D", "GANimator",
            "DeepMotionEditing", "ComfyUI", "ElevenLabsClone", "AutoGen"
        ]))
        tools_label.setStyleSheet("color: #555; font-size: 9px;")
        layout.addWidget(tools_label, 1)

        return status

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog { background-color: #16162a; }
            QTabWidget::pane { border: 1px solid #333; background-color: #16162a; }
            QTabBar::tab { background-color: #1a1a2e; color: #888; padding: 8px 12px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #0f3460; color: #fff; }
            QTabBar::tab:hover { background-color: #16213e; color: #ccc; }
            QLabel { color: #ccc; }
            QLineEdit { background-color: #2b2b3d; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 4px; }
            QComboBox { background-color: #2b2b3d; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 4px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #2b2b3d; color: #fff; selection-background-color: #0f3460; }
            QGroupBox { color: #e94560; }
            QScrollArea { border: none; }
            QWidget { background-color: transparent; }
        """)

    def _add_chat_message(self, role, text):
        msg = ChatMessage(role, text)
        self.chat_area.addWidget(msg)
        self.chat_history.append({"role": role, "text": text})
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def eventFilter(self, obj, event):
        if obj == self.chat_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self._on_send_chat()
                return True
        return super().eventFilter(obj, event)

    def _on_send_chat(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return

        self._add_chat_message("user", text)
        self.chat_input.clear()

        tool_name = self._detect_tool_from_prompt(text)
        params = self._detect_params_from_prompt(text)

        self._run_generation(tool_name, text, params)

    def _on_full_game_generate(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            text = "Create a full RPG game with fantasy terrain, characters, weapons, inventory, dialogue, and music"
            self._add_chat_message("user", text)
        else:
            self._add_chat_message("user", f"[FULL GAME] {text}")
        self.chat_input.clear()

        if not self.orchestrator:
            self._add_chat_message("ai", "Full game orchestrator not available. Using individual generators instead.")
            tool_name = self._detect_tool_from_prompt(text)
            params = self._detect_params_from_prompt(text)
            self._run_generation(tool_name, text, params)
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Generating full game... This may take a moment.")
        self._add_chat_message("ai", "Starting full game generation pipeline...\nAnalyzing your prompt and generating: terrain, models, textures, code, systems, animations, audio, and blueprints...")

        self.full_game_worker = AIGenerationWorker(self.backend, "full_game", text, {})
        self.full_game_worker.finished.connect(lambda result: self._on_full_game_complete(result))
        self.full_game_worker.error.connect(self._on_generation_error)

        import threading
        def run_full_game():
            try:
                result = self.orchestrator.generate_full_game(text)
                self.full_game_worker.finished.emit(result)
            except Exception as e:
                self.full_game_worker.error.emit(str(e))

        self.full_game_thread = threading.Thread(target=run_full_game)
        self.full_game_thread.daemon = True
        self.full_game_thread.start()

    def _on_full_game_complete(self, result):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Full game generation complete!")
        summary = result.get("summary", "Generation complete")
        self._add_chat_message("ai", summary)

        # Show generated file count
        tasks = result.get("tasks", [])
        total_files = 0
        for t in tasks:
            if t.get("files"):
                total_files += len(t["files"])
            if t.get("models"):
                total_files += len(t["models"])
            if t.get("textures"):
                total_files += len(t["textures"])

        self._add_chat_message("ai", f"Generated {len(tasks)} systems with ~{total_files} files.\nAll output saved to: {result.get('assets_root', 'N/A')}\n\nTo use: Open the AIProject/Assets folder and drag files into your O3DE project, or use the individual tabs to refine specific assets.")

    def _detect_tool_from_prompt(self, prompt):
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["terrain", "landscape", "heightmap", "mountain", "valley", "hill", "desert", "forest", "island", "canyon"]):
            return "terrain"
        elif any(w in prompt_lower for w in ["model", "mesh", "3d", "object", "character", "prop", "weapon", "armor", "building"]):
            return "model_3d"
        elif any(w in prompt_lower for w in ["texture", "material", "surface", "pattern"]):
            return "texture"
        elif any(w in prompt_lower for w in ["code", "script", "function", "component", "lua", "python", "blueprint", "node"]):
            return "code"
        elif any(w in prompt_lower for w in ["animation", "animate", "walk", "run", "idle", "attack", "motion", "skeleton"]):
            return "animation"
        elif any(w in prompt_lower for w in ["audio", "sound", "voice", "music", "narrator", "sfx", "ambient"]):
            return "audio"
        elif any(w in prompt_lower for w in ["blueprint", "node graph", "script canvas", "wire", "connect"]):
            return "blueprint"
        return "code"

    def _detect_params_from_prompt(self, prompt):
        params = {}
        prompt_lower = prompt.lower()

        if any(w in prompt_lower for w in ["realistic"]):
            params["style"] = "realistic"
        elif any(w in prompt_lower for w in ["stylized", "cartoon"]):
            params["style"] = "stylized"
        elif any(w in prompt_lower for w in ["low poly"]):
            params["style"] = "low_poly"

        if "seed" in prompt_lower:
            import re
            seed_match = re.search(r'seed\s*[=:]\s*(\d+)', prompt_lower)
            if seed_match:
                params["seed"] = int(seed_match.group(1))

        return params

    def _run_generation(self, tool_name, prompt, params):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Generating {tool_name}...")

        self.current_worker = AIGenerationWorker(self.backend, tool_name, prompt, params)
        self.current_worker.finished.connect(lambda result: self._on_generation_complete(tool_name, result))
        self.current_worker.error.connect(self._on_generation_error)
        self.current_worker.start()

    def _on_generation_complete(self, tool_name, result):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Generation complete")

        status = result.get("status", "unknown")
        if status in ["generated", "pipeline_configured", "configured", "ready", "applied"]:
            summary = self._format_result_summary(tool_name, result)
            self._add_chat_message("ai", summary)

            if tool_name == "code" and "code" in result:
                self.code_preview.setPlainText(result["code"])
                self.tabs.setCurrentIndex(3)

            if tool_name == "terrain":
                self.tabs.setCurrentIndex(1)

            if self.auto_apply.isChecked():
                self._auto_apply_result(tool_name, result)
        else:
            self._add_chat_message("ai", f"Generation completed with status: {status}")

    def _on_generation_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error occurred")
        self._add_chat_message("ai", f"Error: {error_msg}")

    def _format_result_summary(self, tool_name, result):
        lines = [f"**{tool_name.replace('_', ' ').title()} Generated**\n"]

        if tool_name == "terrain":
            lines.append(f"Biome: {result.get('biome', 'unknown')}")
            lines.append(f"Height range: {result.get('height_range', {})}")
            lines.append(f"Erosion: {result.get('erosion', {})}")
            if result.get("features"):
                lines.append(f"Features: {', '.join(result['features'])}")
            lines.append(f"Output: {result.get('output_path', 'N/A')}")

        elif tool_name == "model_3d":
            lines.append(f"Style: {result.get('style', 'default')}")
            lines.append(f"Pipeline steps: {len(result.get('pipeline', []))}")
            for step in result.get("pipeline", []):
                lines.append(f"  - {step['tool']}: {step['method']}")
            lines.append(f"Output: {result.get('output_path', 'N/A')}")

        elif tool_name == "code":
            lines.append(f"Language: {result.get('language', 'lua')}")
            lines.append(f"Instructions: {result.get('instructions', '')}")
            lines.append(f"Output: {result.get('output_path', 'N/A')}")

        elif tool_name == "texture":
            lines.append(f"Resolution: {result.get('resolution', 1024)}")
            lines.append(f"Tileable: {result.get('tileable', True)}")
            maps = result.get("maps", {})
            active_maps = [k for k, v in maps.items() if v]
            lines.append(f"Maps: {', '.join(active_maps)}")

        elif tool_name == "animation":
            lines.append(f"Type: {result.get('type', 'motion')}")
            lines.append(f"Pipeline tools: {len(result.get('pipeline', []))}")

        elif tool_name == "audio":
            lines.append(f"Type: {result.get('type', 'tts')}")
            lines.append(f"Pipeline tools: {len(result.get('pipeline', []))}")

        return "\n".join(lines)

    def _auto_apply_result(self, tool_name, result):
        if tool_name == "terrain":
            self._on_apply_terrain()

    # ---- Button handlers ----

    def _on_generate_terrain(self):
        prompt = self.terrain_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate a terrain"
        size_text = self.terrain_size.currentText()
        size = int(size_text.split("x")[0])
        seed = int(self.terrain_seed.text() or "42")
        self._run_generation("terrain", prompt, {"size": size, "seed": seed})

    def _on_apply_terrain(self):
        self.status_label.setText("Applying terrain to scene...")
        result = self.integration.apply_terrain({"name": "last_generated"})
        self.status_label.setText(f"Terrain: {result.get('status', 'error')}")

    def _on_generate_asset(self):
        prompt = self.asset_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate a 3D model"
        params = {
            "style": self.asset_style.currentText().lower().replace(" ", "_"),
            "poly_count": "medium",
        }
        self._run_generation("model_3d", prompt, params)

    def _on_generate_texture(self):
        prompt = self.tex_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate a texture"
        params = {
            "type": self.tex_type.currentText().lower(),
            "tileable": self.tex_tileable.isChecked(),
            "resolution": int(self.texture_res.currentText()),
        }
        self._run_generation("texture", prompt, params)

    def _on_generate_code(self):
        prompt = self.code_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate a basic component"
        params = {
            "language": self.code_lang.currentText().lower(),
            "category": self.code_category.currentText().lower(),
        }
        self._run_generation("code", prompt, params)

    def _on_generate_blueprint(self):
        prompt = self.code_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate a blueprint"
        self._run_generation("blueprint", prompt, {"type": "script_canvas"})

    def _on_generate_animation(self):
        prompt = self.anim_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate an animation"
        params = {"type": self.anim_type.currentText().lower().replace(" ", "_")}
        self._run_generation("animation", prompt, params)

    def _on_generate_audio(self):
        prompt = self.audio_prompt.toPlainText().strip()
        if not prompt:
            prompt = "Generate audio"
        params = {"type": self.audio_type.currentText().lower().replace("-", "_").replace(" ", "_")}
        self._run_generation("audio", prompt, params)

    def _on_save_llm_settings(self):
        global OPENROUTER_API_KEY
        api_key = self.api_key_input.text().strip()
        if api_key:
            OPENROUTER_API_KEY = api_key
            os.environ["OPENROUTER_API_KEY"] = api_key
        model_id = self.model_selector.currentData()
        if model_id:
            FREE_MODELS["active"] = model_id
        settings = QSettings("AIDesignStudio", "O3DESidebar")
        settings.setValue("openrouter_api_key", api_key)
        settings.setValue("active_model", model_id)
        self.status_label.setText(f"LLM settings saved. Model: {model_id}")

    def _on_save_settings(self):
        settings = QSettings("AIDesignStudio", "O3DESidebar")
        settings.setValue("terrain_tool", self.terrain_tool.currentText())
        settings.setValue("model_tool", self.model_tool.currentText())
        settings.setValue("texture_tool", self.texture_tool.currentText())
        settings.setValue("anim_tool", self.anim_tool.currentText())
        self.status_label.setText("Tool settings saved")

    def _quick_prompt(self, prompt):
        self.chat_input.setPlainText(prompt)
        self._on_send_chat()


# ============================================================
# Registration - Called by bootstrap.py
# ============================================================

def register_ai_sidebar():
    """Register the AI Design Studio panel with the O3DE editor."""
    try:
        import az_qt_helpers
        az_qt_helpers.register_view_pane('AI Design Studio', AISidebarPanel, category="AI Tools")
        print("AI Design Studio registered successfully!")
    except Exception as e:
        print(f"Failed to register AI Design Studio: {e}")


# Auto-register when imported
try:
    register_ai_sidebar()
except:
    pass
