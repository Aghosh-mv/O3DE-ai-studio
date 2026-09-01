# O3DE AI Design Studio

**The closest thing to "vibe coding" a complete AAA game.**

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

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Git** | Latest | For cloning |
| **CMake** | 3.24+ | 3.28 recommended |
| **Clang** | 14+ | Or GCC 13+ |
| **Python** | 3.10+ | O3DE's embedded Python |
| **OS** | Linux (Ubuntu 22.04+) or Windows | |

### Linux Setup (Tested on Ubuntu 22.04)

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential clang lld pkg-config \
  libunwind-dev libzstd-dev libxcb-xinput0-dev libxcb-xfixes0-dev \
  libxcb-keysyms1-dev libxcb-image0-dev libxcb-shm0-dev \
  libxcb-icccm4-dev libxcb-sync-dev libxcb-shape0-dev \
  libxcb-randr0-dev libxcb-render-util0-dev libxcb-xinerama0-dev \
  libxcb-xkb-dev libxkbcommon-dev libxkbcommon-x11-dev \
  python3-dev libssl-dev

# Clone and build
git clone https://github.com/Aghosh-mv/O3DE-ai-studio.git
cd O3DE-ai-studio

# Run O3DE's python setup to get 3rdParty dependencies
python3 scripts/o3de.py register --this-engine

# Configure with CMake (clang recommended)
cmake -B build -S . -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=profile \
  -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++

# Build the Editor (~15-20 min depending on hardware)
cmake --build build --target Editor --config profile -j$(nproc)
```

### Windows Setup

```powershell
# Install Visual Studio 2022 with C++ workload
# Install CMake 3.28+ from https://cmake.org/download/
# Install Python 3.10+

git clone https://github.com/Aghosh-mv/O3DE-ai-studio.git
cd O3DE-ai-studio

python scripts/o3de.py register --this-engine

cmake -B build -S . -G "Visual Studio 17 2022"
cmake --build build --target Editor --config profile
```

### Run the Editor

```bash
# Linux
cd build/bin/profile
./Editor

