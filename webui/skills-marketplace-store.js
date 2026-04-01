import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const SKILLS_CATALOG_API = "/plugins/_skills_marketplace/skills_catalog";
const SKILL_INSTALL_API = "/plugins/_skills_marketplace/skill_install";

const skillsMarketplaceStore = {
  searchQuery: "",
  searchResults: [],
  installedSkills: [],
  loading: false,
  installing: null,
  removing: null,
  error: "",
  statusMessage: "",

  onOpen() {
    this.loadInstalled();
  },

  onClose() {},

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

  isInstalled(source) {
    return this.installedSkills.some((s) => s.source === source);
  },
};

export const store = createStore("skillsMarketplace", skillsMarketplaceStore);
