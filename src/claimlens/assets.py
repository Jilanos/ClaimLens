"""Browser assets served same-origin.

The production CSP keeps `script-src 'self'`, so the live tracking client cannot ship as
an inline script. Keeping it here rather than inside `web.py` also keeps it out of an
f-string, where every JavaScript brace would need doubling.

The client is deliberately configuration-free: the page hands it the endpoint, the poll
rhythm, and the region map through data attributes, so the server stays the single source
of truth for what a poll may repaint.
"""

from __future__ import annotations

#: Served at `/static/live-status.js`. No build step: this is the shipped asset.
LIVE_STATUS_JS = """/* ClaimLens live analysis tracking. */
(() => {
  "use strict";

  const config = document.getElementById("live-config");
  if (config === null) return;
  const endpoint = config.dataset.endpoint || "";
  if (endpoint === "") return;

  function delay(raw, fallback) {
    const value = Number.parseInt(raw, 10);
    return Number.isFinite(value) && value > 0 ? value : fallback;
  }

  const ACTIVE_DELAY = delay(config.dataset.activeDelay, 2000);
  const IDLE_DELAY = delay(config.dataset.idleDelay, 15000);
  const ERROR_DELAY = delay(config.dataset.errorDelay, 5000);
  const ERRORS_BEFORE_NOTICE = delay(config.dataset.errorsBeforeNotice, 2);
  const OFFLINE_MESSAGE = config.dataset.offlineMessage || "";

  let regions = {};
  try {
    regions = JSON.parse(config.dataset.regions || "{}");
  } catch (_error) {
    regions = {};
  }
  const connection = document.getElementById(config.dataset.connectionRegion || "");

  let signature = null;
  let inFlight = false;
  let timer = null;
  let errors = 0;

  function schedule(nextDelay) {
    if (timer !== null) window.clearTimeout(timer);
    timer = window.setTimeout(refresh, nextDelay);
  }

  /* Silence is worse than a stale view: say so once polling has really stopped working,
     and take the notice back down as soon as one poll succeeds. */
  function announce(offline) {
    if (connection === null) return;
    connection.textContent = offline ? OFFLINE_MESSAGE : "";
    connection.hidden = !offline;
  }

  function paint(state) {
    for (const [id, key] of Object.entries(regions)) {
      const node = document.getElementById(id);
      if (node === null || typeof state[key] !== "string") continue;
      /* Never clobber a field the user is typing in, e.g. a pasted transcript. */
      if (node.contains(document.activeElement)) continue;
      node.innerHTML = state[key];
    }
  }

  function failed() {
    errors += 1;
    if (errors >= ERRORS_BEFORE_NOTICE) announce(true);
    schedule(ERROR_DELAY);
  }

  async function refresh() {
    if (inFlight) return;
    if (document.hidden) {
      schedule(IDLE_DELAY);
      return;
    }
    inFlight = true;
    try {
      const response = await fetch(endpoint, {cache: "no-store", credentials: "same-origin"});
      if (!response.ok) {
        failed();
        return;
      }
      const state = await response.json();
      errors = 0;
      announce(false);
      const changed = state.signature !== signature;
      if (changed) {
        paint(state);
        signature = state.signature;
      }
      /* Something that just moved is likely to move again. A chain hands off between two
         jobs with nothing queued for a moment, and reading `active` alone there would drop
         a running analysis to the idle rhythm at every step boundary. */
      schedule(state.active || changed ? ACTIVE_DELAY : IDLE_DELAY);
    } catch (_error) {
      failed();
    } finally {
      inFlight = false;
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) schedule(0);
  });
  refresh();
})();
"""
