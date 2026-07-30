"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  assertSuccessfulEvent,
  getNodeEventContext,
  parseEventLine,
} = require("../../storyagents/h5/sse.js");

test("parses node_complete events using the backend event contract", () => {
  const event = parseEventLine(
    'data: {"event":"node_complete","data":{"node":"Planner","story_title":"Test"}}',
  );

  assert.equal(event.event, "node_complete");
  const { data, node } = getNodeEventContext(event);
  assert.equal(node, "Planner");
  assert.equal(data.story_title, "Test");
});

test("preserves backend error events for the caller to handle", () => {
  const event = parseEventLine('data: {"error":"provider unavailable"}');

  assert.throws(
    () => assertSuccessfulEvent(event),
    /provider unavailable/,
  );
});

test("ignores non-data and empty SSE lines", () => {
  assert.equal(parseEventLine("event: ping"), null);
  assert.equal(parseEventLine("data:   "), null);
});

test("rejects malformed JSON instead of hiding the protocol failure", () => {
  assert.throws(() => parseEventLine("data: {broken"), SyntaxError);
});
