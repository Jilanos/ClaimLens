// Drives the shipped tracking client in a minimal fake DOM.
//
// There is no browser in the test environment, so this is how the client gets executed
// rather than merely read: a real parse, the real control flow, and the real timing and
// announcement decisions. It prints one JSON record for the Python test to assert on.
//
// Usage: node live_status_harness.js <path-to-live-status.js>

const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(process.argv[2], "utf8");

function node(id, dataset = {}) {
  return {id, dataset, innerHTML: "", textContent: "", hidden: false, contains: () => false};
}

const nodes = {
  "live-config": node("live-config", {
    endpoint: "/api/run-status?run_id=7",
    regions: JSON.stringify({"pipeline-status": "pipeline_status_html"}),
    connectionRegion: "pipeline-connection",
    offlineMessage: "Live updates are unavailable. Retrying automatically.",
    activeDelay: "2000",
    idleDelay: "15000",
    errorDelay: "5000",
    errorsBeforeNotice: "2",
  }),
  "pipeline-status": node("pipeline-status"),
  "pipeline-connection": node("pipeline-connection"),
};

const delays = [];
const requested = [];
let pending = null;
let responses = [];

const context = {
  console,
  URL,
  document: {
    hidden: false,
    activeElement: null,
    getElementById: (id) => nodes[id] || null,
    addEventListener: () => {},
  },
  window: {
    setTimeout: (fn, delay) => {
      delays.push(delay);
      pending = fn;
      return delays.length;
    },
    clearTimeout: () => {},
  },
  fetch: async (endpoint) => {
    requested.push(endpoint);
    const next = responses.shift();
    if (next === undefined || next.fail) throw new Error("network unreachable");
    return {ok: next.ok, json: async () => next.body};
  },
};
context.globalThis = context;
vm.createContext(context);

const flush = () => new Promise((resolve) => setImmediate(resolve));

async function poll(queue) {
  responses = queue;
  if (pending === null) {
    vm.runInContext(source, context);
  } else {
    const run = pending;
    pending = null;
    run();
  }
  for (let index = 0; index < 6; index += 1) await flush();
}

const state = (signature, active) => ({
  ok: true,
  body: {signature, active, pipeline_status_html: `<b>${signature}</b>`},
});

async function main() {
  const observed = {};

  // A first poll paints the page and asks again at the active rhythm.
  await poll([state("one", false)]);
  observed.painted = nodes["pipeline-status"].innerHTML;
  observed.firstDelay = delays.at(-1);
  observed.endpoint = requested[0];

  // Work in flight: the active rhythm, plainly.
  await poll([state("two", true)]);
  observed.activeDelay = delays.at(-1);

  // A hand-off between two jobs: nothing queued, but the state moved.
  await poll([state("three", false)]);
  observed.handoffDelay = delays.at(-1);

  // Nothing moved and nothing is queued: back off.
  await poll([state("three", false)]);
  observed.idleDelay = delays.at(-1);

  // One failure is noise, so it is not announced yet.
  await poll([{fail: true}]);
  observed.afterOneError = {
    delay: delays.at(-1),
    announced: !nodes["pipeline-connection"].hidden,
  };

  // A second failure in a row is worth saying out loud.
  await poll([{fail: true}]);
  observed.afterTwoErrors = {
    delay: delays.at(-1),
    announced: !nodes["pipeline-connection"].hidden,
    message: nodes["pipeline-connection"].textContent,
  };

  // A rejected response counts as a failure too, not as an empty state.
  await poll([{ok: false, body: {}}]);
  observed.afterRejection = {delay: delays.at(-1), painted: nodes["pipeline-status"].innerHTML};

  // Recovery takes the notice back down without a reload.
  await poll([state("four", false)]);
  observed.recovered = {
    announced: !nodes["pipeline-connection"].hidden,
    message: nodes["pipeline-connection"].textContent,
    painted: nodes["pipeline-status"].innerHTML,
  };

  // A hidden tab waits instead of polling.
  context.document.hidden = true;
  await poll([state("five", true)]);
  observed.hiddenTab = {delay: delays.at(-1), requests: requested.length};

  process.stdout.write(JSON.stringify(observed));
}

main();
