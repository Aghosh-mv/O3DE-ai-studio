# O3DE AI Design Studio

**The closest thing to "vibe coding" a complete game.**

An AI-powered sidebar for Open 3D Engine (O3DE) that lets you generate terrain, 3D models, textures, code, animations, audio, and complete game systems from a single natural language prompt.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![O3DE](https://img.shields.io/badge/O3DE-26.05-green.svg)
![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)

## What Is This?

This project adds an **AI Design Studio** sidebar panel to the O3DE game engine editor. Instead of manually creating every asset, writing every script, and wiring every blueprint, you describe what you want in plain English and the AI generates it.

### One Prompt. Everything Generated.

Type something like:
> "Create a medieval fantasy RPG with mountain terrain, a knight character, sword weapon, castle building, enemy AI patrol, and background music"

And the system generates:
- **Terrain** - Mountain biome with grass, dirt, rock, snow surface layers
- **3D Models** - Character, weapon, building pipelines via Hunyuan3D/Dust3D
- **Textures** - PBR material sets via ComfyUI
- **Lua Code** - Player controller, inventory, dialogue, quest systems
- **AI Behavior** - Patrol/chase state machine for enemies
- **Animations** - Motion synthesis via GANimator/DeepMotionEditing
- **Audio** - Background music/narration via ElevenLabsClone
- **Blueprints** - ScriptCanvas node configurations

## Architecture

```
O3DE Editor
  └── AI Design Studio (Sidebar Panel)
        ├── Chat Interface (Natural Language Input)
        ├── Full Game Orchestrator (Chains all tools)
        ├── Live LLM (OpenRouter Free Models)
        ├── Terrain Generator (ProceduralTerrains)
        ├── 3D Model Pipeline (Hunyuan3D, Dust3D)
        ├── Texture Pipeline (ComfyUI, Stable Diffusion)
        ├── Code Generator (LLM + Templates)
        ├── Animation Pipeline (GANimator, DeepMotionEditing)
        ├── Audio Pipeline (ElevenLabsClone, InworldAI)
        └── Blueprint Generator (ScriptCanvas)
```

## Integrated AI Tools

| Tool | Purpose | Type |
|------|---------|------|
| **OpenRouter** | Live LLM for code generation | Free Models API |
| **ProceduralTerrains** | GPU-based terrain generation | Local/WebGL |
| **Hunyuan3D** | Text/Image to 3D model | AI Pipeline |
| **Dust3D** | Mesh generation | Local |
| **ComfyUI** | Texture generation (Stable Diffusion) | Local/API |
| **GANimator** | Novel motion synthesis | Local/Python |
| **DeepMotionEditing** | Motion retargeting | Local/Python |
| **ElevenLabsClone** | Text-to-speech | Local/Docker |
| **InworldAI** | Voice AI for NPCs | API |
| **AutoGen** | Multi-agent orchestration | Local/Python |
| **Cline/RooCode** | Autonomous coding | Local/CLI |
| **DeepSeek-R1** | Reasoning model | Local |
| **GPT-NeoX** | Open-source LLM | Local |

## Free LLM Models (OpenRouter)

The system uses OpenRouter's free models for code generation:

| Model | Context | Best For |
|-------|---------|----------|
| `openrouter/free` | Auto-select | General use |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1M tokens | Large context |
| `google/gemma-4-31b-it:free` | 262K tokens | General |
| `openai/gpt-oss-20b:free` | 131K tokens | Fast coding |
| `meta-llama/llama-3.3-70b-instruct:free` | 131K tokens | Code generation |
| `dots-studio/dots-3-note-preview:free` | 512K tokens | Reasoning |
| `poolside/laguna-s-2.1:free` | 262K tokens | Coding agents |

**Rate Limits:** 20 req/min, 50 req/day (free), 1000 req/day (with $10 credits)

## Quick Start

### 1. Clone This Repository
```bash
git clone https://github.com/aghosh-mv/o3de-ai-studio.git
cd o3de-ai-studio
```

### 2. Set Your API Key
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```
Or enter it in the AI Design Studio Settings tab.

### 3. Build O3DE (or use pre-built)
```bash
cd o3de-ai-studio
cmake -B build/windows -S . -G "Visual Studio 16 2019"
cmake --build build/windows --target Editor
```

### 4. Open the Editor
The AI Design Studio sidebar auto-registers. Go to: **View → AI Design Studio**

### 5. Start Creating
Type your game concept and click **"FULL GAME - One Prompt"**

## Project Structure

```
o3de-ai-studio/
├── AISidebar/                 # AI Design Studio panel
│   ├── ai_sidebar.py          # Main sidebar UI (PySide6/Qt)
│   ├── full_game_orchestrator.py  # Chains all AI tools
│   └── o3de_knowledge.py      # O3DE engine knowledge base
├── AIProject/                 # Generated assets output
│   └── Assets/
│       ├── Code/              # Generated Lua/Python scripts
│       ├── Models/            # 3D model pipelines
│       ├── Textures/          # Texture pipelines
│       ├── Terrains/          # Terrain configurations
│       ├── Audio/             # Audio pipelines
│       ├── Animations/        # Animation pipelines
│       └── Scripts/           # System scripts
├── ProceduralTerrains/        # Terrain generation tool
├── Hunyuan3D/                 # 3D model generation
├── Dust3D/                    # Mesh generation
├── ComfyUI/                   # Texture generation
├── GANimator/                 # Animation synthesis
├── DeepMotionEditing/         # Motion retargeting
├── ElevenLabsClone/           # Text-to-speech
├── InworldAI/                 # Voice AI
├── AutoGen/                   # Multi-agent orchestration
├── Cline/                     # Autonomous coding
├── RooCode/                   # Code generation
├── DeepSeek-R1/               # Reasoning model
├── GPT-NeoX/                  # Open-source LLM
├── BlenderMCP/                # Blender integration
├── Code/                      # O3DE editor source
├── Gems/                      # O3DE engine gems
└── README.md
```

## How It Works

### Single Tool Generation
1. User types a prompt in the AI sidebar
2. The system detects what type of content to generate (terrain, code, model, etc.)
3. The appropriate generator is called
4. For code: the LLM is called first, falls back to templates
5. Generated content is saved to the AIProject/Assets directory
6. O3DE's Asset Processor auto-compiles new assets

### Full Game Generation
1. User types a game concept and clicks "FULL GAME"
2. The orchestrator analyzes the prompt for game type, complexity, features
3. It creates a generation plan (terrain → models → textures → code → AI → animations → audio → systems)
4. Each task is executed in sequence
5. All generated files are saved to the project directory
6. Summary is shown in the chat

### Live LLM Integration
- Uses OpenRouter API with free models
- System prompt includes full O3DE knowledge (components, EBus calls, scripting patterns)
- Falls back to curated templates when LLM is unavailable
- Supports multiple free model providers

## Supported Game Types

The orchestrator auto-detects and generates appropriate systems for:

| Game Type | Auto-Generated Systems |
|-----------|----------------------|
| **RPG** | Inventory, Dialogue, Quest, Stats, Save System |
| **Shooter** | Weapon, Health, Ammo, Damage, Respawn |
| **Platformer** | Movement, Jumping, Collectibles, Lives, Checkpoints |
| **Horror** | Sanity, Flashlight, Hiding, AI Enemy |
| **Strategy** | Resources, Building, Units, Wave Spawner |
| **Simulation** | Resources, Building, Management |

## Requirements

- **O3DE 26.05** (source or pre-built)
- **Python 3.10+** (for editor scripting)
- **PySide6** (for Qt UI)
- **OpenRouter API key** (free tier available)
- **GPU** (optional, for local AI tools like ComfyUI, GANimator)

## License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- **Open 3D Engine** - The open-source game engine
- **OpenRouter** - Free AI model API
- **All AI tool repositories** integrated into this project

## Disclaimer

This is an AI-assisted game development tool. Generated content may need refinement. The AI cannot replace human creativity and game design expertise - it accelerates the tedious parts so you can focus on the fun parts.
