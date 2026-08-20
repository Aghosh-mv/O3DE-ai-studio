"""
Full Game Orchestrator - Chains AI tools to generate complete game systems from one prompt.
"""
import os, sys, json, time, traceback
from typing import Dict, List, Any

AI_TOOLS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, AI_TOOLS_ROOT)

try:
    from o3de_knowledge import O3DE_KNOWLEDGE
except ImportError:
    from AISidebar.o3de_knowledge import O3DE_KNOWLEDGE


class FullGameOrchestrator:
    def __init__(self):
        self.output_root = os.path.join(AI_TOOLS_ROOT, "AIProject")
        self.assets_root = os.path.join(self.output_root, "Assets")
        self.generation_log = []
        for d in ["Code", "Models", "Textures", "Terrains", "Audio", "Animations", "Prefabs", "Materials", "Scripts"]:
            os.makedirs(os.path.join(self.assets_root, d), exist_ok=True)

    def generate_full_game(self, prompt: str) -> Dict:
        self.generation_log = []
        results = {"prompt": prompt, "tasks": [], "output_root": self.output_root, "assets_root": self.assets_root, "status": "in_progress"}
        try:
            plan = self._analyze_prompt(prompt)
            results["plan"] = plan
            for task in plan["tasks"]:
                task_result = self._execute_task(task, prompt)
                results["tasks"].append(task_result)
                self.generation_log.append({"task": task["type"], "status": task_result.get("status", "unknown"), "output": task_result.get("output_path", "")})
            results["status"] = "completed"
            results["summary"] = self._generate_summary(results)
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
        return results

    def _analyze_prompt(self, prompt: str) -> Dict:
        plan = {"tasks": [], "game_type": "unknown", "complexity": "medium"}
        p = prompt.lower()
        # Game type detection
        type_map = {"rpg": ["rpg","adventure","fantasy","medieval"], "shooter": ["fps","shooter","gun"], "platformer": ["platformer","jump","side-scroll"], "racing": ["racing","car","drive"], "horror": ["horror","scary","zombie","survival"], "puzzle": ["puzzle","brain","match"], "strategy": ["strategy","rts","tower defense"], "simulation": ["simulation","sim","build","manage"]}
        for gtype, keywords in type_map.items():
            if any(w in p for w in keywords):
                plan["game_type"] = gtype
                break
        # Complexity
        wc = len(prompt.split())
        if wc > 50 or any(w in p for w in ["full","complete","entire","massive"]):
            plan["complexity"] = "high"
        elif wc > 20:
            plan["complexity"] = "medium"
        else:
            plan["complexity"] = "low"
        # Tasks - always terrain + code + systems
        plan["tasks"].append({"type": "terrain", "priority": 1, "params": self._terrain_params(p)})
        model_kw = ["character","player","npc","enemy","weapon","sword","building","house","tree","rock","car","item","chest","door","model","3d","prop"]
        if any(w in p for w in model_kw):
            plan["tasks"].append({"type": "models", "priority": 2, "params": self._model_params(p)})
        tex_kw = ["texture","material","surface","wood","stone","metal","brick","sand","grass"]
        if any(w in p for w in tex_kw):
            plan["tasks"].append({"type": "textures", "priority": 3, "params": self._texture_params(p)})
        plan["tasks"].append({"type": "code", "priority": 4, "params": self._code_params(p, plan["game_type"])})
        ai_kw = ["ai","npc","enemy","patrol","chase","attack","behavior","state machine"]
        if any(w in p for w in ai_kw):
            plan["tasks"].append({"type": "ai_behavior", "priority": 5, "params": {"mode": "patrol_chase"}})
        anim_kw = ["animation","animate","walk","run","idle","attack","jump","die","motion"]
        if any(w in p for w in anim_kw):
            plan["tasks"].append({"type": "animations", "priority": 6, "params": {"type": "motion_synthesis"}})
        audio_kw = ["audio","sound","voice","music","sfx","narrator","dialogue","ambient"]
        if any(w in p for w in audio_kw):
            plan["tasks"].append({"type": "audio", "priority": 7, "params": {"type": "tts"}})
        plan["tasks"].append({"type": "systems", "priority": 8, "params": self._system_params(p, plan["game_type"])})
        bp_kw = ["blueprint","wire","connect","node","script canvas","visual script"]
        if any(w in p for w in bp_kw):
            plan["tasks"].append({"type": "blueprints", "priority": 9, "params": {"type": "script_canvas"}})
        plan["tasks"].sort(key=lambda t: t["priority"])
        return plan

    def _terrain_params(self, p):
        params = {"seed": int(time.time()) % 100000, "size": 2048}
        if any(w in p for w in ["mountain","alpine","peak","canyon"]):
            params["biome"] = "mountain"
            params["height_max"] = 2000
        elif any(w in p for w in ["desert","sand","arid"]):
            params["biome"] = "desert"
            params["height_max"] = 200
        elif any(w in p for w in ["forest","jungle","tree"]):
            params["biome"] = "forest"
            params["height_max"] = 800
        elif any(w in p for w in ["island","ocean","coast","beach"]):
            params["biome"] = "coastal"
            params["height_max"] = 600
        elif any(w in p for w in ["volcano","lava","fire"]):
            params["biome"] = "volcanic"
            params["height_max"] = 2000
        elif any(w in p for w in ["snow","ice","arctic","frozen"]):
            params["biome"] = "tundra"
            params["height_max"] = 1000
        else:
            params["biome"] = "temperate"
            params["height_max"] = 1200
        return params

    def _model_params(self, p):
        models = []
        model_keywords = {"character": ["character","player","npc","enemy","monster","villain"], "weapon": ["weapon","sword","gun","shield","bow","axe"], "building": ["building","house","castle","dungeon","tower","wall"], "nature": ["tree","rock","grass","flower","bush","mushroom"], "vehicle": ["car","vehicle","boat","ship","plane"], "prop": ["item","chest","door","furniture","table","chair"]}
        for cat, words in model_keywords.items():
            if any(w in p for w in words):
                models.append(cat)
        if not models:
            models = ["prop"]
        return {"categories": models, "style": "realistic" if any(w in p for w in ["realistic","real"]) else "stylized"}

    def _texture_params(self, p):
        textures = []
        tex_keywords = ["wood","stone","metal","brick","sand","grass","marble","rust","fabric","concrete"]
        for t in tex_keywords:
            if t in p:
                textures.append(t)
        if not textures:
            textures = ["generic"]
        return {"textures": textures, "tileable": True, "resolution": 1024}

    def _code_params(self, p, game_type):
        modules = ["core"]
        if game_type == "rpg":
            modules.extend(["inventory","dialogue","quest","stats"])
        elif game_type == "shooter":
            modules.extend(["shooting","health","ammo","weapons"])
        elif game_type == "platformer":
            modules.extend(["movement","jumping","collectibles","lives"])
        elif game_type == "horror":
            modules.extend(["sanity","flashlight","hiding","jumpscare"])
        elif game_type == "strategy":
            modules.extend(["resources","building","units","wave_spawner"])
        else:
            modules.extend(["movement","health","spawning"])
        return {"modules": modules, "language": "lua"}

    def _system_params(self, p, game_type):
        systems = ["game_manager", "player_controller"]
        if game_type == "rpg":
            systems.extend(["dialogue_system", "quest_system", "inventory_system", "save_system"])
        elif game_type == "shooter":
            systems.extend(["weapon_system", "damage_system", "respawn_system"])
        elif game_type == "horror":
            systems.extend(["fear_system", "flashlight_system", "ai_enemy"])
        elif game_type == "platformer":
            systems.extend(["checkpoint_system", "collectible_system"])
        elif game_type == "strategy":
            systems.extend(["resource_manager", "wave_spawner", "base_builder"])
        else:
            systems.extend(["camera_controller", "hud_manager"])
        return {"systems": systems}

    def _execute_task(self, task: Dict, original_prompt: str) -> Dict:
        t = task["type"]
        params = task["params"]
        if t == "terrain":
            return self._gen_terrain(params, original_prompt)
        elif t == "models":
            return self._gen_models(params, original_prompt)
        elif t == "textures":
            return self._gen_textures(params, original_prompt)
        elif t == "code":
            return self._gen_code(params, original_prompt)
        elif t == "ai_behavior":
            return self._gen_ai(params, original_prompt)
        elif t == "animations":
            return self._gen_animations(params, original_prompt)
        elif t == "audio":
            return self._gen_audio(params, original_prompt)
        elif t == "systems":
            return self._gen_systems(params, original_prompt)
        elif t == "blueprints":
            return self._gen_blueprints(params, original_prompt)
        return {"type": t, "status": "skipped", "reason": "unknown task type"}

    def _gen_terrain(self, params, prompt):
        biome = params.get("biome", "temperate")
        seed = params.get("seed", 42)
        hmax = params.get("height_max", 1000)
        biome_configs = {
            "mountain": {"surfaces": [{"name":"Grass","tag":"grass","min_h":0,"max_h":600,"min_s":0,"max_s":30},{"name":"Dirt","tag":"dirt","min_h":400,"max_h":1200,"min_s":20,"max_s":50},{"name":"Rock","tag":"rock","min_h":800,"max_h":9999,"min_s":35,"max_s":90},{"name":"Snow","tag":"snow","min_h":1500,"max_h":9999,"min_s":0,"max_s":45}], "erosion": 70},
            "desert": {"surfaces": [{"name":"Sand","tag":"sand","min_h":0,"max_h":9999,"min_s":0,"max_s":90},{"name":"Rock","tag":"rock","min_h":0,"max_h":9999,"min_s":45,"max_s":90}], "erosion": 30},
            "forest": {"surfaces": [{"name":"Grass","tag":"grass","min_h":0,"max_h":800,"min_s":0,"max_s":25},{"name":"Dirt","tag":"dirt","min_h":200,"max_h":9999,"min_s":15,"max_s":45},{"name":"Rock","tag":"rock","min_h":500,"max_h":9999,"min_s":40,"max_s":90},{"name":"Snow","tag":"snow","min_h":1200,"max_h":9999,"min_s":0,"max_s":50}], "erosion": 50},
            "coastal": {"surfaces": [{"name":"Sand","tag":"sand","min_h":-10,"max_h":30,"min_s":0,"max_s":15},{"name":"Grass","tag":"grass","min_h":30,"max_h":400,"min_s":0,"max_s":30},{"name":"Rock","tag":"rock","min_h":300,"max_h":9999,"min_s":35,"max_s":90}], "erosion": 40},
            "volcanic": {"surfaces": [{"name":"LavaRock","tag":"lava_rock","min_h":0,"max_h":9999,"min_s":0,"max_s":90},{"name":"Ash","tag":"ash","min_h":0,"max_h":400,"min_s":0,"max_s":20},{"name":"Obsidian","tag":"obsidian","min_h":400,"max_h":9999,"min_s":30,"max_s":90}], "erosion": 60},
            "tundra": {"surfaces": [{"name":"Snow","tag":"snow","min_h":0,"max_h":9999,"min_s":0,"max_s":40},{"name":"Ice","tag":"ice","min_h":0,"max_h":9999,"min_s":30,"max_s":90},{"name":"Rock","tag":"rock","min_h":800,"max_h":9999,"min_s":50,"max_s":90}], "erosion": 35},
            "temperate": {"surfaces": [{"name":"Grass","tag":"grass","min_h":0,"max_h":600,"min_s":0,"max_s":25},{"name":"Dirt","tag":"dirt","min_h":200,"max_h":9999,"min_s":15,"max_s":45},{"name":"Rock","tag":"rock","min_h":500,"max_h":9999,"min_s":40,"max_s":90},{"name":"Snow","tag":"snow","min_h":1000,"max_h":9999,"min_s":0,"max_s":50}], "erosion": 45},
        }
        cfg = biome_configs.get(biome, biome_configs["temperate"])
        config = {
            "name": f"ai_terrain_{seed}",
            "biome": biome,
            "seed": seed,
            "size": params.get("size", 2048),
            "o3de_config": {
                "terrain_world": {"min_height": -50, "max_height": hmax, "query_resolution": 1.0},
                "gradient_stack": {
                    "seed": seed,
                    "layers": [
                        {"type": "perlin", "frequency": 0.001, "octaves": 6, "amplitude": 1.0},
                        {"type": "perlin", "frequency": 0.005, "octaves": 4, "amplitude": 0.5, "blend": "add"},
                        {"type": "perlin", "frequency": 0.02, "octaves": 2, "amplitude": 0.2, "blend": "add"},
                    ],
                    "erosion": {"iterations": cfg["erosion"], "strength": cfg["erosion"] / 100.0},
                },
                "surface_layers": cfg["surfaces"],
            },
        }
        path = os.path.join(self.assets_root, "Terrains", f"ai_terrain_{seed}.json")
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        return {"type": "terrain", "status": "generated", "output_path": path, "biome": biome, "height_max": hmax, "surfaces": len(cfg["surfaces"])}

    def _gen_models(self, params, prompt):
        categories = params.get("categories", ["prop"])
        style = params.get("style", "stylized")
        results = []
        for cat in categories:
            cfg = {"category": cat, "style": style, "pipeline": [
                {"tool": "Hunyuan3D", "method": "text_to_3d", "config": {"prompt": prompt, "style": style, "output_format": "fbx", "pbr_materials": True}},
                {"tool": "Dust3D", "method": "mesh_generation", "config": {"prompt": prompt, "smooth": True}},
                {"tool": "O3DE_AssetProcessor", "method": "auto_import", "config": {"destination": os.path.join(self.assets_root, "Models")}},
            ]}
            path = os.path.join(self.assets_root, "Models", f"ai_{cat}_{int(time.time())%10000}.json")
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
            results.append({"category": cat, "path": path})
        return {"type": "models", "status": "generated", "count": len(results), "models": results}

    def _gen_textures(self, params, prompt):
        textures = params.get("textures", ["generic"])
        results = []
        for tex in textures:
            cfg = {"texture": tex, "tileable": params.get("tileable", True), "resolution": params.get("resolution", 1024), "pipeline": [
                {"tool": "ComfyUI", "method": "texture_generation", "config": {"prompt": f"{tex} texture {prompt}", "tileable": True, "resolution": params.get("resolution", 1024)}},
                {"tool": "O3DE_AssetProcessor", "method": "auto_import", "config": {"destination": os.path.join(self.assets_root, "Textures")}},
            ]}
            path = os.path.join(self.assets_root, "Textures", f"ai_{tex}_{int(time.time())%10000}.json")
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
            results.append({"texture": tex, "path": path})
        return {"type": "textures", "status": "generated", "count": len(results), "textures": results}

    def _gen_code(self, params, prompt):
        modules = params.get("modules", ["core"])
        lang = params.get("language", "lua")
        templates = self._get_templates()
        generated = []
        for mod in modules:
            code = templates.get(mod, templates["core"])
            name = f"ai_{mod}_{int(time.time())%10000}"
            path = os.path.join(self.assets_root, "Code", f"{name}.lua")
            with open(path, "w") as f:
                f.write(code)
            generated.append({"module": mod, "path": path, "lines": len(code.splitlines())})
        return {"type": "code", "status": "generated", "language": lang, "count": len(generated), "files": generated}

    def _gen_ai(self, params, prompt):
        code = self._get_ai_patrol_code()
        path = os.path.join(self.assets_root, "Code", f"ai_patrol_{int(time.time())%10000}.lua")
        with open(path, "w") as f:
            f.write(code)
        return {"type": "ai_behavior", "status": "generated", "output_path": path}

    def _gen_animations(self, params, prompt):
        cfg = {"type": params.get("type", "motion_synthesis"), "pipeline": [
            {"tool": "GANimator", "method": "motion_synthesis", "config": {"prompt": prompt}},
            {"tool": "DeepMotionEditing", "method": "retargeting", "config": {"prompt": prompt, "foot_skate_cleanup": True}},
        ]}
        path = os.path.join(self.assets_root, "Animations", f"ai_anim_{int(time.time())%10000}.json")
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        return {"type": "animations", "status": "generated", "output_path": path}

    def _gen_audio(self, params, prompt):
        cfg = {"type": params.get("type", "tts"), "pipeline": [
            {"tool": "ElevenLabsClone", "method": "tts", "config": {"text": prompt}},
            {"tool": "InworldAI", "method": "realtime_speech", "config": {"text": prompt}},
        ]}
        path = os.path.join(self.assets_root, "Audio", f"ai_audio_{int(time.time())%10000}.json")
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        return {"type": "audio", "status": "generated", "output_path": path}

    def _gen_systems(self, params, prompt):
        systems = params.get("systems", ["game_manager", "player_controller"])
        templates = self._get_templates()
        generated = []
        for sys_name in systems:
            code = templates.get(sys_name, templates["game_manager"])
            path = os.path.join(self.assets_root, "Scripts", f"{sys_name}.lua")
            with open(path, "w") as f:
                f.write(code)
            generated.append({"system": sys_name, "path": path})
        return {"type": "systems", "status": "generated", "count": len(generated), "files": generated}

    def _gen_blueprints(self, params, prompt):
        nodes = [
            {"id": 1, "type": "ScriptCanvas", "name": "InputNode", "pos": [0, 0]},
            {"id": 2, "type": "ScriptCanvas", "name": "LogicNode", "pos": [300, 0]},
            {"id": 3, "type": "Output", "name": "OutputNode", "pos": [600, 0]},
        ]
        connections = [
            {"from": 1, "fromOutput": "OnActivate", "to": 2, "toInput": "Process"},
            {"from": 2, "fromOutput": "Result", "to": 3, "toInput": "Set"},
        ]
        cfg = {"nodes": nodes, "connections": connections}
        path = os.path.join(self.assets_root, "Scripts", f"ai_blueprint_{int(time.time())%10000}.json")
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        return {"type": "blueprints", "status": "generated", "output_path": path}

    def _generate_summary(self, results):
        lines = [f"=== FULL GAME GENERATION COMPLETE ===", f"Prompt: {results['prompt'][:100]}...", f"Status: {results['status']}", ""]
        for t in results["tasks"]:
            lines.append(f"[{t['type']}] {t.get('status', 'unknown')}")
            if t.get("count"):
                lines.append(f"  Generated {t['count']} items")
            if t.get("files"):
                for f in t["files"]:
                    lines.append(f"  - {f.get('module', f.get('system', '?'))}: {f.get('path', 'N/A')}")
        lines.append(f"\nAll assets saved to: {results['assets_root']}")
        return "\n".join(lines)

    def _get_templates(self):
        t = {}
        t["core"] = """-- O3DE Core Component
local CoreComponent = {
    Properties = {
        Enabled = { default = true },
    },
}

function CoreComponent:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    Debug.Log("CoreComponent activated")
end

function CoreComponent:OnDeactivate()
    self.tickHandler:Disconnect()
end

function CoreComponent:OnTick(dt, tp)
    if not self.Properties.Enabled then return end
end
"""
        t["inventory"] = """-- Inventory System
local InventorySystem = { Properties = { MaxSlots = { default = 20 } } }
function InventorySystem:OnActivate()
    self.items = {}
    self.count = 0
end
function InventorySystem:OnDeactivate() end
function InventorySystem:AddItem(item)
    if self.count >= self.Properties.MaxSlots then return false end
    table.insert(self.items, item)
    self.count = self.count + 1
    return true
end
function InventorySystem:RemoveItem(id)
    for i, item in ipairs(self.items) do
        if item.id == id then table.remove(self.items, i); self.count = self.count - 1; return true end
    end
    return false
end
function InventorySystem:HasItem(id)
    for _, item in ipairs(self.items) do
        if item.id == id then return true end
    end
    return false
end
function InventorySystem:GetItems() return self.items end
"""
        t["dialogue"] = """-- Dialogue System
local DialogueSystem = { Properties = { DialogueAsset = { default = "" } } }
function DialogueSystem:OnActivate()
    self.isActive = false
    self.currentLine = 0
    self.lines = {}
end
function DialogueSystem:OnDeactivate() end
function DialogueSystem:StartDialogue(lines)
    self.lines = lines
    self.currentLine = 1
    self.isActive = true
    self:ShowLine()
end
function DialogueSystem:ShowLine()
    if self.currentLine <= #self.lines then
        local line = self.lines[self.currentLine]
        Debug.Log(line.speaker .. ": " .. line.text)
    else
        self:EndDialogue()
    end
end
function DialogueSystem:Advance()
    self.currentLine = self.currentLine + 1
    self:ShowLine()
end
function DialogueSystem:EndDialogue()
    self.isActive = false
    self.currentLine = 0
end
"""
        t["quest"] = """-- Quest System
local QuestSystem = { Properties = { MaxQuests = { default = 10 } } }
function QuestSystem:OnActivate()
    self.quests = {}
    self.activeQuests = {}
end
function QuestSystem:OnDeactivate() end
function QuestSystem:AcceptQuest(quest)
    if #self.activeQuests >= self.Properties.MaxQuests then return false end
    quest.status = "active"
    quest.progress = 0
    table.insert(self.activeQuests, quest)
    return true
end
function QuestSystem:CompleteQuest(questId)
    for i, q in ipairs(self.activeQuests) do
        if q.id == questId then
            q.status = "completed"
            table.remove(self.activeQuests, i)
            return true
        end
    end
    return false
end
function QuestSystem:GetActiveQuests() return self.activeQuests end
"""
        t["stats"] = """-- Character Stats System
local StatsSystem = { Properties = {
    MaxHealth = { default = 100 }, MaxStamina = { default = 100 },
    Strength = { default = 10 }, Defense = { default = 5 }, Speed = { default = 8 },
} }
function StatsSystem:OnActivate()
    self.health = self.Properties.MaxHealth
    self.stamina = self.Properties.MaxStamina
    self.level = 1
    self.xp = 0
end
function StatsSystem:OnDeactivate() end
function StatsSystem:TakeDamage(amount)
    local reduced = math.max(1, amount - self.Properties.Defense)
    self.health = math.max(0, self.health - reduced)
    if self.health <= 0 then Debug.Log("Entity died!") end
end
function StatsSystem:Heal(amount) self.health = math.min(self.Properties.MaxHealth, self.health + amount) end
function StatsSystem:AddXP(amount)
    self.xp = self.xp + amount
    if self.xp >= self.level * 100 then
        self.level = self.level + 1
        self.xp = 0
        Debug.Log("Level up! Now level " .. self.level)
    end
end
"""
        t["shooting"] = """-- Shooting System
local ShootingSystem = { Properties = {
    FireRate = { default = 0.1 }, Damage = { default = 25 }, Range = { default = 100 }, Ammo = { default = 30 },
} }
function ShootingSystem:OnActivate()
    self.lastFireTime = 0
    self.currentAmmo = self.Properties.Ammo
end
function ShootingSystem:OnDeactivate() end
function ShootingSystem:OnTick(dt, tp)
    if InputDevice.IsMouseButtonPressed(0) and self.currentAmmo > 0 then
        if tp - self.lastFireTime >= self.Properties.FireRate then
            self:Fire()
            self.lastFireTime = tp
        end
    end
end
function ShootingSystem:Fire()
    self.currentAmmo = self.currentAmmo - 1
    Debug.Log("FIRE! Ammo: " .. self.currentAmmo)
end
function ShootingSystem:Reload() self.currentAmmo = self.Properties.Ammo end
"""
        t["health"] = """-- Health System
local HealthSystem = { Properties = { MaxHealth = { default = 100 }, RegenRate = { default = 0 } } }
function HealthSystem:OnActivate()
    self.hp = self.Properties.MaxHealth
    self.alive = true
    self.tickHandler = TickBus.Connect(self, 0)
end
function HealthSystem:OnDeactivate() self.tickHandler:Disconnect() end
function HealthSystem:OnTick(dt, tp)
    if self.alive and self.Properties.RegenRate > 0 then
        self.hp = math.min(self.Properties.MaxHealth, self.hp + self.Properties.RegenRate * dt)
    end
end
function HealthSystem:TakeDamage(amount)
    if not self.alive then return end
    self.hp = math.max(0, self.hp - amount)
    if self.hp <= 0 then self.alive = false; Debug.Log("DIED") end
end
function HealthSystem:Heal(amount) self.hp = math.min(self.Properties.MaxHealth, self.hp + amount) end
function HealthSystem:GetHealth() return self.hp end
"""
        t["movement"] = """-- Movement System
local MovementSystem = { Properties = { Speed = { default = 5.0 }, SprintMult = { default = 1.5 }, JumpForce = { default = 8.0 } } }
function MovementSystem:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    self.vel = Vector3(0, 0, 0)
    self.grounded = true
end
function MovementSystem:OnDeactivate() self.tickHandler:Disconnect() end
function MovementSystem:OnTick(dt, tp)
    local input = Vector3(0, 0, 0)
    if InputDevice.IsKeyDown("keyboard_w") then input = input + Vector3(0, 1, 0) end
    if InputDevice.IsKeyDown("keyboard_s") then input = input + Vector3(0, -1, 0) end
    if InputDevice.IsKeyDown("keyboard_a") then input = input + Vector3(-1, 0, 0) end
    if InputDevice.IsKeyDown("keyboard_d") then input = input + Vector3(1, 0, 0) end
    if input:GetLength() > 0 then input = input:GetNormalized() end
    local speed = self.Properties.Speed
    if InputDevice.IsKeyDown("keyboard_lshift") then speed = speed * self.Properties.SprintMult end
    self.vel = Vector3(input.x * speed, input.y * speed, self.vel.z)
    if not self.grounded then self.vel = Vector3(self.vel.x, self.vel.y, self.vel.z - 9.81 * dt) end
    if InputDevice.IsKeyDown("keyboard_space") and self.grounded then
        self.vel = Vector3(self.vel.x, self.vel.y, self.Properties.JumpForce); self.grounded = false
    end
    local pos = TransformBus.Event.GetLocalTranslation(self.entityId)
    TransformBus.Event.SetLocalTranslation(self.entityId, pos + self.vel * dt)
end
"""
        t["jumping"] = t["movement"]
        t["collectibles"] = """-- Collectible System
local CollectibleSystem = { Properties = { PickupRadius = { default = 2.0 }, Value = { default = 1 } } }
function CollectibleSystem:OnActivate() self.collected = false end
function CollectibleSystem:OnDeactivate() end
function CollectibleSystem:OnTriggerEnter(otherId)
    if not self.collected then
        self.collected = true
        Debug.Log("Collected item worth " .. self.Properties.Value)
        DynamicBus.ToolsRequestBus.Broadcast.RequestDeleteEntity(self.entityId)
    end
end
"""
        t["lives"] = """-- Lives System
local LivesSystem = { Properties = { MaxLives = { default = 3 }, RespawnDelay = { default = 2.0 } } }
function LivesSystem:OnActivate()
    self.lives = self.Properties.MaxLives
    self.respawnTimer = 0
    self.isDead = false
end
function LivesSystem:OnDeactivate() end
function LivesSystem:Die()
    self.isDead = true
    self.lives = self.lives - 1
    self.respawnTimer = self.Properties.RespawnDelay
    Debug.Log("Died! Lives remaining: " .. self.lives)
end
"""
        t["ammo"] = t["shooting"]
        t["weapons"] = t["shooting"]
        t["respawn_system"] = """-- Respawn System
local RespawnSystem = { Properties = { RespawnPoint = { default = Vector3(0, 0, 0) }, RespawnDelay = { default = 3.0 } } }
function RespawnSystem:OnActivate() self.respawnTimer = 0; self.isDead = false end
function RespawnSystem:OnDeactivate() end
function RespawnSystem:OnTick(dt, tp)
    if self.isDead then
        self.respawnTimer = self.respawnTimer - dt
        if self.respawnTimer <= 0 then self:Respawn() end
    end
end
function RespawnSystem:Die() self.isDead = true; self.respawnTimer = self.Properties.RespawnDelay end
function RespawnSystem:Respawn()
    self.isDead = false
    TransformBus.Event.SetLocalTranslation(self.entityId, self.Properties.RespawnPoint)
    Debug.Log("Respawned!")
end
"""
        t["damage_system"] = t["health"]
        t["camera_controller"] = """-- Camera Controller
local CameraController = { Properties = { FollowSpeed = { default = 5.0 }, Offset = { default = Vector3(0, -10, 5) }, LookAtEntity = { default = nil } } }
function CameraController:OnActivate() self.tickHandler = TickBus.Connect(self, 0) end
function CameraController:OnDeactivate() self.tickHandler:Disconnect() end
function CameraController:OnTick(dt, tp)
    if self.Properties.LookAtEntity and self.Properties.LookAtEntity:IsValid() then
        local targetPos = TransformBus.Event.GetWorldTranslation(self.Properties.LookAtEntity)
        local desiredPos = targetPos + self.Properties.Offset
        local currentPos = TransformBus.Event.GetWorldTranslation(self.entityId)
        local newPos = currentPos + (desiredPos - currentPos) * self.Properties.FollowSpeed * dt
        TransformBus.Event.SetWorldTranslation(self.entityId, newPos)
    end
end
"""
        t["hud_manager"] = """-- HUD Manager
local HUDManager = { Properties = { HealthBarEntity = { default = nil }, AmmoTextEntity = { default = nil } } }
function HUDManager:OnActivate() self.tickHandler = TickBus.Connect(self, 0) end
function HUDManager:OnDeactivate() self.tickHandler:Disconnect() end
function HUDManager:OnTick(dt, tp) end
function HUDManager:UpdateHealth(percent)
    Debug.Log("Health: " .. math.floor(percent * 100) .. "%")
end
function HUDManager:UpdateAmmo(count)
    Debug.Log("Ammo: " .. count)
end
"""
        t["game_manager"] = """-- Game Manager
local GameManager = { Properties = { GameState = { default = "menu" } } }
function GameManager:OnActivate()
    Debug.Log("Game Manager initialized")
    self.score = 0
    self.wave = 1
    self.tickHandler = TickBus.Connect(self, 0)
end
function GameManager:OnDeactivate() self.tickHandler:Disconnect() end
function GameManager:OnTick(dt, tp) end
function GameManager:AddScore(amount) self.score = self.score + amount end
function GameManager:NextWave() self.wave = self.wave + 1; Debug.Log("Wave " .. self.wave) end
"""
        t["player_controller"] = """-- Player Controller
local PlayerController = { Properties = { Speed = { default = 5.0 }, Health = { default = 100 } } }
function PlayerController:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    self.hp = self.Properties.Health
end
function PlayerController:OnDeactivate() self.tickHandler:Disconnect() end
function PlayerController:OnTick(dt, tp)
    local input = Vector3(0, 0, 0)
    if InputDevice.IsKeyDown("keyboard_w") then input = input + Vector3(0, 1, 0) end
    if InputDevice.IsKeyDown("keyboard_s") then input = input + Vector3(0, -1, 0) end
    if InputDevice.IsKeyDown("keyboard_a") then input = input + Vector3(-1, 0, 0) end
    if InputDevice.IsKeyDown("keyboard_d") then input = input + Vector3(1, 0, 0) end
    if input:GetLength() > 0 then input = input:GetNormalized() end
    local pos = TransformBus.Event.GetLocalTranslation(self.entityId)
    TransformBus.Event.SetLocalTranslation(self.entityId, pos + input * self.Properties.Speed * dt)
end
"""
        t["dialogue_system"] = t["dialogue"]
        t["quest_system"] = t["quest"]
        t["inventory_system"] = t["inventory"]
        t["save_system"] = """-- Save System
local SaveSystem = { Properties = { SaveFileName = { default = "savegame.json" } } }
function SaveSystem:OnActivate() end
function SaveSystem:OnDeactivate() end
function SaveSystem:SaveGame(data)
    local path = self.Properties.SaveFileName
    Debug.Log("Game saved to " .. path)
end
function SaveSystem:LoadGame()
    Debug.Log("Game loaded")
end
"""
        t["weapon_system"] = t["shooting"]
        t["fear_system"] = """-- Fear/Sanity System
local FearSystem = { Properties = { MaxSanity = { default = 100 }, DecayRate = { default = 1.0 } } }
function FearSystem:OnActivate()
    self.sanity = self.Properties.MaxSanity
    self.tickHandler = TickBus.Connect(self, 0)
end
function FearSystem:OnDeactivate() self.tickHandler:Disconnect() end
function FearSystem:OnTick(dt, tp)
    self.sanity = math.max(0, self.sanity - self.Properties.DecayRate * dt)
    if self.sanity <= 0 then Debug.Log("Sanity depleted!") end
end
function FearSystem:AddFear(amount) self.sanity = math.max(0, self.sanity - amount) end
function FearSystem:ReduceFear(amount) self.sanity = math.min(self.Properties.MaxSanity, self.sanity + amount) end
"""
        t["flashlight_system"] = """-- Flashlight System
local FlashlightSystem = { Properties = { BatteryDrain = { default = 0.5 }, MaxBattery = { default = 100 } } }
function FlashlightSystem:OnActivate()
    self.battery = self.Properties.MaxBattery
    self.isOn = false
    self.tickHandler = TickBus.Connect(self, 0)
end
function FlashlightSystem:OnDeactivate() self.tickHandler:Disconnect() end
function FlashlightSystem:OnTick(dt, tp)
    if self.isOn then
        self.battery = math.max(0, self.battery - self.Properties.BatteryDrain * dt)
        if self.battery <= 0 then self.isOn = false; Debug.Log("Flashlight battery dead!") end
    end
end
function FlashlightSystem:Toggle() self.isOn = not self.isOn end
"""
        t["ai_enemy"] = t.get("ai_patrol", """-- AI Enemy
local AIEnemy = { Properties = { Speed = { default = 3.0 }, DetectRange = { default = 20.0 } } }
function AIEnemy:OnActivate() self.state = "patrol"; self.tickHandler = TickBus.Connect(self, 0) end
function AIEnemy:OnDeactivate() self.tickHandler:Disconnect() end
function AIEnemy:OnTick(dt, tp) end
""")
        t["checkpoint_system"] = """-- Checkpoint System
local CheckpointSystem = { Properties = { CurrentCheckpoint = { default = Vector3(0, 0, 0) } } }
function CheckpointSystem:OnActivate() end
function CheckpointSystem:OnDeactivate() end
function CheckpointSystem:SetCheckpoint(pos) self.Properties.CurrentCheckpoint = pos; Debug.Log("Checkpoint set") end
function CheckpointSystem:GetCheckpoint() return self.Properties.CurrentCheckpoint end
"""
        t["collectible_system"] = t["collectibles"]
        t["resource_manager"] = """-- Resource Manager
local ResourceManager = { Properties = { Gold = { default = 0 }, Wood = { default = 0 }, Stone = { default = 0 } } }
function ResourceManager:OnActivate() end
function ResourceManager:OnDeactivate() end
function ResourceManager:AddResource(type, amount)
    if type == "gold" then self.Properties.Gold = self.Properties.Gold + amount
    elseif type == "wood" then self.Properties.Wood = self.Properties.Wood + amount
    elseif type == "stone" then self.Properties.Stone = self.Properties.Stone + amount end
end
function ResourceManager:SpendResource(type, amount)
    if type == "gold" and self.Properties.Gold >= amount then self.Properties.Gold = self.Properties.Gold - amount; return true end
    return false
end
"""
        t["wave_spawner"] = """-- Wave Spawner
local WaveSpawner = { Properties = { EnemiesPerWave = { default = 5 }, WaveDelay = { default = 10.0 }, PrefabPath = { default = "" } } }
function WaveSpawner:OnActivate()
    self.currentWave = 1
    self.spawnedCount = 0
    self.waveTimer = 0
    self.tickHandler = TickBus.Connect(self, 0)
end
function WaveSpawner:OnDeactivate() self.tickHandler:Disconnect() end
function WaveSpawner:OnTick(dt, tp)
    self.waveTimer = self.waveTimer + dt
    if self.waveTimer >= self.Properties.WaveDelay then
        self:SpawnWave()
        self.waveTimer = 0
    end
end
function WaveSpawner:SpawnWave()
    local count = self.Properties.EnemiesPerWave * self.currentWave
    Debug.Log("Spawning wave " .. self.currentWave .. " with " .. count .. " enemies")
    self.currentWave = self.currentWave + 1
end
"""
        t["base_builder"] = """-- Base Builder
local BaseBuilder = { Properties = { BuildRange = { default = 20.0 } } }
function BaseBuilder:OnActivate() self.buildings = {} end
function BaseBuilder:OnDeactivate() end
function BaseBuilder:PlaceBuilding(type, pos)
    table.insert(self.buildings, {type = type, position = pos})
    Debug.Log("Placed " .. type .. " at " .. tostring(pos))
end
function BaseBuilder:GetBuildings() return self.buildings end
"""
        return t

    def _get_ai_patrol_code(self):
        return """-- AI Patrol/Chase State Machine
local AIPatrol = {
    Properties = {
        PatrolSpeed = { default = 3.0 },
        ChaseSpeed = { default = 6.0 },
        DetectionRange = { default = 20.0 },
        LoseRange = { default = 30.0 },
        PatrolWaitTime = { default = 2.0 },
    },
}

function AIPatrol:OnActivate()
    self.state = "patrol"
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
        if self:DetectPlayer(myPos) then
            self.state = "chase"
        end
    elseif self.state == "chase" then
        if not self:DetectPlayer(myPos) then
            self.state = "patrol"
        else
            self:ChaseTick(deltaTime, myPos)
        end
    end
end

function AIPatrol:DetectPlayer(myPos)
    local allEntities = TagGlobalRequestBus.Connect(self, "Player")
    if allEntities then
        for _, playerId in ipairs(allEntities) do
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

function AIPatrol:ChaseTick(deltaTime, myPos)
    if not self.targetEntityId or not self.targetEntityId:IsValid() then return end
    local targetPos = TransformBus.Event.GetWorldTranslation(self.targetEntityId)
    local direction = (targetPos - myPos):GetNormalized()
    local newPos = myPos + direction * self.Properties.ChaseSpeed * deltaTime
    TransformBus.Event.SetWorldTranslation(self.entityId, newPos)
end
"""


orchestrator = FullGameOrchestrator()
