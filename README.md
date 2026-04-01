# Skills Marketplace Plugin for Agent Zero

Search, install, and manage skills from the [skills.sh](https://skills.sh) marketplace.

## Installation

Copy or symlink this directory into your Agent Zero `usr/plugins/` folder:

```bash
ln -s /path/to/skills_marketplace /path/to/agent-zero/usr/plugins/skills_marketplace
```

### Requirements

- **Node.js / npx** — required for the `npx skills` CLI that powers marketplace operations.
  Install from [nodejs.org](https://nodejs.org/).

## Features

- **Marketplace Search** — search the skills.sh catalog from the UI or via the agent tool
- **One-click Install** — install skills from `owner/repo` sources
- **Skill Management** — list and remove installed marketplace skills
- **Agent Tool** — `skills_marketplace` tool with methods: `search_remote`, `install`, `remove`, `list_installed`
- **Prompt Injection** — installed marketplace skills are automatically surfaced in agent context
- **Sidebar Quick Access** — button in the sidebar for fast marketplace access

## Directory Structure

```
skills_marketplace/
├── plugin.yaml                    # Plugin manifest
├── hooks.py                       # Install hook (checks for npx)
├── default_config.yaml            # Default settings
├── helpers/
│   └── skills_cli.py              # npx skills CLI wrapper + local skill management
├── tools/
│   └── skills_marketplace.py      # Agent tool for marketplace operations
├── api/
│   ├── skills_catalog.py          # Search & list API handler
│   └── skill_install.py           # Install & remove API handler
├── extensions/
│   ├── python/
│   │   └── message_loop_prompts_after/
│   │       └── _60_skills_catalog.py   # Prompt injection for installed skills
│   └── webui/
│       ├── _sidebar-quick-actions-main-start/
│       │   └── skills-entry.html       # Sidebar button
│       └── sidebar-quick-actions-dropdown-start/
│           └── skills-entry.html       # Dropdown entry
├── webui/
│   ├── main.html                  # Plugin main page
│   ├── config.html                # Settings panel
│   └── skills-settings.html       # Marketplace browse/manage UI
├── skills/                        # Where marketplace skills are installed
│   └── .gitkeep
└── README.md
```

## Configuration

| Setting              | Default | Description                              |
|----------------------|---------|------------------------------------------|
| `marketplace_enabled`| `true`  | Enable/disable marketplace integration   |
| `auto_check_updates` | `false` | Auto-check for updates to installed skills |

## Usage

### Via UI

1. Click the **extension** icon in the sidebar, or open Settings → Skills Marketplace
2. Search for skills in the marketplace
3. Click **Install** to add a skill
4. Installed skills appear in the "Installed Skills" tab

### Via Agent Tool

The agent can use the `skills_marketplace` tool:

```
skills_marketplace:search_remote  query="python debugging"
skills_marketplace:install        source="owner/repo"
skills_marketplace:update         source="owner/repo@skill"
skills_marketplace:check_updates
skills_marketplace:remove         skill_name="my-skill"
skills_marketplace:list_installed
```

### Via API

```bash
# Search marketplace
curl -X POST /api/skills_catalog -d '{"action": "search", "query": "testing"}'

# Install skill
curl -X POST /api/skill_install -d '{"action": "install", "source": "owner/repo"}'

# Check for updates
curl -X POST /api/skills_catalog -d '{"action": "check_updates"}'

# Update skill
curl -X POST /api/skill_install -d '{"action": "update", "source": "owner/repo@skill"}'

# List installed
curl -X POST /api/skills_catalog -d '{"action": "list_installed"}'

# Remove skill
curl -X POST /api/skill_install -d '{"action": "remove", "skill_name": "my-skill"}'
```