# Windows
cd build\bin\profile
Editor.exe
```

### Open AI Design Studio

Once the editor loads:
1. Go to **View → AI Design Studio** in the menu bar
2. Enter your **OpenRouter API key** in the Settings tab
3. Click **Chat** tab and start typing your game idea
4. Click **"FULL GAME - One Prompt"** to generate everything at once

## Getting Your Free API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up (free)
3. Go to **Keys** → Create new key
4. Copy the key (starts with `sk-or-v1-`)
5. Paste it into the AI Design Studio Settings tab

**Free tier includes:**
- 20 requests/minute
- 50 requests/day
- All free models available

**With $10 credits:**
- 1000 requests/day
- Access to paid models

## Free Models Available

| Model | Context | Best For |
|-------|---------|----------|
| `auto` | Auto-select | General use |
| `nvidia/nemotron-ultra-253b:free` | 1M tokens | Large context |
| `nvidia/nemotron-super-49b-a17b:free` | 262K tokens | General |
| `google/gemma-4-31b-it:free` | 262K tokens | General |
| `openai/gpt-oss-20b:free` | 131K tokens | Fast coding |
| `meta-llama/llama-3.3-70b-instruct:free` | 131K tokens | Code generation |
| `dots-studio/dots-3-note-preview:free` | 512K tokens | Reasoning |
| `poolside/laguna-s-2.1:free` | 262K tokens | Coding agents |

## How It Works

### Single Tool Generation
1. You type a prompt in the AI sidebar
2. The system detects what type of content to generate (terrain, code, model, etc.)
3. The appropriate generator is called
4. For code: the LLM is called first, falls back to templates
5. Generated content is saved to the project directory
6. O3DE's Asset Processor auto-compiles new assets

### Full Game Generation
1. You type a game concept and click "FULL GAME"
2. The orchestrator analyzes the prompt for game type, complexity, features
3. It creates a generation plan (terrain -> models -> textures -> code -> AI -> animations -> audio -> systems)
4. Each task is executed in sequence
5. All generated files are saved to the project directory
6. Summary is shown in the chat

### Live LLM Integration
- Uses OpenRouter API with free models
- System prompt includes full O3DE knowledge (components, EBus calls, scripting patterns)
- Falls back to curated templates when LLM is unavailable
- Supports multiple free model providers

## Supported Game Types

| Game Type | Auto-Generated Systems |
|-----------|----------------------|
| **RPG** | Inventory, Dialogue, Quest, Stats, Save System |
| **Shooter** | Weapon, Health, Ammo, Damage, Respawn |
| **Platformer** | Movement, Jumping, Collectibles, Lives, Checkpoints |
| **Horror** | Sanity, Flashlight, Hiding, AI Enemy |
| **Strategy** | Resources, Building, Units, Wave Spawner |
| **Racing** | Vehicle, Track, Speed, Checkpoints, Lap System |
| **Survival** | Hunger, Thirst, Health, Crafting, Base Building |
| **Space** | Ship, Weapons, Shields, Asteroids, Docking |
| **Simulation** | Resources, Building, Management |

## Project Structure

```
O3DE-ai-studio/
├── Gems/
│   └── AIDesignStudio/          # AI Design Studio Gem
│       ├── gem.json             # Gem metadata
│       ├── CMakeLists.txt       # Build configuration
│       └── Editor/Scripts/
│           ├── ai_sidebar.py    # Main sidebar UI (PySide6/Qt)
│           ├── full_game_orchestrator.py  # One-prompt game generator
│           └── o3de_knowledge.py # O3DE engine knowledge base
├── Gems/QtForPython/            # Qt for Python (auto-loaded)
│   └── Editor/Scripts/
│       └── bootstrap.py         # Auto-registers AI Design Studio
├── Code/                        # O3DE engine source
├── cmake/                       # CMake build system
├── Scripts/                     # O3DE build scripts
├── python/                      # Python requirements
└── README.md
```

## AI Tools Integrated

| Tool | Purpose | Status |
|------|---------|--------|
| **OpenRouter** | Live LLM for code generation | Integrated |
| **ProceduralTerrains** | GPU-based terrain generation | Integrated |
| **Hunyuan3D** | Text/Image to 3D model | Integrated |
| **Dust3D** | Mesh generation | Integrated |
| **ComfyUI** | Texture generation (Stable Diffusion) | Integrated |
| **GANimator** | Novel motion synthesis | Integrated |
| **DeepMotionEditing** | Motion retargeting | Integrated |
| **ElevenLabsClone** | Text-to-speech | Integrated |
| **InworldAI** | Voice AI for NPCs | Integrated |
| **AutoGen** | Multi-agent orchestration | Integrated |

## Troubleshooting

### Build fails with "Could NOT find Threads"
Fix: Install `libunwind-dev` and `libzstd-dev`:
```bash
sudo apt-get install -y libunwind-dev libzstd-dev
```

### Build fails with "PRIVATE: linker input file not found"
This is a known O3DE cmake bug. The fix is in `cmake/Platform/Common/GCC/Configurations_gcc.cmake` - ensure line 50 reads:
```cmake
set(O3DE_COMPILE_OPTION_DISABLE_FAST_MATH -fno-fast-math)
```
(No `PRIVATE` keyword)

### Editor crashes on startup
Ensure you have a GPU with Vulkan support, or use the software renderer:
```bash
./Editor --rhi=null
```

### AI sidebar doesn't appear
Check that `Gems/QtForPython/Editor/Scripts/bootstrap.py` includes the AI Design Studio registration code. The sidebar appears under **View → AI Design Studio**.

### "No space left on device"
O3DE build requires ~15-20GB of disk space. Clean up before building:
```bash
du -sh ~/ollama-training/  # Check large directories
# Move or delete what you don't need
```

## License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- **Open 3D Engine** - The open-source game engine by the Linux Foundation
- **OpenRouter** - Free AI model API
- **All AI tool repositories** integrated into this project

## Disclaimer

This is an AI-assisted game development tool. Generated content may need refinement. The AI cannot replace human creativity and game design expertise - it accelerates the tedious parts so you can focus on the fun parts.
