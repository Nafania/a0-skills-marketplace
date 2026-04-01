import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const SKILLS_CATALOG_API = "/plugins/skills_marketplace/skills_catalog";
const SKILL_INSTALL_API = "/plugins/skills_marketplace/skill_install";

const skillsMarketplaceStore = {
  searchQuery: "",
  searchResults: [],
  installedSkills: [],
  updatesAvailable: [],
  loading: false,
  installing: null,
  removing: null,
  updating: null,
  checkingUpdates: false,
  error: "",
  statusMessage: "",
  autoCheckUpdates: false,

  async onOpen() {
    await this.loadInstalled();
    await this._loadConfig();
    if (this.autoCheckUpdates) {
      this.checkUpdates();
    }
  },

  onClose() {},

  async _loadConfig() {
    try {
      const data = await API.callJsonApi(SKILLS_CATALOG_API, {
        action: "get_config",
      });
      if (data.ok && data.data) {
        this.autoCheckUpdates = !!data.data.auto_check_updates;
      }
    } catch (e) {
      // config load failure is non-critical
    }
  },

  async search() {
    const q = this.searchQuery.trim();
    if (!q) return;
    this.loading = true;
    this.error = "";
    this.statusMessage = "";
    this.searchResults = [];
    try {
      const data = await API.callJsonApi(SKILLS_CATALOG_API, {
        action: "search",
        query: q,
      });
      if (data.ok) {
        this.searchResults = data.data?.results || [];
        if (this.searchResults.length === 0) {
          this.statusMessage = `No skills found matching "${q}".`;
        }
      } else {
        this.error = data.error || "Search failed";
      }
    } catch (e) {
      this.error = "Network error: " + e.message;
    }
    this.loading = false;
  },

  async installSkill(source) {
    this.installing = source;
    this.error = "";
    this.statusMessage = "";
    try {
      const data = await API.callJsonApi(SKILL_INSTALL_API, {
        action: "install",
        source,
      });
      if (data.ok) {
        this.statusMessage = `Installed "${source}" successfully.`;
        await this.loadInstalled();
      } else {
        this.error = data.error || "Install failed";
      }
    } catch (e) {
      this.error = "Network error: " + e.message;
    }
    this.installing = null;
  },

  async removeSkill(name) {
    this.removing = name;
    this.error = "";
    this.statusMessage = "";
    try {
      const data = await API.callJsonApi(SKILL_INSTALL_API, {
        action: "remove",
        skill_name: name,
      });
      if (data.ok) {
        this.statusMessage = `Removed "${name}".`;
        await this.loadInstalled();
        this.updatesAvailable = this.updatesAvailable.filter((u) => u.name !== name);
      } else {
        this.error = data.error || "Remove failed";
      }
    } catch (e) {
      this.error = "Network error: " + e.message;
    }
    this.removing = null;
  },

  async loadInstalled() {
    try {
      const data = await API.callJsonApi(SKILLS_CATALOG_API, {
        action: "list_installed",
      });
      if (data.ok) {
        this.installedSkills = data.data?.skills || [];
      }
    } catch (e) {
      // silently fail on load
    }
  },

  async checkUpdates() {
    this.checkingUpdates = true;
    this.error = "";
    try {
      const data = await API.callJsonApi(SKILLS_CATALOG_API, {
        action: "check_updates",
      });
      if (data.ok) {
        this.updatesAvailable = data.data?.updates || [];
        if (this.updatesAvailable.length === 0) {
          this.statusMessage = "All skills are up to date.";
        } else {
          this.statusMessage = `${this.updatesAvailable.length} update(s) available.`;
        }
      } else {
        this.error = data.error || "Failed to check for updates";
      }
    } catch (e) {
      this.error = "Network error: " + e.message;
    }
    this.checkingUpdates = false;
  },

  async updateSkill(source) {
    this.updating = source;
    this.error = "";
    this.statusMessage = "";
    try {
      const data = await API.callJsonApi(SKILL_INSTALL_API, {
        action: "update",
        source,
      });
      if (data.ok) {
        this.statusMessage = `Updated "${source}" successfully.`;
        this.updatesAvailable = this.updatesAvailable.filter((u) => u.source !== source);
        await this.loadInstalled();
      } else {
        this.error = data.error || "Update failed";
      }
    } catch (e) {
      this.error = "Network error: " + e.message;
    }
    this.updating = null;
  },

  async updateAll() {
    const sources = this.updatesAvailable.map((u) => u.source).filter(Boolean);
    for (const source of sources) {
      await this.updateSkill(source);
      if (this.error) break;
    }
  },

  hasUpdate(name) {
    return this.updatesAvailable.some((u) => u.name === name);
  },

  getUpdateSource(name) {
    const upd = this.updatesAvailable.find((u) => u.name === name);
    return upd ? upd.source : "";
  },

  isInstalled(source) {
    return this.installedSkills.some((s) => s.source === source);
  },
};

export const store = createStore("skillsMarketplace", skillsMarketplaceStore);
