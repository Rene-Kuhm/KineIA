export interface TextContentPart {
  kind: "text";
  value: string;
}

export interface CitationContentPart {
  citationId: string;
  kind: "citation";
  value: string;
}

export type SafeContentPart = CitationContentPart | TextContentPart;

const CITATION_MARKER = /\[C([1-9][0-9]?)\]/g;
const MAX_PARSABLE_CONTENT_LENGTH = 32_000;
const MAX_CITATION_MARKERS = 99;
const MAX_EXTERNAL_URL_LENGTH = 2_048;
const CANONICAL_EXTERNAL_URL = /^https?:\/\/[^/]/i;
const UNSAFE_URL_CHARACTER = /[\\\p{Cc}\p{Cf}\p{Z}]/u;

export function safeExternalUrl(value: unknown): string | null {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > MAX_EXTERNAL_URL_LENGTH ||
    !CANONICAL_EXTERNAL_URL.test(value) ||
    UNSAFE_URL_CHARACTER.test(value)
  ) {
    return null;
  }
  try {
    const url = new URL(value);
    if (
      (url.protocol !== "http:" && url.protocol !== "https:") ||
      !url.hostname ||
      url.username ||
      url.password
    ) {
      return null;
    }
    return url.href;
  } catch {
    return null;
  }
}

export function splitSafeContent(content: string): SafeContentPart[] {
  if (content.length > MAX_PARSABLE_CONTENT_LENGTH) {
    return [{ kind: "text", value: content }];
  }
  const parts: SafeContentPart[] = [];
  let cursor = 0;
  let markerCount = 0;

  for (const match of content.matchAll(CITATION_MARKER)) {
    if (markerCount >= MAX_CITATION_MARKERS) break;
    const index = match.index;
    if (index > cursor) {
      parts.push({ kind: "text", value: content.slice(cursor, index) });
    }
    parts.push({
      citationId: `C${match[1]}`,
      kind: "citation",
      value: match[0],
    });
    cursor = index + match[0].length;
    markerCount += 1;
  }

  if (cursor < content.length || parts.length === 0) {
    parts.push({ kind: "text", value: content.slice(cursor) });
  }
  return parts;
}
