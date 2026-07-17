import assert from "node:assert/strict";
import test from "node:test";

import { safeExternalUrl, splitSafeContent } from "./safeContent.ts";

test("preserves malicious HTML as inert text", () => {
  const content = '<img src=x onerror="alert(1)"><script>alert(2)</script>';

  assert.deepEqual(splitSafeContent(content), [{ kind: "text", value: content }]);
});

test("splits only strict citation markers from surrounding text", () => {
  assert.deepEqual(splitSafeContent("First [C1]\nthen [C99]."), [
    { kind: "text", value: "First " },
    { citationId: "C1", kind: "citation", value: "[C1]" },
    { kind: "text", value: "\nthen " },
    { citationId: "C99", kind: "citation", value: "[C99]" },
    { kind: "text", value: "." },
  ]);
});

test("leaves malformed markers, entities, scripts, SVG, and attributes as text", () => {
  const content =
    "[C0] [C00] [C01] [C100] [c1] [C1 [C1x] &#60;script&#62; " +
    '<svg onload="alert(1)"></svg> onclick=alert(2)';

  assert.deepEqual(splitSafeContent(content), [{ kind: "text", value: content }]);
});

test("preserves oversized content without scanning it for markers", () => {
  const content = `${"x".repeat(32_000)}[C1]`;

  assert.deepEqual(splitSafeContent(content), [{ kind: "text", value: content }]);
});

test("accepts only absolute HTTP and HTTPS URLs", () => {
  assert.equal(safeExternalUrl("https://example.org/a?b=1#c"), "https://example.org/a?b=1#c");
  assert.equal(safeExternalUrl("http://example.org"), "http://example.org/");
  assert.equal(safeExternalUrl("HTTPS://example.org/path"), "https://example.org/path");
  for (const value of [
    "/relative", "example.org", "javascript:alert(1)", "data:text/html,x", "file:///tmp/x",
    "https:example.org", "https:/example.org", "https:////example.org",
    "http:example.org", "http:/example.org", "http:////example.org",
  ]) {
    assert.equal(safeExternalUrl(value), null);
  }
});

test("rejects credentials, backslashes, controls, Unicode spacing, and oversized URLs", () => {
  const unsafe = [
    "https://user@example.org/path",
    "https://user:pass@example.org/path",
    "https://example.org\\@evil.example/path",
    "https://example.org/line\nbreak",
    "https://example.org/zero\u200Bwidth",
    "https://example.org/non\u00A0breaking",
    `https://example.org/${"a".repeat(2_049)}`,
  ];

  for (const value of unsafe) assert.equal(safeExternalUrl(value), null);
});

test("bounds citation tokenization while preserving all text", () => {
  const content = "[C1]".repeat(100);
  const parts = splitSafeContent(content);

  assert.equal(parts.filter((part) => part.kind === "citation").length, 99);
  assert.deepEqual(parts.at(-1), { kind: "text", value: "[C1]" });
  assert.equal(parts.map((part) => part.value).join(""), content);
});

test("rejects non-string URL input without throwing", () => {
  for (const value of [null, undefined, 7, {}, []]) {
    assert.equal(safeExternalUrl(value as never), null);
  }
});

test("preserves paragraph breaks and every original character", () => {
  const content = "First paragraph.\n\nSecond paragraph.\nThird line &amp; **literal markers**.";

  assert.equal(splitSafeContent(content).map((part) => part.value).join(""), content);
});
