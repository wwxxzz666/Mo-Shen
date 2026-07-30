(function exposeStoryAgentsSSE(globalScope) {
  "use strict";

  function parseEventLine(line) {
    if (typeof line !== "string" || !line.startsWith("data:")) {
      return null;
    }

    const payload = line.slice(5).trim();
    if (!payload) {
      return null;
    }
    return JSON.parse(payload);
  }

  function assertSuccessfulEvent(event) {
    if (event && event.error) {
      throw new Error(event.error);
    }
    return event;
  }

  function getNodeEventContext(event) {
    const data = event && event.data ? event.data : {};
    return { data, node: data.node };
  }

  const api = {
    assertSuccessfulEvent,
    getNodeEventContext,
    parseEventLine,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.StoryAgentsSSE = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
